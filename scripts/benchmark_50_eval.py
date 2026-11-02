"""Script kiểm thử toàn diện 50 câu hỏi thực tế trên hệ thống FPTUniQA:
- Nhóm A (15 câu): Quy chế & Chính sách học vụ đơn lượt.
- Nhóm B (15 câu): Từ điển miền, Chuẩn hóa thực thể (Ngành 2026, Môn CKB, Không dấu, Viết tắt).
- Nhóm C (20 câu): Chuỗi hội thoại Đa lượt (Multi-turn Context Accumulation & Slot Filling).
"""

import sys
import os
import time
import json
from pathlib import Path

sys.path.insert(0, os.path.abspath("src"))

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from FPTUniQA.pipeline.rag_pipeline import RAGPipeline


BENCHMARK_SUITE = [
    # =========================================================================
    # NHÓM A: QUY CHẾ & CHÍNH SÁCH HỌC VỤ ĐƠN LƯỢT (15 câu)
    # =========================================================================
    {
        "id": "A01",
        "category": "academic_policy",
        "session_id": "session_single_a01",
        "query": "Điều kiện để không bị cảnh cáo học vụ là gì?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "A02",
        "category": "academic_policy",
        "session_id": "session_single_a02",
        "query": "Sinh viên vắng bao nhiêu phần trăm số buổi thì bị cấm thi?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "A03",
        "category": "academic_policy",
        "session_id": "session_single_a03",
        "query": "Điều kiện xét tốt nghiệp đại học như thế nào?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "A04",
        "category": "academic_policy",
        "session_id": "session_single_a04",
        "query": "Điều kiện làm đồ án tốt nghiệp Capstone là gì?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "A05",
        "category": "academic_policy",
        "session_id": "session_single_a05",
        "query": "Sinh viên được đăng ký tối đa bao nhiêu tín chỉ trong một học kỳ?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "A06",
        "category": "academic_policy",
        "session_id": "session_single_a06",
        "query": "Điều kiện để duy trì học bổng Nguyễn Văn Đạo qua các kỳ là gì?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "A07",
        "category": "academic_policy",
        "session_id": "session_single_a07",
        "query": "Sinh viên bị điểm F thì phải học lại hay thi lại?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "A08",
        "category": "academic_policy",
        "session_id": "session_single_a08",
        "query": "Quy định rút môn học trong kỳ của ĐH FPT như thế nào?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "A09",
        "category": "academic_policy",
        "session_id": "session_single_a09",
        "query": "Sinh viên muốn chuyển ngành hoặc chuyển cơ sở đào tạo cần thỏa mãn điều kiện gì?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "A10",
        "category": "academic_policy",
        "session_id": "session_single_a10",
        "query": "Thời gian tối đa để hoàn thành chương trình đào tạo đại học là bao lâu?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "A11",
        "category": "common_fees",
        "session_id": "session_single_a11",
        "query": "Lệ phí thi lại của trường Đại học FPT là bao nhiêu?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "A12",
        "category": "common_fees",
        "session_id": "session_single_a12",
        "query": "Lệ phí học lại mỗi tín chỉ là bao nhiêu tiền?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "A13",
        "category": "common_fees",
        "session_id": "session_single_a13",
        "query": "Giai đoạn đi thực tập doanh nghiệp OJT có phải đóng học phí không?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "A14",
        "category": "common_fees",
        "session_id": "session_single_a14",
        "query": "Phí ký túc xá phân hiệu Hòa Lạc là bao nhiêu một kỳ?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "A15",
        "category": "common_fees",
        "session_id": "session_single_a15",
        "query": "Lệ phí công nhận tốt nghiệp và cấp bằng là bao nhiêu?",
        "expected_route": "structured_lookup"
    },

    # =========================================================================
    # NHÓM B: TỪ ĐIỂN MIỀN & CHUẨN HÓA THỰC THỂ (15 câu)
    # =========================================================================
    {
        "id": "B01",
        "category": "dictionary_course",
        "session_id": "session_single_b01",
        "query": "Môn cơ sở lập trình C có bao nhiêu tín chỉ?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B02",
        "category": "dictionary_course",
        "session_id": "session_single_b02",
        "query": "Môn CSD201 cần học môn tiên quyết nào?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B03",
        "category": "dictionary_course",
        "session_id": "session_single_b03",
        "query": "Môn nhập môn khoa học máy tính học ở kỳ mấy?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B04",
        "category": "dictionary_course",
        "session_id": "session_single_b04",
        "query": "Giáo trình môn cấu trúc dữ liệu và giải thuật là sách gì?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B05",
        "category": "dictionary_major_2026",
        "session_id": "session_single_b05",
        "query": "Học phí ngành Thiết kế vi mạch bán dẫn năm 2026 tại phân hiệu Quy Nhơn là bao nhiêu?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B06",
        "category": "dictionary_major_2026",
        "session_id": "session_single_b06",
        "query": "Học phí ngành Công nghệ ô tô số khóa 2026 cơ sở Cần Thơ là bao nhiêu?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B07",
        "category": "dictionary_major_2026",
        "session_id": "session_single_b07",
        "query": "Học phí ngành Luật kinh tế năm 2026 tại Hà Nội là bao nhiêu?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B08",
        "category": "unaccented_vietnamese",
        "session_id": "session_single_b08",
        "query": "hoc phi k22 co so da nang la bao nhieu",
        "expected_route": "clarification"
    },
    {
        "id": "B09",
        "category": "unaccented_vietnamese",
        "session_id": "session_single_b09",
        "query": "nganh tri tue nhan tao co so quy nhon hoc phi bao nhieu",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B10",
        "category": "unaccented_vietnamese",
        "session_id": "session_single_b10",
        "query": "mon csd201 hoc ky may",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B11",
        "category": "student_abbreviations",
        "session_id": "session_single_b11",
        "query": "Sinh viên nợ học phí thì có được ĐKM không?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "B12",
        "category": "student_abbreviations",
        "session_id": "session_single_b12",
        "query": "Sinh viên muốn xem CTĐT ngành KTPM thì xem ở đâu?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "B13",
        "category": "cohort_mapping",
        "session_id": "session_single_b13",
        "query": "Học phí ngành AI của sinh viên nhập học năm 2026 là bao nhiêu?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B14",
        "category": "campus_discount",
        "session_id": "session_single_b14",
        "query": "Chính sách ưu đãi học phí tại phân hiệu Quy Nhơn là bao nhiêu phần trăm?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "B15",
        "category": "campus_discount",
        "session_id": "session_single_b15",
        "query": "Học phí tại phân hiệu Cần Thơ có ưu đãi giảm 30% đúng không?",
        "expected_route": "structured_lookup"
    },

    # =========================================================================
    # NHÓM C: CHUỖI HỘI THOẠI ĐA LƯỢT (20 câu chia thành 4 phiên liên hoàn)
    # =========================================================================
    # Phiên C1: Tra cứu so sánh biểu phí đa phân hiệu và đa khóa (5 lượt)
    {
        "id": "C01",
        "category": "multiturn_fee_comparison",
        "session_id": "session_multi_c1",
        "query": "hoc phi cntt k20 can tho",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C02",
        "category": "multiturn_fee_comparison",
        "session_id": "session_multi_c1",
        "query": "con k19 thi sao?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C03",
        "category": "multiturn_fee_comparison",
        "session_id": "session_multi_c1",
        "query": "the con o da nang?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C04",
        "category": "multiturn_fee_comparison",
        "session_id": "session_multi_c1",
        "query": "con nganh AI thi sao?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C05",
        "category": "multiturn_fee_comparison",
        "session_id": "session_multi_c1",
        "query": "hoc phi nay bao gom nhung khoan nao?",
        "expected_route": "structured_lookup"
    },

    # Phiên C2: Hỏi làm rõ, tích lũy slot và chuyển chủ đề (5 lượt)
    {
        "id": "C06",
        "category": "multiturn_clarify_accumulate",
        "session_id": "session_multi_c2",
        "query": "học phí",
        "expected_route": "clarification"
    },
    {
        "id": "C07",
        "category": "multiturn_clarify_accumulate",
        "session_id": "session_multi_c2",
        "query": "ngành KTPM khóa 2026",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C08",
        "category": "multiturn_clarify_accumulate",
        "session_id": "session_multi_c2",
        "query": "ở phân hiệu Quy Nhơn",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C09",
        "category": "multiturn_clarify_accumulate",
        "session_id": "session_multi_c2",
        "query": "phân hiệu này có chính sách ưu đãi gì?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C10",
        "category": "multiturn_clarify_accumulate",
        "session_id": "session_multi_c2",
        "query": "môn PRF192 có bao nhiêu tín chỉ?",
        "expected_route": "structured_lookup"
    },

    # Phiên C3: Khảo sát chuyên sâu môn học CKB (5 lượt)
    {
        "id": "C11",
        "category": "multiturn_course_ckb",
        "session_id": "session_multi_c3",
        "query": "môn CSD201",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C12",
        "category": "multiturn_course_ckb",
        "session_id": "session_multi_c3",
        "query": "môn này cần tiên quyết môn gì?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C13",
        "category": "multiturn_course_ckb",
        "session_id": "session_multi_c3",
        "query": "học mấy tín chỉ?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C14",
        "category": "multiturn_course_ckb",
        "session_id": "session_multi_c3",
        "query": "giáo trình môn này là sách gì?",
        "expected_route": "structured_lookup"
    },
    {
        "id": "C15",
        "category": "multiturn_course_ckb",
        "session_id": "session_multi_c3",
        "query": "hình thức đánh giá và thi cử như thế nào?",
        "expected_route": "structured_lookup"
    },

    # Phiên C4: Quy chế học vụ, Cảnh cáo học tập tới Tốt nghiệp (5 lượt)
    {
        "id": "C16",
        "category": "multiturn_policy_flow",
        "session_id": "session_multi_c4",
        "query": "Quy định về cảnh cáo học vụ như thế nào?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "C17",
        "category": "multiturn_policy_flow",
        "session_id": "session_multi_c4",
        "query": "nếu bị 2 lần liên tiếp thì sao?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "C18",
        "category": "multiturn_policy_flow",
        "session_id": "session_multi_c4",
        "query": "bị cảnh cáo có được đăng ký làm đồ án tốt nghiệp không?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "C19",
        "category": "multiturn_policy_flow",
        "session_id": "session_multi_c4",
        "query": "thế điều kiện làm đồ án capstone là gì?",
        "expected_route": "rag_pipeline"
    },
    {
        "id": "C20",
        "category": "multiturn_policy_flow",
        "session_id": "session_multi_c4",
        "query": "cảm ơn trợ lý nhé",
        "expected_route": "ood"
    },
]


def run_benchmark():
    print("=" * 80)
    print("🚀 FPTUniQA - KHỞI CHẠY BỘ BENCHMARK ĐÁNH GIÁ 50 CÂU HỎI THỰC TẾ")
    print("=" * 80)
    print("Đang nạp chỉ mục và khởi tạo hệ thống...")

    pipeline = RAGPipeline(use_mock_fallback=False)
    results = []
    
    start_total_time = time.time()
    route_stats = {"structured_lookup": 0, "rag_pipeline": 0, "clarification": 0, "ood": 0, "uncertain": 0, "other": 0}
    latencies = []
    success_count = 0

    print(f"\nBắt đầu chạy {len(BENCHMARK_SUITE)} ca kiểm thử...\n")

    for idx, item in enumerate(BENCHMARK_SUITE, 1):
        test_id = item["id"]
        category = item["category"]
        session_id = item["session_id"]
        query = item["query"]
        expected_route = item.get("expected_route")

        t0 = time.time()
        res = pipeline.answer(query, session_id=session_id)
        latency = (time.time() - t0) * 1000.0
        latencies.append(latency)

        actual_route = res.get("route", "unknown")
        rewritten = res.get("rewritten_query", query)
        answer = res.get("answer", "")
        citations = res.get("citations", [])
        
        # Thống kê route
        route_key = actual_route.lower()
        if "structured" in route_key:
            route_stats["structured_lookup"] += 1
            simple_route = "structured_lookup"
        elif "clarification" in route_key:
            route_stats["clarification"] += 1
            simple_route = "clarification"
        elif "ood" in route_key:
            route_stats["ood"] += 1
            simple_route = "ood"
        elif "rag" in route_key:
            route_stats["rag_pipeline"] += 1
            simple_route = "rag_pipeline"
        elif "uncertain" in route_key:
            route_stats["uncertain"] += 1
            simple_route = "uncertain"
        else:
            route_stats["other"] += 1
            simple_route = actual_route

        # Đánh giá tính chính xác của Route
        is_route_match = (expected_route is None) or (expected_route.lower() in simple_route)
        if is_route_match:
            success_count += 1
            status_symbol = "✅"
        else:
            status_symbol = "⚠️"

        first_line_ans = answer.strip().splitlines()[0] if answer else "[Không có câu trả lời]"
        if len(first_line_ans) > 70:
            first_line_ans = first_line_ans[:67] + "..."

        print(f"[{test_id}] {status_symbol} ({latency:5.1f}ms) [{simple_route:18}] {query[:35]:35}")
        if rewritten != query:
            print(f"      ↳ [Rewritten]: '{rewritten}'")
        print(f"      ↳ [Phản hồi]:  {first_line_ans}")

        results.append({
            "id": test_id,
            "category": category,
            "session_id": session_id,
            "query": query,
            "rewritten_query": rewritten,
            "expected_route": expected_route,
            "actual_route": actual_route,
            "simple_route": simple_route,
            "is_route_match": is_route_match,
            "latency_ms": round(latency, 2),
            "citations_count": len(citations),
            "answer_preview": first_line_ans,
            "full_answer": answer
        })

    total_time = time.time() - start_total_time
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    latencies_sorted = sorted(latencies)
    p50_latency = latencies_sorted[int(len(latencies_sorted) * 0.5)]
    p95_latency = latencies_sorted[int(len(latencies_sorted) * 0.95)]
    route_accuracy = (success_count / len(BENCHMARK_SUITE)) * 100.0

    print("\n" + "=" * 80)
    print("📊 BÁO CÁO TỔNG HỢP KẾT QUẢ BENCHMARK 50 CÂU HỎI")
    print("=" * 80)
    print(f"• Tổng số câu kiểm thử:     {len(BENCHMARK_SUITE)}")
    print(f"• Độ chính xác Định tuyến:  {success_count}/{len(BENCHMARK_SUITE)} ({route_accuracy:.1f}%)")
    print(f"• Tổng thời gian thực thi:  {total_time:.2f}s")
    print(f"• Độ trễ trung bình:        {avg_latency:.1f} ms")
    print(f"• Độ trễ p50:               {p50_latency:.1f} ms | p95: {p95_latency:.1f} ms")
    print("\n📌 Phân bố Routing:")
    for r_name, count in route_stats.items():
        pct = (count / len(BENCHMARK_SUITE)) * 100.0
        print(f"  - {r_name:20}: {count:2d} ({pct:5.1f}%)")
    print("=" * 80)

    # Lưu kết quả chi tiết ra file JSON
    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "benchmark_50_results.json"
    
    summary_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_queries": len(BENCHMARK_SUITE),
        "route_accuracy": round(route_accuracy, 2),
        "total_time_seconds": round(total_time, 2),
        "latency_metrics": {
            "avg_ms": round(avg_latency, 2),
            "p50_ms": round(p50_latency, 2),
            "p95_ms": round(p95_latency, 2)
        },
        "route_distribution": route_stats,
        "details": results
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Đã lưu báo cáo chi tiết tại: {out_file.resolve()}")
    return summary_report


if __name__ == "__main__":
    run_benchmark()
