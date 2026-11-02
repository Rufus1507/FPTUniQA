"""Script thực thi đánh giá benchmark đa lượt theo đợt (Round 1 đến Round 5).
Đo lường 3 tiêu chí khách quan (Rubric 3 lớp):
1. Rewriting Accuracy (Giải đúng coreference / ellipsis cho continuation; Zero bleeding cho topic switch)
2. Routing Accuracy (Định tuyến chuẩn vào structured_lookup, rag_pipeline, hoặc ood)
3. Answer Correctness (Chứa số liệu golden chính xác, không hallucination, từ chối OOD đúng)

Ngưỡng đạt yêu cầu: Accuracy tổng >= 90% (>= 0.90).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from FPTUniQA.pipeline.rag_pipeline import RAGPipeline
from FPTUniQA.utils.logger import get_logger

logger = get_logger("scripts.benchmark_multiturn_rounds")


def check_rewriting_quality(
    item: Dict[str, Any],
    rewritten_query: str,
    original_query: str,
    topic_switch_detected: bool,
) -> tuple[bool, str]:
    """Đánh giá chất lượng của Query Rewriter dựa trên phân loại câu hỏi."""
    is_cont = item.get("is_continuation", False)
    is_switch = item.get("is_topic_switch", False)

    # Trường hợp 1: Câu hỏi kế thừa đa lượt (Continuation)
    if is_cont:
        expected_contains = item.get("expected_rewrite_contains", [])
        rewritten_lower = (rewritten_query or "").lower()
        missing = []
        for kw in expected_contains:
            if kw.lower() not in rewritten_lower:
                missing.append(kw)
        if missing:
            return False, f"Rewriter thiếu thực thể kế thừa: {missing} trong '{rewritten_query}'"
        return True, "Kế thừa thực thể đầy đủ"

    # Trường hợp 2: Chuyển đổi chủ đề đột ngột (Topic Switch)
    if is_switch:
        avoid_entities = item.get("avoid_bleeding_entities", [])
        rewritten_lower = (rewritten_query or "").lower()
        bleeding = []
        for kw in avoid_entities:
            if kw.lower() in rewritten_lower:
                bleeding.append(kw)
        if bleeding:
            return False, f"Context Bleeding: bị nhiễm thực thể cũ {bleeding} trong '{rewritten_query}'"
        return True, "Chuyển chủ đề sạch sẽ, không bị nhiễm ngữ cảnh"

    # Trường hợp 3: Câu đơn hoặc turn 1
    return True, "Câu độc lập / Turn 1"


def check_routing_quality(item: Dict[str, Any], actual_route: str) -> tuple[bool, str]:
    """Kiểm tra độ chính xác của Router."""
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
) -> tuple[bool, str]:
    """Kiểm tra độ chính xác của câu trả lời so với Golden Truth."""
    expected_contains = item.get("expected_answer_contains", [])
    expected_route = item.get("expected_route", "")
    ans_clean = (answer_text or "").lower()

    # OOD: Kiểm tra từ chối
    if expected_route == "ood" or "ood" in str(actual_route).lower():
        if any(w in ans_clean for w in ["ngoài phạm vi", "không thuộc phạm vi", "chỉ hỗ trợ", "quy chế", "đại học fpt"]):
            return True, "Từ chối OOD chính xác"
        return False, "Không từ chối câu hỏi ngoài miền"

    # Structured lookup / Cohort / Course: Kiểm tra sự có mặt của số liệu/thực thể chuẩn
    if not expected_contains:
        return True, "Không có ràng buộc chuỗi cụ thể"

    found_any = False
    for expected_str in expected_contains:
        # Chuẩn hóa để so khớp số tiền (hỗ trợ cả dấu chấm lẫn dấu phẩy)
        target = expected_str.lower().strip()
        target_alt = target.replace(".", ",").replace(" ", "")
        ans_normalized = ans_clean.replace(".", ",").replace(" ", "")

        if target in ans_clean or target_alt in ans_normalized:
            found_any = True
            break

    if not found_any:
        return False, f"Thiếu thông tin mong đợi {expected_contains} trong câu trả lời"

    if possible_hallucination:
        return False, "Phát hiện ảo giác số liệu (Hallucination Guardrail)"

    return True, "Câu trả lời chính xác, đầy đủ thông tin chuẩn"


def run_benchmark(round_num: int, limit: int | None = None, output_dir: str | None = None) -> Dict[str, Any]:
    """Chạy toàn bộ bài test của round_num và tính toán báo cáo tổng thể."""
    dataset_path = Path(f"data/evaluation/multiturn_rounds/round_{round_num}.jsonl")
    if not dataset_path.exists():
        logger.info(f"Chưa có tập test cho Round {round_num}. Đang tự động sinh...")
        from scripts.generate_multiturn_round import generate_round_questions
        items = generate_round_questions(round_num)
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dataset_path, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    else:
        with open(dataset_path, "r", encoding="utf-8") as f:
            items = [json.loads(line) for line in f if line.strip()]

    if limit and limit > 0:
        items = items[:limit]

    out_folder = Path(output_dir or f"experiments/benchmark_mt/round_{round_num}")
    out_folder.mkdir(parents=True, exist_ok=True)

    logger.info(f"=== BẮT ĐẦU CHẠY BENCHMARK ROUND {round_num} ({len(items)} câu hỏi) ===")
    pipeline = RAGPipeline(use_mock_fallback=False)

    results: List[Dict[str, Any]] = []
    category_stats: Dict[str, Dict[str, int]] = {}

    total_pass = 0
    total_rewrite_pass = 0
    total_route_pass = 0
    total_answer_pass = 0

    start_time_all = time.time()

    for idx, item in enumerate(items, start=1):
        q_id = item["q_id"]
        cat = item["category"]
        sess_id = item["session_id"]
        turn = item["turn_index"]
        query = item["query"]

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "pass": 0, "rewrite_pass": 0, "route_pass": 0, "answer_pass": 0}
        category_stats[cat]["total"] += 1

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
                "answer": f"Lỗi hệ thống: {error}",
                "topic_switch_detected": False,
                "possible_hallucination": False,
            }

        rewritten = res.get("rewritten_query", query)
        actual_route = res.get("route", "unknown")
        answer_text = res.get("answer", "")
        sw_detected = res.get("topic_switch_detected", False)
        hallucination = res.get("possible_hallucination", False)

        # Chấm điểm 3 tiêu chí
        rewrite_ok, rewrite_msg = check_rewriting_quality(item, rewritten, query, sw_detected)
        route_ok, route_msg = check_routing_quality(item, actual_route)
        answer_ok, answer_msg = check_answer_quality(item, answer_text, actual_route, hallucination)

        item_pass = rewrite_ok and route_ok and answer_ok

        if rewrite_ok:
            total_rewrite_pass += 1
            category_stats[cat]["rewrite_pass"] += 1
        if route_ok:
            total_route_pass += 1
            category_stats[cat]["route_pass"] += 1
        if answer_ok:
            total_answer_pass += 1
            category_stats[cat]["answer_pass"] += 1
        if item_pass:
            total_pass += 1
            category_stats[cat]["pass"] += 1

        res_record = {
            "q_id": q_id,
            "session_id": sess_id,
            "turn_index": turn,
            "category": cat,
            "query": query,
            "rewritten_query": rewritten,
            "expected_route": item.get("expected_route"),
            "actual_route": actual_route,
            "answer": answer_text[:250] + ("..." if len(answer_text) > 250 else ""),
            "expected_contains": item.get("expected_answer_contains"),
            "item_passed": item_pass,
            "rewrite_ok": rewrite_ok,
            "rewrite_msg": rewrite_msg,
            "route_ok": route_ok,
            "route_msg": route_msg,
            "answer_ok": answer_ok,
            "answer_msg": answer_msg,
            "latency_ms": round(latency, 2),
        }
        results.append(res_record)

        status_icon = "✓" if item_pass else "✗"
        print(f"[{idx:03d}/{len(items):03d}] {status_icon} [{cat:24s}] Turn {turn} | Route: {actual_route:17s} | Pass: {item_pass}")
        if not item_pass:
            if not rewrite_ok:
                print(f"       -> Rewriter FAIL: {rewrite_msg}")
            if not route_ok:
                print(f"       -> Route FAIL: {route_msg}")
            if not answer_ok:
                print(f"       -> Answer FAIL: {answer_msg}")

    total_time = time.time() - start_time_all
    total_count = len(items)
    accuracy_total = round(total_pass / total_count, 4) if total_count > 0 else 0.0
    rewrite_acc = round(total_rewrite_pass / total_count, 4) if total_count > 0 else 0.0
    route_acc = round(total_route_pass / total_count, 4) if total_count > 0 else 0.0
    answer_acc = round(total_answer_pass / total_count, 4) if total_count > 0 else 0.0

    verdict = "PASS" if accuracy_total >= 0.90 else "FAIL"

    summary = {
        "round": round_num,
        "total_questions": total_count,
        "total_passed": total_pass,
        "accuracy_total": accuracy_total,
        "target_accuracy": 0.90,
        "verdict": verdict,
        "metrics": {
            "rewriting_accuracy": rewrite_acc,
            "routing_accuracy": route_acc,
            "answer_accuracy": answer_acc,
        },
        "category_breakdown": {
            cat: {
                "total": stats["total"],
                "passed": stats["pass"],
                "accuracy": round(stats["pass"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
                "rewrite_acc": round(stats["rewrite_pass"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
                "route_acc": round(stats["route_pass"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
                "answer_acc": round(stats["answer_pass"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
            }
            for cat, stats in category_stats.items()
        },
        "execution_time_seconds": round(total_time, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Xuất file kết quả chi tiết
    results_path = out_folder / "results.jsonl"
    with open(results_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Xuất file summary
    summary_path = out_folder / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Xuất file báo cáo Markdown
    report_path = out_folder / "report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Báo Cáo Đánh Giá Benchmark Đa Lượt - Round {round_num}\n\n")
        f.write(f"- **Thời gian:** {summary['timestamp']}\n")
        f.write(f"- **Tổng số câu:** {total_count}\n")
        f.write(f"- **Tổng số câu đạt:** {total_pass} / {total_count}\n")
        f.write(f"- **Độ chính xác toàn diện (Accuracy Total):** **{accuracy_total * 100:.2f}%**\n")
        f.write(f"- **Chỉ tiêu (Target):** ≥ 90.00%\n")
        f.write(f"- **Kết quả:** **{verdict}**\n\n")
        f.write(f"### Chi tiết theo tiêu chí đánh giá (Rubric 3 lớp):\n")
        f.write(f"- **Rewriting Accuracy:** {rewrite_acc * 100:.2f}%\n")
        f.write(f"- **Routing Accuracy:** {route_acc * 100:.2f}%\n")
        f.write(f"- **Answer Correctness:** {answer_acc * 100:.2f}%\n\n")
        f.write(f"### Phân rã theo nhóm câu hỏi:\n")
        f.write("| Nhóm câu hỏi | Số câu | Đạt | Tỷ lệ đạt (%) | Rewrite Acc (%) | Route Acc (%) | Answer Acc (%) |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for cat, c_info in summary["category_breakdown"].items():
            f.write(
                f"| `{cat}` | {c_info['total']} | {c_info['passed']} | {c_info['accuracy']*100:.1f}% | "
                f"{c_info['rewrite_acc']*100:.1f}% | {c_info['route_acc']*100:.1f}% | {c_info['answer_acc']*100:.1f}% |\n"
            )

    print("\n" + "=" * 65)
    print(f"             KẾT QUẢ BENCHMARK ROUND {round_num}")
    print("=" * 65)
    print(f"  Tổng số câu hỏi       : {total_count}")
    print(f"  Số câu đạt chuẩn      : {total_pass} / {total_count}")
    print(f"  Độ chính xác tổng thể : {accuracy_total * 100:.2f}%  (Mục tiêu: >= 90.0%)")
    print(f"  Rewriting Accuracy    : {rewrite_acc * 100:.2f}%")
    print(f"  Routing Accuracy      : {route_acc * 100:.2f}%")
    print(f"  Answer Correctness    : {answer_acc * 100:.2f}%")
    print(f"  KẾT LUẬN              : {verdict}")
    print("=" * 65)
    print(f"  Báo cáo chi tiết tại  : {summary_path}")
    print("=" * 65 + "\n")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Chạy benchmark đa lượt theo đợt")
    parser.add_argument("--round", type=int, default=1, choices=[1, 2, 3, 4, 5], help="Số thứ tự round (1..5)")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số câu để test nhanh")
    parser.add_argument("--output_dir", type=str, default=None, help="Thư mục xuất báo cáo")
    args = parser.parse_args()

    run_benchmark(round_num=args.round, limit=args.limit, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
