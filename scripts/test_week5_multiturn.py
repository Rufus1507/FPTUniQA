"""Script kiểm thử hội thoại đa lượt Tuần 5: Query Rewriting, Session State và 7-field Structured Logging (TV3).

Kịch bản kiểm thử (4 kịch bản, mỗi kịch bản 2 lượt):
1. Kịch bản 1 (Milestone bắt buộc): Học phí ngành AI 2026 -> "Còn năm 2023 thì sao?"
2. Kịch bản 2 (Quy chế học vụ): Vắng bao nhiêu phần trăm bị cấm thi? -> "Nếu bị cấm thi thì có được thi lại không?"
3. Kịch bản 3 (Điều kiện tốt nghiệp): Điều kiện xét tốt nghiệp đại học? -> "Chuẩn tiếng Anh cụ thể là bao nhiêu?"
4. Kịch bản 4 (Làm rõ thiếu slot): Học phí ngành CNTT là bao nhiêu? -> "Khóa 2024 nhé"
"""

import json
import sys
from pathlib import Path

# Đảm bảo nạp đúng src/ và root vào sys.path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

from university_qa.pipeline.rag_pipeline import RAGPipeline

SCENARIOS = [
    {
        "name": "Kịch bản 1: Tra cứu học phí liên tiếp theo khóa (Milestone bắt buộc)",
        "session_id": "session_tuition_01",
        "turns": [
            "Học phí ngành AI khoá 2026 là bao nhiêu?",
            "Còn năm 2023 thì sao?",
        ],
    },
    {
        "name": "Kịch bản 2: Quy chế học vụ - Điểm danh và thi lại",
        "session_id": "session_policy_02",
        "turns": [
            "Sinh viên vắng bao nhiêu phần trăm số buổi thì bị cấm thi?",
            "Nếu bị cấm thi thì có được thi lại không?",
        ],
    },
    {
        "name": "Kịch bản 3: Điều kiện tốt nghiệp và chuẩn ngoại ngữ",
        "session_id": "session_grad_03",
        "turns": [
            "Điều kiện xét tốt nghiệp đại học như thế nào?",
            "Chuẩn tiếng Anh cụ thể là bao nhiêu?",
        ],
    },
    {
        "name": "Kịch bản 4: Hỏi làm rõ và bổ sung thông tin thiếu slot",
        "session_id": "session_clarify_04",
        "turns": [
            "Học phí ngành CNTT là bao nhiêu?",
            "Khóa 2024 nhé",
        ],
    },
]


def run_multiturn_tests():
    pipeline = RAGPipeline()
    print("=" * 80)
    print("BẮT ĐẦU KIỂM THỬ HỘI THOẠI ĐA LƯỢT TUẦN 5 (QUERY REWRITING & 7-FIELD LOGGING)")
    print("=" * 80)

    for s_idx, scenario in enumerate(SCENARIOS, start=1):
        session_id = scenario["session_id"]
        print(f"\n{'#' * 80}")
        print(f"[{s_idx}/4] {scenario['name']} (Session ID: {session_id})")
        print(f"{'#' * 80}")

        for t_idx, user_query in enumerate(scenario["turns"], start=1):
            print(f"\n--- LƯỢT {t_idx} ---")
            print(f"[*] Câu hỏi gốc (Original) : \"{user_query}\"")

            res = pipeline.answer(user_query, session_id=session_id)
            rewritten = res.get("rewritten_query", user_query)
            parsed = res.get("parsed_query", {})
            route = res.get("route", "unknown")
            answer = res.get("answer", "")
            citations = res.get("citations", [])

            print(f"[>] Câu hỏi viết lại (Rewritten) : \"{rewritten}\"")
            print(f"    ├─ Intent                    : {parsed.get('intent')} (confidence: {parsed.get('confidence')})")
            print(f"    ├─ Slots                     : {parsed.get('slots')}")
            print(f"    ├─ Route Chosen              : {route.upper()}")
            print(f"    ├─ Answer                    : {answer}")
            if citations:
                print(f"    └─ Citations ({len(citations)})          :")
                for c in citations:
                    print(f"        • [{c.get('doc_id')}] {c.get('title')} ({c.get('source')})")
            else:
                print(f"    └─ Citations                 : Không có")

    print("\n" + "=" * 80)
    print("HOÀN TẤT KIỂM THỬ TOÀN BỘ 4 KỊCH BẢN ĐA LƯỢT.")
    print("Đã ghi log đầy đủ 7 trường vào logs/pipeline_events.jsonl")
    print("=" * 80)


if __name__ == "__main__":
    run_multiturn_tests()
