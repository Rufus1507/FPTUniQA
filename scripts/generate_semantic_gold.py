"""Sinh nhãn vàng Semantic Parsing (Intent & Slots) cho toàn bộ 500 câu hỏi Benchmark v2.
File đích: data/evaluation/benchmark_v2/semantic_gold.json
"""

import glob
import json
import os
import re
from typing import Any, Dict


def extract_gold_slots(query: str, category: str, answer_contains: list) -> Dict[str, Any]:
    slots: Dict[str, Any] = {}
    q_low = query.lower()

    # 1. Cohort
    m_cohort = re.search(r"\b(k1[5-9]|k2[0-5])\b", query, re.IGNORECASE)
    if m_cohort:
        slots["cohort"] = m_cohort.group(1).upper()

    # 2. Campus
    if any(c in q_low for c in ["hà nội", "ha noi", "hòa lạc", "hoa lac", "hn"]):
        slots["campus"] = "Hà Nội"
    elif any(c in q_low for c in ["tp.hcm", "hồ chí minh", "hcm", "sài gòn", "quận 9"]):
        slots["campus"] = "TP. Hồ Chí Minh"
    elif any(c in q_low for c in ["đà nẵng", "da nang", "đn"]):
        slots["campus"] = "Đà Nẵng"
    elif any(c in q_low for c in ["cần thơ", "can tho", "ct"]):
        slots["campus"] = "Cần Thơ"
    elif any(c in q_low for c in ["quy nhơn", "quy nhon", "qn"]):
        slots["campus"] = "Quy Nhơn"

    # 3. Course Code (từ regex chuẩn mã môn học FPT)
    m_course = re.search(r"\b([A-Z]{2,4}[0-9]{3}[a-zA-Z]?)\b", query)
    if m_course:
        code_cand = m_course.group(1).upper()
        # Loại trừ cohort dạng K20, K21
        if not re.match(r"^K[0-9]{2}$", code_cand):
            slots["course_code"] = code_cand

    # 4. Program
    programs_map = {
        "kỹ thuật phần mềm": "Kỹ thuật phần mềm",
        "phần mềm": "Kỹ thuật phần mềm",
        "software engineering": "Kỹ thuật phần mềm",
        "se": "Kỹ thuật phần mềm",
        "trí tuệ nhân tạo": "Trí tuệ nhân tạo",
        "ai": "Trí tuệ nhân tạo",
        "an toàn thông tin": "An toàn thông tin",
        "information assurance": "An toàn thông tin",
        "ia": "An toàn thông tin",
        "thiết kế mỹ thuật số": "Thiết kế mỹ thuật số",
        "thiết kế đồ họa": "Thiết kế mỹ thuật số",
        "graphic design": "Thiết kế mỹ thuật số",
        "gd": "Thiết kế mỹ thuật số",
        "quản trị kinh doanh": "Quản trị kinh doanh",
        "business administration": "Quản trị kinh doanh",
        "ba": "Quản trị kinh doanh",
        "kinh doanh quốc tế": "Kinh doanh quốc tế",
        "international business": "Kinh doanh quốc tế",
        "ib": "Kinh doanh quốc tế",
        "công nghệ thông tin": "Công nghệ thông tin",
        "cntt": "Công nghệ thông tin",
        "it": "Công nghệ thông tin",
    }
    for kw, prog_name in programs_map.items():
        if re.search(r"\b" + re.escape(kw) + r"\b", q_low):
            slots["program"] = prog_name
            break

    # 5. Course Aspect
    if any(k in q_low for k in ["tiên quyết", "prerequisite", "điều kiện"]):
        slots["course_aspect"] = "prerequisite"
    elif any(k in q_low for k in ["tín chỉ", "credits", "credit"]):
        slots["course_aspect"] = "credits"
    elif any(k in q_low for k in ["giáo trình", "sách", "textbook", "tài liệu"]):
        slots["course_aspect"] = "textbook"
    elif any(k in q_low for k in ["mục tiêu", "chuẩn đầu ra", "clo", "nội dung"]):
        slots["course_aspect"] = "objective"
    elif any(k in q_low for k in ["đánh giá", "pe", "fe", "lab", "thi", "chấm điểm"]):
        slots["course_aspect"] = "assessment"

    return slots


def generate_semantic_gold(output_path: str = "data/evaluation/benchmark_v2/semantic_gold.json") -> Dict[str, Any]:
    gold_data: Dict[str, Any] = {}

    for f in sorted(glob.glob("data/evaluation/benchmark_v2/batch_*.jsonl")):
        with open(f, "r", encoding="utf-8") as fp:
            for line in fp:
                item = json.loads(line)
                q_id = item["q_id"]
                query = item["query"]
                cat = item.get("category", "")
                exp_route = item.get("expected_route", "")
                contains = item.get("expected_answer_contains", [])

                slots = extract_gold_slots(query, cat, contains)

                # Xác định Intent vàng
                if exp_route == "ood":
                    intent = "OOD"
                elif "course" in cat or slots.get("course_code") or "môn" in query.lower():
                    intent = "course_lookup"
                elif "tuition" in cat or "phí" in query.lower() or "học phí" in query.lower() or "tiền" in query.lower():
                    intent = "tuition_lookup"
                elif "graduation" in cat or "ojt" in cat or "tốt nghiệp" in query.lower():
                    intent = "graduation_lookup"
                elif exp_route == "structured_lookup":
                    intent = "tuition_lookup" if ("phí" in query.lower()) else "course_lookup"
                else:
                    intent = "policy_lookup"

                gold_data[q_id] = {
                    "q_id": q_id,
                    "intent": intent,
                    "slots": slots,
                    "expected_route": exp_route,
                }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(gold_data, f, ensure_ascii=False, indent=2)

    print(f"Generated semantic gold for {len(gold_data)} entries at {output_path}")
    return gold_data


if __name__ == "__main__":
    generate_semantic_gold()
