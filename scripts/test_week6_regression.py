"""Script kiểm thử toàn diện Tuần 6 (Regression + Guardrails). Phụ trách: TV3.

Bao gồm 3 phần:
Phần 1: Hồi quy 10 câu hỏi Tuần 4 (8 câu chuẩn + 2 câu thiếu slot).
Phần 2: Hồi quy 4 kịch bản đa lượt Tuần 5 (8 lượt tổng cộng).
Phần 3: Kiểm thử 2 Guardrails mới của Tuần 6:
  - Guardrail 1: Câu hỏi độ tin cậy thấp (confidence < 0.5) -> Route: UNCERTAIN.
  - Guardrail 2: Câu hỏi kích hoạt kiểm tra hậu kỳ ảo giác số liệu -> possible_hallucination = True.
"""

import json
import sys
from pathlib import Path

# Đảm bảo nạp đúng src/ và root vào sys.path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

from university_qa.pipeline.rag_pipeline import RAGPipeline
from university_qa.generation.guardrails import check_hallucination
from contracts import ParsedQuery
from university_qa.query.router import route_query

# ==============================================================================
# DỮ LIỆU KIỂM THỬ
# ==============================================================================

WEEK4_QUERIES = [
    # 8 câu chuẩn
    "Điều kiện để không bị cảnh cáo học vụ là gì?",
    "Sinh viên vắng bao nhiêu phần trăm số buổi thì bị cấm thi?",
    "Điều kiện xét tốt nghiệp đại học như thế nào?",
    "Điều kiện làm đồ án tốt nghiệp Capstone là gì?",
    "Học phí ngành AI khoá 2026 là bao nhiêu?",
    "Học phí ngành CNTT khoá 2024 là bao nhiêu?",
    "Hôm nay thời tiết Hà Nội thế nào?",
    "Điểm chuẩn ngành Công nghệ thông tin của Đại học Bách Khoa là bao nhiêu?",
    # 2 câu thiếu slot
    "Học phí ngành AI là bao nhiêu?",
    "Học phí khóa 2026 là bao nhiêu?",
]

WEEK5_SCENARIOS = [
    {
        "name": "Kịch bản 1: Tra cứu học phí liên tiếp theo khóa (Milestone bắt buộc)",
        "session_id": "reg_tuition_01",
        "turns": [
            "Học phí ngành AI khoá 2026 là bao nhiêu?",
            "Còn năm 2023 thì sao?",
        ],
    },
    {
        "name": "Kịch bản 2: Quy chế học vụ - Điểm danh và thi lại",
        "session_id": "reg_policy_02",
        "turns": [
            "Sinh viên vắng bao nhiêu phần trăm số buổi thì bị cấm thi?",
            "Nếu bị cấm thi thì có được thi lại không?",
        ],
    },
    {
        "name": "Kịch bản 3: Điều kiện tốt nghiệp và chuẩn ngoại ngữ",
        "session_id": "reg_grad_03",
        "turns": [
            "Điều kiện xét tốt nghiệp đại học như thế nào?",
            "Chuẩn tiếng Anh cụ thể là bao nhiêu?",
        ],
    },
    {
        "name": "Kịch bản 4: Hỏi làm rõ và bổ sung thông tin thiếu slot",
        "session_id": "reg_clarify_04",
        "turns": [
            "Học phí ngành CNTT là bao nhiêu?",
            "Khóa 2024 nhé",
        ],
    },
]


def run_regression_tests():
    pipeline = RAGPipeline()

    print("=" * 80)
    print("PHẦN 1: HỒI QUY 10 CÂU HỎI TUẦN 4 (ROUTING & STRUCTURED LOOKUP)")
    print("=" * 80)
    for idx, q in enumerate(WEEK4_QUERIES, start=1):
        res = pipeline.answer(q)
        route = res.get("route", "").upper()
        print(f"[{idx:02d}/10] \"{q}\" -> Route: {route} | Answer: {res['answer'][:70]}...")

    print("\n" + "=" * 80)
    print("PHẦN 2: HỒI QUY 4 KỊCH BẢN ĐA LƯỢT TUẦN 5 (QUERY REWRITING)")
    print("=" * 80)
    for s_idx, sc in enumerate(WEEK5_SCENARIOS, start=1):
        print(f"\n[*] {sc['name']} ({sc['session_id']})")
        for t_idx, q in enumerate(sc["turns"], start=1):
            res = pipeline.answer(q, session_id=sc["session_id"])
            print(f"    Lượt {t_idx}: \"{q}\" -> Rewritten: \"{res['rewritten_query']}\" -> Route: {res['route'].upper()}")

    print("\n" + "=" * 80)
    print("PHẦN 3: KIỂM THỬ 2 GUARDRAILS MỚI CỦA TUẦN 6")
    print("=" * 80)

    # Test Guardrail 1: Confidence thấp (< 0.5) kích hoạt nhánh UNCERTAIN
    print("\n[GUARDRAIL 1] Kiểm tra câu hỏi có độ tin cậy thấp (confidence < 0.5):")
    low_conf_query = ParsedQuery(
        intent="policy_lookup",
        slots={"topic": "unknown"},
        confidence=0.35,  # < 0.5
        parser_method="rule_based",
        fallback_used=True,
        original_query="alo trường gì đó ơi kì này học cái gì nhỉ?",
    )
    g1_route = route_query(low_conf_query)
    print(f"  ├─ Query           : \"{low_conf_query.original_query}\"")
    print(f"  ├─ Confidence      : {low_conf_query.confidence} (< 0.5)")
    print(f"  ├─ Route Decision  : {str(g1_route).upper()}")
    print(f"  └─ Clarification Msg: {getattr(g1_route, 'clarification', '')}")

    # Test Guardrail 2: Kiểm tra phát hiện ảo giác số liệu không có trong context
    print("\n[GUARDRAIL 2] Kiểm tra post-check phát hiện số liệu lạ (possible_hallucination):")
    g2_query = "Nếu sinh viên bị cảnh cáo học vụ thì bị phạt 5000000 VNĐ đúng không?"
    g2_res = pipeline.answer(g2_query)
    print(f"  ├─ Query           : \"{g2_query}\"")
    print(f"  ├─ Route           : {g2_res['route'].upper()}")
    print(f"  ├─ Answer          : {g2_res['answer'][:90]}...")
    print(f"  ├─ Hallucination?  : {g2_res.get('possible_hallucination')} (True = phát hiện số liệu ngoài context)")
    print(f"  └─ Ungrounded nums : {g2_res.get('ungrounded_numbers')}")

    print("\n" + "=" * 80)
    print("HOÀN TẤT TOÀN BỘ KIỂM THỬ TUẦN 6!")
    print("=" * 80)


if __name__ == "__main__":
    run_regression_tests()
