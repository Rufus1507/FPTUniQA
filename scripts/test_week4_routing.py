"""Script kiểm thử toàn diện Tuần 4: Semantic Parsing, Router và Structured Lookup (TV3).

Kịch bản kiểm thử:
- 8 câu hỏi chuẩn (2 policy, 2 graduation, 2 tuition đầy đủ slot, 2 OOD)
- 2 câu hỏi cố tình thiếu slot (thiếu cohort, thiếu program) để kiểm tra nhánh clarification.
"""

import json
import sys
from pathlib import Path

# Đảm bảo import được các module trong src/ và root (contracts.py)
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

from university_qa.pipeline.rag_pipeline import RAGPipeline
from university_qa.query.semantic_parser import parse_query
from university_qa.query.router import route_query

TEST_QUERIES = [
    # --- 8 CÂU HỎI CHUẨN ---
    # 1-2: policy_lookup -> rag_pipeline
    "Điều kiện để không bị cảnh cáo học vụ là gì?",
    "Sinh viên vắng bao nhiêu phần trăm số buổi thì bị cấm thi?",
    # 3-4: graduation_lookup -> rag_pipeline
    "Điều kiện xét tốt nghiệp đại học như thế nào?",
    "Điều kiện làm đồ án tốt nghiệp Capstone là gì?",
    # 5-6: tuition_lookup đủ slot -> structured_lookup
    "Học phí ngành AI khoá 2026 là bao nhiêu?",
    "Học phí ngành CNTT khoá 2024 là bao nhiêu?",
    # 7-8: OOD -> ood
    "Hôm nay thời tiết Hà Nội thế nào?",
    "Điểm chuẩn ngành Công nghệ thông tin của Đại học Bách Khoa là bao nhiêu?",
    # --- 2 CÂU HỎI THIẾU SLOT (MẦM CHO MULTI-TURN TUẦN 5) ---
    # 9: tuition_lookup có program nhưng thiếu cohort -> clarification
    "Học phí ngành AI là bao nhiêu?",
    # 10: tuition_lookup có cohort nhưng thiếu program -> clarification
    "Học phí khóa 2026 là bao nhiêu?",
]


def run_tests():
    pipeline = RAGPipeline()
    print("=" * 80)
    print("BẮT ĐẦU KIỂM THỬ TUẦN 4: SEMANTIC PARSING & DYNAMIC ROUTING")
    print("=" * 80)

    for idx, q in enumerate(TEST_QUERIES, start=1):
        print(f"\n[{idx}/10] CÂU HỎI: \"{q}\"")
        res = pipeline.answer(q)
        parsed = res.get("parsed_query", {})
        route = res.get("route", "unknown")

        print(f"  ├─ Intent        : {parsed.get('intent')} (confidence: {parsed.get('confidence')})")
        print(f"  ├─ Slots         : {parsed.get('slots')}")
        print(f"  ├─ Parser Method : {parsed.get('parser_method')} (fallback_used: {parsed.get('fallback_used')})")
        print(f"  ├─ Route Chosen  : {route.upper()}")
        print(f"  ├─ Answer        : {res.get('answer')}")
        citations = res.get("citations", [])
        if citations:
            print(f"  └─ Citations ({len(citations)}):")
            for c in citations:
                print(f"      • [{c.get('doc_id')}] {c.get('title')} ({c.get('source')})")
        else:
            print(f"  └─ Citations     : Không có (phù hợp với route {route})")
        print("-" * 80)

    print("\nHOÀN TẤT KIỂM THỬ 10/10 CÂU HỎI.")
    print("File log sự kiện parsing: logs/parsing_events.jsonl")


if __name__ == "__main__":
    run_tests()
