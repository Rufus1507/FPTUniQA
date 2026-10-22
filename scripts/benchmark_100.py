"""Script thực thi đánh giá toàn diện hệ thống FPTUniQA trên bộ dữ liệu chuẩn benchmark 100 câu hỏi.

Đo lường:
1. Độ trễ (Latency: Mean, Min, Max, p50, p95, p99).
2. Hiệu năng Cache (Cache Hits, Misses, Hit Rate).
3. Độ chính xác định tuyến (Routing Accuracy).
4. Chất lượng câu trả lời (Faithfulness, Relevance, Hallucination Rate).
5. Khả năng từ chối ngoài miền (OOD Rejection Accuracy).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Đảm bảo đường dẫn root có trong sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from FPTUniQA.evaluation.evaluator import RAGEvaluator
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline
from FPTUniQA.utils.config import load_config
from FPTUniQA.utils.io import read_jsonl, write_json
from FPTUniQA.utils.logger import get_logger

logger = get_logger("scripts.benchmark_100")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Chạy benchmark 100 câu hỏi toàn diện cho hệ thống FPTUniQA RAG & Structured Lookup."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/evaluation.yaml",
        help="Đường dẫn file cấu hình evaluation (mặc định: configs/evaluation.yaml)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Đường dẫn file dữ liệu benchmark JSONL (mặc định: lấy từ config hoặc data/evaluation/benchmark_100.jsonl)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Thư mục xuất báo cáo (mặc định: experiments/benchmark_100)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Giới hạn số lượng câu hỏi cần chạy (để kiểm tra nhanh, mặc định chạy toàn bộ 100 câu)",
    )
    return parser.parse_args()


def generate_markdown_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """Tạo báo cáo chi tiết định dạng Markdown chuyên nghiệp."""
    lat = report_data.get("latency_metrics", {})
    cache = report_data.get("cache_metrics", {})
    routing = report_data.get("routing_metrics", {})
    quality = report_data.get("answer_quality_metrics", {})
    ood = report_data.get("ood_metrics", {})

    content = f"""# Báo Cáo Đánh Giá Thực Nghiệm Hệ Thống FPTUniQA (Benchmark 100)

**Thời điểm thực thi:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Tổng số câu hỏi đánh giá:** {report_data.get('total_evaluated')}  
**Môi trường:** Python {sys.version.split()[0]} on {sys.platform}

---

## 1. Tổng Quan Chỉ Số Hiệu Năng Cốt Lõi

| Nhóm Chỉ Số | Tên Chỉ Số | Kết Quả Thực Nghiệm | Tiêu Chuẩn Kỹ Thuật |
| :--- | :--- | :---: | :---: |
| **Định Tuyến (Routing)** | Routing Accuracy | **{routing.get('routing_accuracy', 0.0) * 100:.1f}%** ({routing.get('correct_routes')}/{routing.get('total_evaluated')}) | >= 85.0% |
| **Từ Chối Ngoài Miền** | OOD Rejection Accuracy | **{ood.get('ood_rejection_accuracy', 0.0) * 100:.1f}%** | >= 90.0% |
| **Độ Trung Thực** | Faithfulness | **{quality.get('mean_faithfulness', 0.0):.4f}** | >= 0.7500 |
| **Độ Tương Đồng Đáp Án** | Answer Relevance | **{quality.get('mean_relevance', 0.0):.4f}** | >= 0.4000 |
| **Tỷ Lệ Ảo Giác** | Hallucination Rate | **{quality.get('hallucination_rate', 0.0) * 100:.1f}%** | <= 15.0% |
| **Độ Trễ Trung Bình** | Latency Mean | **{lat.get('mean_ms', 0.0):.1f} ms** | N/A |
| **Độ Trễ P50** | Latency P50 | **{lat.get('p50_ms', 0.0):.1f} ms** | N/A |
| **Độ Trễ P95** | Latency P95 | **{lat.get('p95_ms', 0.0):.1f} ms** | N/A |
| **Tỷ Lệ Cache Hit** | Retrieval Cache Hit Rate | **{cache.get('hit_rate', 0.0) * 100:.1f}%** | N/A |

---

## 2. Phân Phối Độ Trễ (Latency Distribution)

- **Thời gian trung bình (Mean):** `{lat.get('mean_ms', 0.0)} ms`
- **Trung vị (Median / P50):** `{lat.get('p50_ms', 0.0)} ms`
- **Phân vị 95 (P95):** `{lat.get('p95_ms', 0.0)} ms`
- **Phân vị 99 (P99):** `{lat.get('p99_ms', 0.0)} ms`
- **Nhanh nhất (Min):** `{lat.get('min_ms', 0.0)} ms`
- **Chậm nhất (Max):** `{lat.get('max_ms', 0.0)} ms`

---

## 3. Hoạt Động Của Retrieval Caching Layer

- **Tổng số lần tra cứu Cache:** `{cache.get('total_lookups', 0)}`
- **Số lần Cache Hit:** `{cache.get('hits', 0)}`
- **Số lần Cache Miss:** `{cache.get('misses', 0)}`
- **Tỷ lệ trúng Cache (Hit Rate):** `{cache.get('hit_rate', 0.0) * 100:.2f}%`
- **Số bản ghi đang lưu trữ:** `{cache.get('cached_entries', 0)}`

---

## 4. Phân Bố Kết Quả Theo Danh Mục Câu Hỏi

| Danh Mục | Số Câu | Tỷ Lệ Tuyến Chính Xác | Tuyến Phổ Biến |
| :--- | :---: | :---: | :---: |
"""
    cat_stats = report_data.get("category_breakdown", {})
    for cat, stat in cat_stats.items():
        acc = (stat["correct"] / stat["count"] * 100) if stat["count"] > 0 else 0.0
        content += f"| `{cat}` | {stat['count']} | {acc:.1f}% ({stat['correct']}/{stat['count']}) | `{stat.get('most_frequent_route', 'N/A')}` |\n"

    content += """
---

*Báo cáo được tạo tự động bởi FPTUniQA Automated Benchmark Tool.*
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    args = parse_args()

    # 1. Nạp cấu hình
    cfg = load_config(args.config)
    bm_cfg = cfg.get("benchmark_100", {})

    dataset_path = args.dataset or bm_cfg.get("dataset_path", "data/evaluation/benchmark_100.jsonl")
    output_dir = Path(args.output_dir or bm_cfg.get("output_dir", "experiments/benchmark_100"))
    results_json_path = output_dir / "results.json"
    report_md_path = output_dir / "report.md"

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Nạp dataset benchmark từ: {dataset_path}")
    questions = read_jsonl(dataset_path)

    if args.limit and args.limit > 0:
        logger.info(f"Giới hạn số lượng câu hỏi kiểm thử: {args.limit}/{len(questions)}")
        questions = questions[: args.limit]

    logger.info(f"Tổng số câu hỏi sẽ thực thi: {len(questions)}")

    # 2. Khởi tạo Pipeline & Evaluator
    logger.info("Khởi tạo RAG Pipeline...")
    pipeline = RAGPipeline()
    if pipeline.retriever is not None:
        pipeline.retriever.ensure_loaded()
    evaluator = RAGEvaluator(pipeline)

    # 3. Thực thi tuần tự toàn bộ câu hỏi
    run_results = []
    latencies = []
    predictions = []

    print("\n" + "=" * 65)
    print("      BẮT ĐẦU CHẠY BENCHMARK 100 CÂU HỎI HỆ THỐNG FPTUNIQA")
    print("=" * 65)

    start_all = time.time()
    for idx, q in enumerate(questions, 1):
        query_text = q["query"]
        t0 = time.perf_counter()
        res = pipeline.answer(query_text)
        duration_ms = (time.perf_counter() - t0) * 1000.0

        run_results.append(res)
        latencies.append(duration_ms)

        expected_r = q.get("expected_route", "N/A")
        actual_r = res.get("route", "N/A")
        status_sym = "[OK]" if expected_r == actual_r else "[DIFF]"

        if idx % 10 == 0 or idx == len(questions):
            print(f"[{idx:3d}/{len(questions):3d}] {status_sym} Route: {actual_r:17s} ({duration_ms:6.1f}ms) | Q: {query_text[:40]}...")

        predictions.append({
            "q_id": q.get("q_id"),
            "query": query_text,
            "category": q.get("category"),
            "expected_route": expected_r,
            "actual_route": actual_r,
            "answer": res.get("answer", ""),
            "golden_answer": q.get("golden_answer", ""),
            "citations_count": len(res.get("citations", [])),
            "latency_ms": round(duration_ms, 2),
        })

    total_duration = time.time() - start_all
    logger.info(f"Hoàn thành toàn bộ {len(questions)} câu hỏi trong {total_duration:.2f}s")

    # 4. Tính toán Metrics
    routing_metrics = evaluator.evaluate_routing(questions, run_results)
    latency_metrics = evaluator.evaluate_latency(latencies)
    cache_metrics = evaluator.evaluate_cache_performance()
    quality_metrics = evaluator.evaluate_answer_quality(questions, run_results)

    # Đánh giá OOD cho tập câu hỏi có nhãn ood
    ood_subset = [q for q, r in zip(questions, run_results) if q.get("category") == "ood"]
    ood_results = [r for q, r in zip(questions, run_results) if q.get("category") == "ood"]
    ood_accuracy = (
        sum(1 for r in ood_results if r.get("intent") == "ood" or "ngoài phạm vi" in r.get("answer", "").lower())
        / len(ood_results)
        if ood_results
        else 1.0
    )
    ood_metrics = {"ood_rejection_accuracy": round(ood_accuracy, 4), "ood_count": len(ood_subset)}

    # Thống kê chi tiết theo từng danh mục
    category_breakdown = {}
    for p in predictions:
        cat = p["category"]
        if cat not in category_breakdown:
            category_breakdown[cat] = {"count": 0, "correct": 0, "routes": {}}
        category_breakdown[cat]["count"] += 1
        if p["expected_route"] == p["actual_route"]:
            category_breakdown[cat]["correct"] += 1
        r = p["actual_route"]
        category_breakdown[cat]["routes"][r] = category_breakdown[cat]["routes"].get(r, 0) + 1

    for cat, data in category_breakdown.items():
        routes = data["routes"]
        most_freq = max(routes.items(), key=lambda x: x[1])[0] if routes else "N/A"
        data["most_frequent_route"] = most_freq

    # 5. Xuất báo cáo JSON & Markdown
    final_report = {
        "benchmark_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_evaluated": len(questions),
        "total_time_seconds": round(total_duration, 2),
        "routing_metrics": routing_metrics,
        "latency_metrics": latency_metrics,
        "cache_metrics": cache_metrics,
        "answer_quality_metrics": quality_metrics,
        "ood_metrics": ood_metrics,
        "category_breakdown": category_breakdown,
        "predictions": predictions,
    }

    write_json(final_report, results_json_path)
    generate_markdown_report(final_report, report_md_path)

    # 6. Hiển thị tóm tắt trên terminal
    print("\n" + "=" * 65)
    print("           TỔNG HỢP KẾT QUẢ BENCHMARK 100")
    print("=" * 65)
    print(f"  * Tổng số câu hỏi:        {len(questions)}")
    print(f"  * Tổng thời gian:         {total_duration:.2f} s")
    print(f"  * Routing Accuracy:       {routing_metrics['routing_accuracy'] * 100:.1f}% ({routing_metrics['correct_routes']}/{routing_metrics['total_evaluated']})")
    print(f"  * OOD Rejection Accuracy: {ood_metrics['ood_rejection_accuracy'] * 100:.1f}%")
    print(f"  * Mean Faithfulness:      {quality_metrics['mean_faithfulness']:.4f}")
    print(f"  * Mean Relevance:         {quality_metrics['mean_relevance']:.4f}")
    print(f"  * Hallucination Rate:     {quality_metrics['hallucination_rate'] * 100:.1f}%")
    print(f"  * Latency Mean:           {latency_metrics['mean_ms']:.1f} ms")
    print(f"  * Latency P50:            {latency_metrics['p50_ms']:.1f} ms")
    print(f"  * Latency P95:            {latency_metrics['p95_ms']:.1f} ms")
    print(f"  * Cache Hit Rate:         {cache_metrics['hit_rate'] * 100:.1f}% ({cache_metrics['hits']}/{cache_metrics['total_lookups']})")
    print("=" * 65)
    print(f"  -> File kết quả JSON:     {results_json_path}")
    print(f"  -> Báo cáo Markdown:      {report_md_path}\n")


if __name__ == "__main__":
    main()
