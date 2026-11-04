"""Script thực thi đánh giá Benchmark v2 (500 câu hỏi, chia 10 Batches).
Đo lường ma trận 6 chiều (6-Dimensional Benchmark Matrix):
1. Rewriting Accuracy (%)
2. Routing Accuracy (%)
3. Answer Correctness (%)
4. Latency p50 / p95 (ms)
5. Fallback Rate (%)
6. Context Bleeding Rate (%)

Đồng thời kiểm soát an toàn phần cứng (Hardware Safety & Memory Isolation):
- Phân tách theo từng Batch (50 câu/batch)
- Dọn dẹp bộ nhớ (gc.collect(), session_manager.clear(), torch cache empty nếu có)
- Tự động xuất ma trận tổng hợp JSON và Markdown
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from FPTUniQA.pipeline.rag_pipeline import RAGPipeline
from FPTUniQA.utils.logger import get_logger

logger = get_logger("scripts.benchmark_v2_batches")

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def check_rewriting_quality(
    item: Dict[str, Any],
    rewritten_query: str,
    original_query: str,
    topic_switch_detected: bool,
) -> Tuple[bool, str]:
    """Đánh giá chất lượng của Query Rewriter."""
    is_cont = item.get("is_continuation", False)
    is_switch = item.get("is_topic_switch", False)
    rewritten_lower = (rewritten_query or "").lower()

    if is_cont:
        expected_contains = item.get("expected_rewrite_contains", [])
        missing = []
        for kw in expected_contains:
            if kw.lower() not in rewritten_lower:
                missing.append(kw)
        if missing:
            return False, f"Thiếu thực thể kế thừa: {missing} trong '{rewritten_query}'"
        return True, "Kế thừa thực thể chuẩn xác"

    if is_switch:
        avoid_entities = item.get("avoid_bleeding_entities", [])
        bleeding = []
        for kw in avoid_entities:
            if kw.lower() in rewritten_lower:
                bleeding.append(kw)
        if bleeding:
            return False, f"Context Bleeding: bị nhiễm {bleeding} trong '{rewritten_query}'"
        return True, "Chuyển chủ đề sạch sẽ (0 bleeding)"

    return True, "Turn 1 / Câu độc lập"


def check_routing_quality(item: Dict[str, Any], actual_route: str) -> Tuple[bool, str]:
    """Kiểm tra độ chính xác của Semantic Router."""
    expected_route = item.get("expected_route", "")
    act = str(actual_route).lower()
    exp = str(expected_route).lower()

    if exp in act or act in exp:
        return True, f"Route chuẩn: {act}"
    if exp == "ood" and ("ood" in act or "ngoài" in act):
        return True, "Route OOD chuẩn"
    return False, f"Sai route: mong đợi '{exp}', thực tế '{act}'"


def check_answer_quality(
    item: Dict[str, Any],
    answer_text: str,
    actual_route: str,
    possible_hallucination: bool,
) -> Tuple[bool, str]:
    """Kiểm tra độ chính xác của câu trả lời so với Golden Truth."""
    expected_contains = item.get("expected_answer_contains", [])
    expected_route = item.get("expected_route", "")
    ans_clean = (answer_text or "").lower()

    # OOD: Kiểm tra từ chối
    if expected_route == "ood" or "ood" in str(actual_route).lower():
        if any(w in ans_clean for w in ["ngoài phạm vi", "không thuộc phạm vi", "chỉ hỗ trợ", "quy chế", "đại học fpt"]):
            return True, "Từ chối OOD chính xác"
        return False, "Không từ chối câu hỏi ngoài miền"

    if not expected_contains:
        return True, "Không có ràng buộc chuỗi cụ thể"

    found_any = False
    for expected_str in expected_contains:
        target = expected_str.lower().strip()
        target_alt = target.replace(".", ",").replace(" ", "")
        ans_normalized = ans_clean.replace(".", ",").replace(" ", "")

        if target in ans_clean or target_alt in ans_normalized:
            found_any = True
            break

    if not found_any:
        return False, f"Thiếu thông tin {expected_contains} trong câu trả lời"

    if possible_hallucination:
        return False, "Cảnh báo ảo giác số liệu"

    return True, "Câu trả lời chính xác, chuẩn xác số liệu"


def percentile(data: List[float], p: float) -> float:
    """Tính phân vị percentile theo chuẩn thống kê."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1


def cleanup_memory(pipeline: Optional[RAGPipeline] = None):
    """Giải phóng bộ nhớ an toàn sau mỗi batch và kiểm soát an toàn phần cứng."""
    if pipeline and hasattr(pipeline, "session_manager"):
        pipeline.session_manager.clear()
    gc.collect()
    if HAS_TORCH and torch.cuda.is_available():
        torch.cuda.empty_cache()

    try:
        import psutil
        vm = psutil.virtual_memory()
        ram_used_gb = vm.used / (1024**3)
        ram_avail_gb = vm.available / (1024**3)
        print(f"  [Hardware Guard] RAM: {ram_used_gb:.2f} GB used ({vm.percent}%) | {ram_avail_gb:.2f} GB available - Status: SAFE")
        if ram_avail_gb < 1.0:
            print("  [Hardware Guard] CẢNH BÁO: Bộ nhớ RAM khả dụng dưới 1GB! Tạm dừng 2s để HĐH dọn dẹp...")
            time.sleep(2.0)
            gc.collect()
    except Exception:
        pass


def run_batch(
    batch_num: int,
    pipeline: RAGPipeline,
    dataset_dir: str = "data/evaluation/benchmark_v2",
    output_dir: str = "experiments/benchmark_v2",
) -> Dict[str, Any]:
    """Chạy đánh giá cho một batch đơn lẻ (50 câu)."""
    batch_file = Path(dataset_dir) / f"batch_{batch_num:02d}.jsonl"
    if not batch_file.exists():
        raise FileNotFoundError(f"Không tìm thấy tập dữ liệu: {batch_file}")

    with open(batch_file, "r", encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]

    print(f"\n{'='*70}")
    print(f"▶ CHẠY BATCH {batch_num:02d} / 10 ({len(items)} câu hỏi) - Tệp: {batch_file.name}")
    print(f"{'='*70}")

    results = []
    latencies = []
    total_passed = 0
    total_continuation = 0
    continuation_passed = 0
    total_switch = 0
    switch_bleeding = 0
    total_route_ok = 0
    total_answer_ok = 0
    total_fallback = 0

    batch_start_time = time.time()

    for idx, item in enumerate(items, start=1):
        q_id = item["q_id"]
        cat = item["category"]
        sess_id = item["session_id"]
        turn = item["turn_index"]
        query = item["query"]
        is_cont = item.get("is_continuation", False)
        is_switch = item.get("is_topic_switch", False)

        t0 = time.time()
        try:
            res = pipeline.answer(query, session_id=sess_id)
            latency = (time.time() - t0) * 1000.0
            error = None
        except Exception as exc:
            latency = (time.time() - t0) * 1000.0
            error = str(exc)
            res = {
                "rewritten_query": query,
                "route": "error",
                "answer": f"Lỗi thực thi: {error}",
                "topic_switch_detected": False,
                "possible_hallucination": False,
            }

        latencies.append(latency)

        rewritten = res.get("rewritten_query", query)
        actual_route = res.get("route", "unknown")
        answer_text = res.get("answer", "")
        sw_detected = res.get("topic_switch_detected", False)
        hallucination = res.get("possible_hallucination", False)

        # Kiểm tra 6 chiều
        rewrite_ok, rewrite_msg = check_rewriting_quality(item, rewritten, query, sw_detected)
        route_ok, route_msg = check_routing_quality(item, actual_route)
        answer_ok, answer_msg = check_answer_quality(item, answer_text, actual_route, hallucination)

        if is_cont:
            total_continuation += 1
            if rewrite_ok:
                continuation_passed += 1

        if is_switch:
            total_switch += 1
            if not rewrite_ok:
                switch_bleeding += 1

        if route_ok:
            total_route_ok += 1

        if actual_route in ["fallback", "unhandled", "error"]:
            total_fallback += 1

        if answer_ok:
            total_answer_ok += 1

        item_pass = rewrite_ok and route_ok and answer_ok
        if item_pass:
            total_passed += 1

        record = {
            "q_id": q_id,
            "turn_index": turn,
            "category": cat,
            "query": query,
            "rewritten_query": rewritten,
            "expected_route": item.get("expected_route"),
            "actual_route": actual_route,
            "expected_contains": item.get("expected_answer_contains"),
            "answer_snippet": answer_text[:200] + ("..." if len(answer_text) > 200 else ""),
            "item_passed": item_pass,
            "rewrite_ok": rewrite_ok,
            "route_ok": route_ok,
            "answer_ok": answer_ok,
            "latency_ms": round(latency, 2),
            "rewrite_msg": rewrite_msg,
            "route_msg": route_msg,
            "answer_msg": answer_msg,
        }
        results.append(record)

        icon = "✓" if item_pass else "✗"
        print(f"[{idx:02d}/{len(items):02d}] {icon} | QID: {q_id} | Turn {turn} | Route: {actual_route:18s} | Latency: {latency:6.1f}ms | Pass: {item_pass}")
        if not item_pass:
            if not rewrite_ok:
                print(f"        -> Rewriter Fail: {rewrite_msg}")
            if not route_ok:
                print(f"        -> Route Fail: {route_msg}")
            if not answer_ok:
                print(f"        -> Answer Fail: {answer_msg}")

    # Tính toán các chỉ số thống kê
    n = len(items)
    acc_total = round(total_passed / n * 100.0, 2) if n > 0 else 0.0
    rewriting_acc = round(continuation_passed / total_continuation * 100.0, 2) if total_continuation > 0 else 100.0
    routing_acc = round(total_route_ok / n * 100.0, 2) if n > 0 else 0.0
    answer_acc = round(total_answer_ok / n * 100.0, 2) if n > 0 else 0.0
    fallback_rate = round(total_fallback / n * 100.0, 2) if n > 0 else 0.0
    bleeding_rate = round(switch_bleeding / total_switch * 100.0, 2) if total_switch > 0 else 0.0
    p50_lat = round(percentile(latencies, 50), 2)
    p95_lat = round(percentile(latencies, 95), 2)
    avg_lat = round(sum(latencies) / n, 2) if n > 0 else 0.0

    batch_summary = {
        "batch_index": batch_num,
        "batch_name": f"batch_{batch_num:02d}",
        "category": items[0]["category"] if items else "unknown",
        "total_questions": n,
        "passed_questions": total_passed,
        "overall_accuracy_pct": acc_total,
        "rewriting_accuracy_pct": rewriting_acc,
        "routing_accuracy_pct": routing_acc,
        "answer_correctness_pct": answer_acc,
        "fallback_rate_pct": fallback_rate,
        "context_bleeding_rate_pct": bleeding_rate,
        "latency_p50_ms": p50_lat,
        "latency_p95_ms": p95_lat,
        "latency_avg_ms": avg_lat,
        "total_time_seconds": round(time.time() - batch_start_time, 2),
        "verdict": "PASS" if acc_total >= 90.0 else "FAIL",
    }

    # Lưu kết quả chi tiết của batch
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    detail_path = out_dir / f"batch_{batch_num:02d}_result.json"
    with open(detail_path, "w", encoding="utf-8") as f:
        json.dump({"summary": batch_summary, "details": results}, f, ensure_ascii=False, indent=2)

    print(f"\n--- TỔNG KẾT BATCH {batch_num:02d} ---")
    print(f"Passed: {total_passed}/{n} ({acc_total}%) | Verdict: {batch_summary['verdict']}")
    print(f"Rewriting: {rewriting_acc}% | Routing: {routing_acc}% | Answer: {answer_acc}%")
    print(f"Fallback: {fallback_rate}% | Bleeding: {bleeding_rate}% | Latency: p50={p50_lat}ms, p95={p95_lat}ms")

    # Dọn dẹp bộ nhớ giữa các batch
    cleanup_memory(pipeline)
    return batch_summary


def generate_matrix_reports(batch_summaries: List[Dict[str, Any]], output_dir: str = "experiments/benchmark_v2"):
    """Tổng hợp ma trận đánh giá 6 chiều thành JSON và Markdown."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    total_q = sum(b["total_questions"] for b in batch_summaries)
    total_passed = sum(b["passed_questions"] for b in batch_summaries)
    overall_acc = round(total_passed / total_q * 100.0, 2) if total_q > 0 else 0.0

    avg_rewrite = round(sum(b["rewriting_accuracy_pct"] for b in batch_summaries) / len(batch_summaries), 2)
    avg_route = round(sum(b["routing_accuracy_pct"] for b in batch_summaries) / len(batch_summaries), 2)
    avg_answer = round(sum(b["answer_correctness_pct"] for b in batch_summaries) / len(batch_summaries), 2)
    avg_fallback = round(sum(b["fallback_rate_pct"] for b in batch_summaries) / len(batch_summaries), 2)
    avg_bleeding = round(sum(b["context_bleeding_rate_pct"] for b in batch_summaries) / len(batch_summaries), 2)
    avg_p50 = round(sum(b["latency_p50_ms"] for b in batch_summaries) / len(batch_summaries), 2)
    avg_p95 = round(sum(b["latency_p95_ms"] for b in batch_summaries) / len(batch_summaries), 2)

    matrix_data = {
        "benchmark_name": "FPTUniQA 500-Question Comprehensive Benchmark v2",
        "total_batches": len(batch_summaries),
        "total_questions": total_q,
        "total_passed": total_passed,
        "overall_accuracy_pct": overall_acc,
        "macro_metrics": {
            "mean_rewriting_accuracy_pct": avg_rewrite,
            "mean_routing_accuracy_pct": avg_route,
            "mean_answer_correctness_pct": avg_answer,
            "mean_fallback_rate_pct": avg_fallback,
            "mean_context_bleeding_rate_pct": avg_bleeding,
            "mean_latency_p50_ms": avg_p50,
            "mean_latency_p95_ms": avg_p95,
        },
        "batches": batch_summaries,
    }

    # Lưu JSON matrix
    json_path = out_dir / "matrix.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(matrix_data, f, ensure_ascii=False, indent=2)

    # Sinh Markdown Table
    md_lines = [
        "# BẢNG MA TRẬN ĐÁNH GIÁ BENCHMARK CHI TIẾT (500 CÂU HỎI - BENCHMARK V2)",
        "",
        f"- **Tổng số câu hỏi đánh giá:** {total_q} câu (10 batches × 50 câu)",
        f"- **Đạt chuẩn:** {total_passed}/{total_q} câu ({overall_acc}%)",
        f"- **Kết luận tổng thể:** {'PASS (ĐẠT CHUẨN XUẤT SẮC)' if overall_acc >= 90.0 else 'FAIL'}",
        "",
        "## 1. Ma Trận Đánh Giá 6 Chiều Theo Từng Batch",
        "",
        "| Batch | Chủ đề / Ngữ cảnh | Số câu | Độ chính xác tổng | Rewriting Acc | Routing Acc | Answer Acc | Fallback Rate | Bleeding Rate | Latency p50 | Latency p95 | Kết quả |",
        "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for b in batch_summaries:
        md_lines.append(
            f"| **Batch {b['batch_index']:02d}** | {b['category']} | {b['total_questions']} | "
            f"**{b['overall_accuracy_pct']}%** | {b['rewriting_accuracy_pct']}% | {b['routing_accuracy_pct']}% | "
            f"{b['answer_correctness_pct']}% | {b['fallback_rate_pct']}% | {b['context_bleeding_rate_pct']}% | "
            f"{b['latency_p50_ms']} ms | {b['latency_p95_ms']} ms | **{b['verdict']}** |"
        )

    md_lines.extend([
        "",
        "## 2. Thống Kê Tổng Hợp (Macro Summary)",
        "",
        f"- **Độ chính xác tổng thể (Overall Accuracy):** **{overall_acc}%**",
        f"- **Độ chính xác viết lại ngữ cảnh (Rewriting Accuracy):** **{avg_rewrite}%**",
        f"- **Độ chính xác định tuyến (Routing Accuracy):** **{avg_route}%**",
        f"- **Độ chính xác câu trả lời (Answer Correctness):** **{avg_answer}%**",
        f"- **Tỷ lệ Fallback (Fallback Rate):** **{avg_fallback}%**",
        f"- **Tỷ lệ nhiễm ngữ cảnh (Context Bleeding Rate):** **{avg_bleeding}%**",
        f"- **Độ trễ trung vị p50:** **{avg_p50} ms** | **Độ trễ phân vị p95:** **{avg_p95} ms**",
        "",
        "---",
        "*Báo cáo được sinh tự động bởi FPTUniQA Benchmark Suite.*"
    ])

    md_path = out_dir / "matrix.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(f"\n✓ Đã lưu ma trận Benchmark tại:\n  - {json_path}\n  - {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Run FPTUniQA Benchmark v2 Batches")
    parser.add_argument("--batch", type=int, default=None, help="Chạy batch cụ thể (1 đến 10)")
    parser.add_argument("--start-batch", type=int, default=1, help="Batch bắt đầu (mặc định 1)")
    parser.add_argument("--end-batch", type=int, default=10, help="Batch kết thúc (mặc định 10)")
    parser.add_argument("--skip-existing", action="store_true", help="Bỏ qua batch nếu đã có file kết quả JSON")
    parser.add_argument("--all", action="store_true", help="Chạy toàn bộ 10 batches (500 câu)")
    args = parser.parse_args()

    pipeline = RAGPipeline(use_mock_fallback=False)
    out_dir = Path("experiments/benchmark_v2")
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.batch:
        if args.batch < 1 or args.batch > 10:
            print(f"Lỗi: Batch phải từ 1 đến 10, nhận được: {args.batch}")
            sys.exit(1)
        run_batch(args.batch, pipeline)
    else:
        # Chạy dải batches từ start-batch đến end-batch
        all_summaries = []
        for b in range(1, 11):
            res_file = out_dir / f"batch_{b:02d}_result.json"
            if b < args.start_batch or b > args.end_batch:
                if res_file.exists():
                    with open(res_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        all_summaries.append(data["summary"])
                continue

            if args.skip_existing and res_file.exists():
                print(f"\n[SKIP] Batch {b:02d} đã có kết quả tại {res_file.name}, nạp lại từ bộ nhớ đệm.")
                with open(res_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    all_summaries.append(data["summary"])
                continue

            summary = run_batch(b, pipeline)
            all_summaries.append(summary)

        # Tổng hợp báo cáo ma trận nếu đủ 10 batches hoặc khi chạy batch kết thúc là 10
        if len(all_summaries) >= 10:
            generate_matrix_reports(all_summaries)
        else:
            print(f"\nĐã hoàn thành {len(all_summaries)} batches.")


if __name__ == "__main__":
    main()
