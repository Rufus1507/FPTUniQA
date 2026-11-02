"""FPTUniQA - Script Đánh giá Benchmark 150 Câu hỏi Đa Tầng Độ Khó (Easy -> Hard).

Quy mô:
- Tier 1 (Easy): 50 câu hỏi rõ ràng, có dấu, đầy đủ thông tin (E01 - E50)
- Tier 2 (Medium): 50 câu hỏi không dấu, từ lóng, viết tắt, ghép lai, khóa cũ, clarification, OOD (M01 - M50)
- Tier 3 (Hard): 50 câu hỏi lỗi gõ dấu telex, đa lượt, topic switch, disambiguation, quy chế ranh giới (H01 - H50)

Tổng: 150 câu hỏi toàn diện kiểm định pipeline, dictionary, normalization, router và session context.
Báo cáo lưu tại: reports/benchmark_150_results.json
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Cấu hình encoding stdout an toàn cho Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm src vào sys.path
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from FPTUniQA.pipeline.rag_pipeline import RAGPipeline

BENCHMARK_PATH = _ROOT / "data" / "evaluation" / "benchmark_150_difficulty.jsonl"
REPORT_PATH = _ROOT / "reports" / "benchmark_150_results.json"


def load_benchmark_150() -> List[Dict[str, Any]]:
    """Nạp danh sách 150 câu hỏi từ tệp JSONL."""
    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp benchmark: {BENCHMARK_PATH}")
    questions = []
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions


def run_benchmark():
    print("=" * 80)
    print("🚀 FPTUniQA - KHỞI CHẠY BỘ BENCHMARK 150 CÂU HỎI ĐA TẦNG ĐỘ KHÓ (EASY -> HARD)")
    print("=" * 80)
    print("Đang nạp chỉ mục và khởi tạo hệ thống...")

    rag = RAGPipeline(
        use_mock_fallback=False,
    )

    questions = load_benchmark_150()
    print(f"Đã nạp thành công {len(questions)} câu hỏi từ {BENCHMARK_PATH.name}.\n")

    results = []
    start_all = time.time()

    # Thống kê theo độ khó
    tier_stats = {
        "easy": {"total": 0, "correct": 0, "latencies": []},
        "medium": {"total": 0, "correct": 0, "latencies": []},
        "hard": {"total": 0, "correct": 0, "latencies": []},
    }

    route_counts = {}
    passed_count = 0

    print("Bắt đầu chạy 150 ca kiểm thử...\n")

    for idx, item in enumerate(questions, 1):
        qid = item["id"]
        diff = item.get("difficulty", "unknown")
        sid = item.get("session_id", f"session_auto_{idx}")
        query = item["query"]
        expected_route = item["expected_route"]
        desc = item.get("description", "")

        t0 = time.time()
        try:
            res = rag.answer(
                query=query,
                session_id=sid,
            )
            elapsed_ms = (time.time() - t0) * 1000

            actual_route = res.get("route", "uncertain")
            answer = res.get("answer", "")
            rewritten_q = res.get("rewritten_query", query)
            citations = res.get("citations", [])

            is_correct = (actual_route == expected_route)
            if is_correct:
                passed_count += 1
                status_icon = "✅"
            else:
                status_icon = "❌"

            # Cập nhật thống kê tier
            if diff in tier_stats:
                tier_stats[diff]["total"] += 1
                if is_correct:
                    tier_stats[diff]["correct"] += 1
                tier_stats[diff]["latencies"].append(elapsed_ms)

            route_counts[actual_route] = route_counts.get(actual_route, 0) + 1

            record = {
                "id": qid,
                "difficulty": diff,
                "session_id": sid,
                "query": query,
                "rewritten_query": rewritten_q,
                "expected_route": expected_route,
                "actual_route": actual_route,
                "is_correct": is_correct,
                "elapsed_ms": round(elapsed_ms, 2),
                "answer_snippet": answer[:120] + "..." if len(answer) > 120 else answer,
                "citations_count": len(citations),
                "description": desc,
            }
            results.append(record)

            preview = query[:40] + ("..." if len(query) > 40 else "")
            print(f"[{qid:>3}] {status_icon} ({elapsed_ms:>6.1f}ms) [{diff.upper():^6}] [{actual_route:<17}] {preview}")
            if not is_correct:
                print(f"      ⚠️ Kỳ vọng: '{expected_route}' nhưng nhận được: '{actual_route}'")
                print(f"      ↳ Phản hồi: {record['answer_snippet']}")

        except Exception as exc:
            elapsed_ms = (time.time() - t0) * 1000
            print(f"[{qid:>3}] 💥 LỖI NGOẠI LỆ ({elapsed_ms:.1f}ms): {exc}")
            results.append({
                "id": qid,
                "difficulty": diff,
                "session_id": sid,
                "query": query,
                "expected_route": expected_route,
                "actual_route": "error",
                "is_correct": False,
                "error": str(exc),
                "elapsed_ms": round(elapsed_ms, 2),
                "description": desc,
            })
            if diff in tier_stats:
                tier_stats[diff]["total"] += 1
                tier_stats[diff]["latencies"].append(elapsed_ms)

    total_time = time.time() - start_all
    all_latencies = sorted([r["elapsed_ms"] for r in results if "elapsed_ms" in r])
    avg_lat = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0
    p50_lat = all_latencies[int(len(all_latencies) * 0.50)] if all_latencies else 0.0
    p95_lat = all_latencies[int(len(all_latencies) * 0.95)] if all_latencies else 0.0

    print("\n" + "=" * 80)
    print("📊 BÁO CÁO TỔNG HỢP KẾT QUẢ BENCHMARK 150 CÂU HỎI")
    print("=" * 80)
    acc_pct = (passed_count / len(questions)) * 100
    print(f"• Tổng số câu kiểm thử:     {len(questions)}")
    print(f"• Độ chính xác Định tuyến:  {passed_count}/{len(questions)} ({acc_pct:.1f}%)")
    print(f"• Tổng thời gian thực thi:  {total_time:.2f}s")
    print(f"• Độ trễ trung bình:        {avg_lat:.1f} ms")
    print(f"• Độ trễ p50:               {p50_lat:.1f} ms | p95: {p95_lat:.1f} ms\n")

    print("📈 PHÂN BỐ KẾT QUẢ THEO ĐỘ KHÓ (DIFFICULTY BREAKDOWN):")
    for diff in ["easy", "medium", "hard"]:
        st = tier_stats[diff]
        t_acc = (st["correct"] / st["total"] * 100) if st["total"] > 0 else 0.0
        t_lat = sum(st["latencies"]) / len(st["latencies"]) if st["latencies"] else 0.0
        print(f"  - [{diff.upper():<6}]: {st['correct']:>2}/{st['total']:>2} ({t_acc:>5.1f}%) | Độ trễ TB: {t_lat:>5.1f} ms")

    print("\n📌 PHÂN BỐ ROUTING:")
    for route, cnt in sorted(route_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {route:<20}: {cnt:>2} ({(cnt/len(questions)*100):>5.1f}%)")
    print("=" * 80)

    # Lưu báo cáo chi tiết JSON
    report_data = {
        "benchmark_suite": "benchmark_150_difficulty",
        "total_questions": len(questions),
        "passed_routing": passed_count,
        "routing_accuracy_pct": round(acc_pct, 2),
        "total_time_seconds": round(total_time, 2),
        "latency_stats_ms": {
            "avg": round(avg_lat, 2),
            "p50": round(p50_lat, 2),
            "p95": round(p95_lat, 2),
        },
        "difficulty_breakdown": {
            d: {
                "total": tier_stats[d]["total"],
                "correct": tier_stats[d]["correct"],
                "accuracy_pct": round((tier_stats[d]["correct"] / tier_stats[d]["total"] * 100), 2) if tier_stats[d]["total"] > 0 else 0.0,
                "avg_latency_ms": round(sum(tier_stats[d]["latencies"]) / len(tier_stats[d]["latencies"]), 2) if tier_stats[d]["latencies"] else 0.0,
            }
            for d in ["easy", "medium", "hard"]
        },
        "route_distribution": route_counts,
        "results": results,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Đã lưu báo cáo chi tiết tại: {REPORT_PATH}")


if __name__ == "__main__":
    run_benchmark()
