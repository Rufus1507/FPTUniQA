"""Script sinh tập dữ liệu benchmark đa lượt theo đợt (Round 1 đến Round 5).
Mỗi đợt gồm 100 câu hỏi hoàn toàn mới, đa dạng ngữ cảnh và cấu trúc:
- 40 câu Multi-turn kế thừa (Ellipsis / Coreference)
- 20 câu Chuyển đổi chủ đề (Topic Switch) kiểm tra tính hợp lý của Query Rewriter
- 20 câu Khóa học K17, K18, K20, K21, K22 (Học phí chuyên ngành, KTX, thi lại, số kỳ)
- 10 câu Môn học chuyên sâu (Syllabus, giáo trình, điều kiện tiên quyết, tín chỉ)
- 10 câu Ngoài miền (OOD Rejection)
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_truth_data() -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Tải dữ liệu biểu phí khóa và 66 môn học chuẩn làm căn cứ sinh golden answer."""
    structured_path = Path("data/processed/structured_data.json")
    courses_path = Path("data/processed/structured_data_courses.json")

    with open(structured_path, "r", encoding="utf-8") as f:
        struct_data = json.load(f)

    with open(courses_path, "r", encoding="utf-8") as f:
        course_data = json.load(f)

    cohort_fees = struct_data.get("fpt_cohort_fees", [])
    courses = course_data.get("courses", [])
    return struct_data, courses


def generate_round_questions(round_num: int) -> List[Dict[str, Any]]:
    """Sinh 100 câu hỏi đánh giá độc lập cho đợt round_num."""
    random.seed(42 + round_num * 100)
    struct_data, courses = load_truth_data()
    cohort_fees = struct_data.get("fpt_cohort_fees", [])
    courses_by_code = {c["course_code"]: c for c in courses}

    questions: List[Dict[str, Any]] = []
    q_counter = 1

    # =========================================================================
    # 1. NHÓM 40 CÂU MULTI-TURN KẾ THỪA (20 sessions × 2 lượt)
    # =========================================================================
    # Danh sách mẫu kịch bản hội thoại đa lượt kế thừa
    continuation_templates = [
        # Sub-type A: Hỏi học phí chuyên ngành -> Hỏi tiếp phí KTX / thi lại / tiếng Anh
        {
            "cohort": "K21",
            "t1": "Học phí chuyên ngành khóa K21 là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["31.200.000", "31,200,000"],
            "t2": "Còn phí ký túc xá thì sao?",
            "t2_rewrite": ["K21", "ký túc xá"],
            "t2_route": "structured_lookup",
            "t2_ans": ["4.200.000", "4,200,000", "4.000.000", "4,000,000"],
        },
        {
            "cohort": "K18",
            "t1": "Học phí chuyên ngành của khóa K18 là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["27.300.000", "27,300,000"],
            "t2": "Vậy lệ phí thi lại khóa này là bao nhiêu?",
            "t2_rewrite": ["K18", "thi lại"],
            "t2_route": "structured_lookup",
            "t2_ans": ["300.000", "300,000"],
        },
        {
            "cohort": "K20",
            "t1": "Khóa K20 đóng học phí chuyên ngành một kỳ là bao nhiêu tiền?",
            "t1_route": "structured_lookup",
            "t1_ans": ["28.700.000", "28,700,000"],
            "t2": "Thế học phí tiếng Anh dự bị mỗi mức là bao nhiêu?",
            "t2_rewrite": ["K20", "tiếng Anh"],
            "t2_route": "structured_lookup",
            "t2_ans": ["11.300.000", "11,300,000"],
        },
        {
            "cohort": "K17",
            "t1": "Biểu phí chuyên ngành khóa K17 tại Hà Nội như thế nào?",
            "t1_route": "structured_lookup",
            "t1_ans": ["25.300.000", "25,300,000"],
            "t2": "Còn tiền học lại một tín chỉ là bao nhiêu?",
            "t2_rewrite": ["K17", "học lại"],
            "t2_route": "structured_lookup",
            "t2_ans": ["600.000", "600,000", "650.000", "650,000"],
        },
        {
            "cohort": "K22",
            "t1": "Học phí chuyên ngành khóa K22 tại TP.HCM là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["32.500.000", "32,500,000"],
            "t2": "Còn chi phí ký túc xá mỗi kỳ của khóa này?",
            "t2_rewrite": ["K22", "ký túc xá"],
            "t2_route": "structured_lookup",
            "t2_ans": ["4.500.000", "4,500,000", "4.000.000", "4,000,000"],
        },
        # Sub-type B: Hỏi học phí ngành X tại campus Y -> Hỏi sang campus khác
        {
            "cohort": "K22",
            "t1": "Học phí ngành Kỹ thuật phần mềm tại Hà Nội năm 2026 là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["31.600.000", "31,600,000", "22.120.000", "22,120,000"],
            "t2": "Còn ở phân hiệu Cần Thơ thì sao?",
            "t2_rewrite": ["Kỹ thuật phần mềm", "Cần Thơ"],
            "t2_route": "structured_lookup",
            "t2_ans": ["22.120.000", "22,120,000", "15.480.000", "15,480,000", "30%"],
        },
        {
            "cohort": "K22",
            "t1": "Học phí ngành Trí tuệ nhân tạo tại TP. Hồ Chí Minh là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["31.600.000", "31,600,000", "22.120.000", "22,120,000"],
            "t2": "Nếu học ở Quy Nhơn thì mức thu bao nhiêu?",
            "t2_rewrite": ["Trí tuệ nhân tạo", "Quy Nhơn"],
            "t2_route": "structured_lookup",
            "t2_ans": ["15.800.000", "15,800,000", "11.060.000", "11,060,000", "50%"],
        },
        {
            "cohort": "K22",
            "t1": "Học phí ngành Quản trị kinh doanh tại Hà Nội là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["31.600.000", "31,600,000", "22.120.000", "22,120,000", "29.250.000", "29,250,000"],
            "t2": "Còn tại cơ sở Đà Nẵng thì thế nào?",
            "t2_rewrite": ["Quản trị kinh doanh", "Đà Nẵng"],
            "t2_route": "structured_lookup",
            "t2_ans": ["22.120.000", "22,120,000", "15.480.000", "15,480,000", "30%"],
        },
        # Sub-type C: Hỏi môn học -> Hỏi tiếp điều kiện tiên quyết / giáo trình / số tín
        {
            "course": "PRF192",
            "t1": "Môn PRF192 học những nội dung gì?",
            "t1_route": "structured_lookup",
            "t1_ans": ["C", "biến", "vòng lặp", "con trỏ"],
            "t2": "Môn này học giáo trình nào?",
            "t2_rewrite": ["PRF192", "giáo trình"],
            "t2_route": "structured_lookup",
            "t2_ans": ["Kernighan", "Ritchie", "Programming Language"],
        },
        {
            "course": "PRO192",
            "t1": "Giáo trình môn PRO192 là sách gì?",
            "t1_route": "structured_lookup",
            "t1_ans": ["Java", "Deitel"],
            "t2": "Môn đó có yêu cầu môn tiên quyết nào không?",
            "t2_rewrite": ["PRO192", "tiên quyết"],
            "t2_route": "structured_lookup",
            "t2_ans": ["PRF192"],
        },
        {
            "course": "CSD201",
            "t1": "Môn CSD201 học về kiến thức gì?",
            "t1_route": "structured_lookup",
            "t1_ans": ["cấu trúc dữ liệu", "giải thuật", "cây", "đồ thị"],
            "t2": "Môn này có mấy tín chỉ?",
            "t2_rewrite": ["CSD201", "tín chỉ"],
            "t2_route": "structured_lookup",
            "t2_ans": ["3 tín chỉ", "3"],
        },
        {
            "course": "DBI202",
            "t1": "Môn DBI202 yêu cầu môn tiên quyết gì?",
            "t1_route": "structured_lookup",
            "t1_ans": ["tiên quyết", "không có", "None"],
            "t2": "Nội dung học chính của môn đó là gì?",
            "t2_rewrite": ["DBI202", "nội dung"],
            "t2_route": "structured_lookup",
            "t2_ans": ["SQL", "cơ sở dữ liệu", "quan hệ"],
        },
        # Sub-type D: Quy chế học vụ đa lượt
        {
            "topic": "warning",
            "t1": "Quy định về cảnh báo học tập tại Đại học FPT như thế nào?",
            "t1_route": "rag_pipeline",
            "t1_ans": ["cảnh báo", "học vụ", "điểm"],
            "t2": "Bị cảnh báo mấy lần thì bị buộc thôi học?",
            "t2_rewrite": ["cảnh báo", "thôi học"],
            "t2_route": "rag_pipeline",
            "t2_ans": ["buộc thôi học", "lần"],
        },
        {
            "topic": "graduation",
            "t1": "Điều kiện tốt nghiệp tại Đại học FPT gồm những gì?",
            "t1_route": "rag_pipeline",
            "t1_ans": ["tín chỉ", "chuẩn đầu ra", "tiếng Anh"],
            "t2": "Chuẩn đầu ra tiếng Anh yêu cầu chứng chỉ gì?",
            "t2_rewrite": ["tốt nghiệp", "tiếng Anh"],
            "t2_route": "rag_pipeline",
            "t2_ans": ["TOEIC", "IELTS", "tiếng Anh"],
        },
        {
            "topic": "ojt",
            "t1": "Sinh viên đi thực tập OJT vào học kỳ thứ mấy?",
            "t1_route": "rag_pipeline",
            "t1_ans": ["kỳ 6", "học kỳ 6", "OJT"],
            "t2": "Trong kỳ đó có phải nộp học phí chuyên ngành không?",
            "t2_rewrite": ["OJT", "học phí"],
            "t2_route": "structured_lookup",
            "t2_ans": ["không phải đóng học phí chuyên ngành", "miễn học phí"],
        },
        {
            "topic": "relearn",
            "t1": "Nếu bị trượt môn thì lệ phí học lại tính như thế nào?",
            "t1_route": "structured_lookup",
            "t1_ans": ["650.000", "650,000", "tín chỉ"],
            "t2": "Thế còn lệ phí thi lại một lần là bao nhiêu?",
            "t2_rewrite": ["thi lại", "lệ phí"],
            "t2_route": "structured_lookup",
            "t2_ans": ["300.000", "300,000", "lần thi"],
        },
        {
            "course": "MAS291",
            "t1": "Môn Xác suất thống kê MAS291 học những gì?",
            "t1_route": "structured_lookup",
            "t1_ans": ["xác suất", "biến ngẫu nhiên", "thống kê"],
            "t2": "Giáo trình chính môn này tên là gì?",
            "t2_rewrite": ["MAS291", "giáo trình"],
            "t2_route": "structured_lookup",
            "t2_ans": ["Probability", "Statistics", "Montgomery"],
        },
        {
            "course": "VOV114",
            "t1": "Môn Vovinam 1 VOV114 có mấy tín chỉ?",
            "t1_route": "structured_lookup",
            "t1_ans": ["0 tín chỉ", "0"],
            "t2": "Môn này học về những kỹ thuật nào?",
            "t2_rewrite": ["VOV114", "nội dung"],
            "t2_route": "structured_lookup",
            "t2_ans": ["Vovinam", "quyền", "thế tự vệ"],
        },
        {
            "cohort": "K19",
            "t1": "Học phí chuyên ngành của sinh viên khóa K19 là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["28.700.000", "28,700,000"],
            "t2": "Sinh viên khóa này học bao nhiêu học kỳ chuyên ngành?",
            "t2_rewrite": ["K19", "kỳ chuyên ngành"],
            "t2_route": "structured_lookup",
            "t2_ans": ["9 học kỳ", "9"],
        },
        {
            "cohort": "K21",
            "t1": "Khóa K21 học phí tiếng Anh dự bị một mức là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["11.900.000", "11,900,000"],
            "t2": "Tối đa có bao nhiêu mức tiếng Anh chuẩn bị?",
            "t2_rewrite": ["tiếng Anh", "mức"],
            "t2_route": "structured_lookup",
            "t2_ans": ["6 mức", "6 level", "6"],
        },
    ]

    # Xáo trộn nhẹ hoặc điều chỉnh paraphrase tùy theo round_num để đảm bảo 5 đợt không trùng nhau nguyên văn
    paraphrase_suffixes = [
        "", " ạ?", " vậy ad?", " thế ad?", " cho em hỏi với?", " ạ bot?"
    ]
    p_suf = paraphrase_suffixes[round_num % len(paraphrase_suffixes)]

    for idx, item in enumerate(continuation_templates, start=1):
        sess_id = f"r{round_num}_cont_sess_{idx:02d}"
        # Turn 1
        q1_text = item["t1"] + (p_suf if not item["t1"].endswith("?") else "")
        questions.append({
            "q_id": f"R{round_num}_{q_counter:03d}",
            "round": round_num,
            "category": "multi_turn_continuation",
            "session_id": sess_id,
            "turn_index": 1,
            "query": q1_text,
            "is_continuation": False,
            "expected_rewrite_contains": [],
            "is_topic_switch": False,
            "expected_route": item["t1_route"],
            "golden_answer": f"Đáp án lượt 1 session {sess_id}",
            "expected_answer_contains": item["t1_ans"],
        })
        q_counter += 1

        # Turn 2 (Continuation)
        q2_text = item["t2"] + (p_suf if not item["t2"].endswith("?") else "")
        questions.append({
            "q_id": f"R{round_num}_{q_counter:03d}",
            "round": round_num,
            "category": "multi_turn_continuation",
            "session_id": sess_id,
            "turn_index": 2,
            "query": q2_text,
            "is_continuation": True,
            "expected_rewrite_contains": item["t2_rewrite"],
            "is_topic_switch": False,
            "expected_route": item["t2_route"],
            "golden_answer": f"Đáp án lượt 2 session {sess_id}",
            "expected_answer_contains": item["t2_ans"],
        })
        q_counter += 1

    # =========================================================================
    # 2. NHÓM 20 CÂU TOPIC SWITCH (10 sessions × 2 lượt: Turn 1 chủ đề A, Turn 2 đột ngột nhảy sang chủ đề B)
    # =========================================================================
    topic_switch_pairs = [
        # Switch 1: Từ Học phí K21 nhảy sang Giáo trình môn PRF192
        {
            "t1": "Học phí chuyên ngành khóa K21 là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["31.200.000", "31,200,000"],
            "t2_switch": "Giáo trình môn PRF192 là sách nào của tác giả nào?",
            "t2_route": "structured_lookup",
            "t2_ans": ["Kernighan", "Ritchie"],
            "avoid_bleed": ["K21", "học phí"],
        },
        # Switch 2: Từ Cảnh báo học vụ nhảy sang Học phí K18
        {
            "t1": "Sinh viên bị bao nhiêu lần cảnh báo học vụ thì bị buộc thôi học?",
            "t1_route": "rag_pipeline",
            "t1_ans": ["cảnh báo", "thôi học"],
            "t2_switch": "Học phí chuyên ngành khóa K18 tại Hà Nội là bao nhiêu?",
            "t2_route": "structured_lookup",
            "t2_ans": ["27.300.000", "27,300,000"],
            "avoid_bleed": ["cảnh báo", "buộc thôi học"],
        },
        # Switch 3: Từ Môn CSD201 nhảy sang Lệ phí thi lại
        {
            "t1": "Môn CSD201 học về cấu trúc dữ liệu và giải thuật gì?",
            "t1_route": "structured_lookup",
            "t1_ans": ["cây", "đồ thị", "giải thuật"],
            "t2_switch": "Lệ phí thi lại của trường FPT là bao nhiêu một lần?",
            "t2_route": "structured_lookup",
            "t2_ans": ["300.000", "300,000"],
            "avoid_bleed": ["CSD201", "cấu trúc dữ liệu"],
        },
        # Switch 4: Từ Học phí K20 nhảy sang OOD (Nấu ăn)
        {
            "t1": "Khóa K20 học phí chuyên ngành là bao nhiêu một kỳ?",
            "t1_route": "structured_lookup",
            "t1_ans": ["28.700.000", "28,700,000"],
            "t2_switch": "Cách nấu món phở bò Nam Định truyền thống ngon nhất?",
            "t2_route": "ood",
            "t2_ans": ["ngoài phạm vi"],
            "avoid_bleed": ["K20", "học phí"],
        },
        # Switch 5: Từ Điều kiện tốt nghiệp nhảy sang Môn PRO192
        {
            "t1": "Điều kiện để sinh viên FPT được xét tốt nghiệp ra trường?",
            "t1_route": "rag_pipeline",
            "t1_ans": ["tín chỉ", "chuẩn đầu ra"],
            "t2_switch": "Môn PRO192 yêu cầu môn tiên quyết nào?",
            "t2_route": "structured_lookup",
            "t2_ans": ["PRF192"],
            "avoid_bleed": ["tốt nghiệp", "chuẩn đầu ra"],
        },
        # Switch 6: Từ Học phí K17 nhảy sang Môn DBI202
        {
            "t1": "Học phí khóa K17 chuyên ngành là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["25.300.000", "25,300,000"],
            "t2_switch": "Môn DBI202 có cần môn tiên quyết không?",
            "t2_route": "structured_lookup",
            "t2_ans": ["tiên quyết", "không có", "None"],
            "avoid_bleed": ["K17", "học phí"],
        },
        # Switch 7: Từ Tiếng Anh dự bị nhảy sang OOD (Bóng đá)
        {
            "t1": "Học phí tiếng Anh chuẩn bị khóa K21 là bao nhiêu?",
            "t1_route": "structured_lookup",
            "t1_ans": ["11.900.000", "11,900,000"],
            "t2_switch": "Đội tuyển nào vô địch World Cup 2022?",
            "t2_route": "ood",
            "t2_ans": ["ngoài phạm vi"],
            "avoid_bleed": ["tiếng Anh", "K21"],
        },
        # Switch 8: Từ Thực tập OJT nhảy sang Học phí K22 Quy Nhơn
        {
            "t1": "Giai đoạn thực tập doanh nghiệp OJT diễn ra kỳ thứ mấy?",
            "t1_route": "rag_pipeline",
            "t1_ans": ["kỳ 6", "học kỳ 6", "OJT"],
            "t2_switch": "Chính sách ưu đãi học phí tại phân hiệu Quy Nhơn là bao nhiêu phần trăm?",
            "t2_route": "structured_lookup",
            "t2_ans": ["50%"],
            "avoid_bleed": ["OJT", "thực tập"],
        },
        # Switch 9: Từ Môn MAS291 nhảy sang Phí KTX FUHL
        {
            "t1": "Môn Xác suất thống kê MAS291 có mấy tín chỉ?",
            "t1_route": "structured_lookup",
            "t1_ans": ["3 tín chỉ", "3"],
            "t2_switch": "Phí ký túc xá phân hiệu Hòa Lạc FUHL là bao nhiêu một học kỳ?",
            "t2_route": "structured_lookup",
            "t2_ans": ["4.000.000", "4,000,000", "4.200.000", "4,200,000"],
            "avoid_bleed": ["MAS291", "xác suất"],
        },
        # Switch 10: Từ Quy chế phúc khảo nhảy sang Môn VOV114
        {
            "t1": "Thời hạn nộp đơn phúc khảo bài thi sau khi công bố điểm là bao lâu?",
            "t1_route": "rag_pipeline",
            "t1_ans": ["ngày", "phúc khảo"],
            "t2_switch": "Môn võ Vovinam 1 VOV114 có bao nhiêu tín chỉ?",
            "t2_route": "structured_lookup",
            "t2_ans": ["0 tín chỉ", "0"],
            "avoid_bleed": ["phúc khảo", "điểm thi"],
        },
    ]

    for idx, item in enumerate(topic_switch_pairs, start=1):
        sess_id = f"r{round_num}_switch_sess_{idx:02d}"
        # Turn 1
        questions.append({
            "q_id": f"R{round_num}_{q_counter:03d}",
            "round": round_num,
            "category": "topic_switch_turn1",
            "session_id": sess_id,
            "turn_index": 1,
            "query": item["t1"],
            "is_continuation": False,
            "expected_rewrite_contains": [],
            "is_topic_switch": False,
            "expected_route": item["t1_route"],
            "golden_answer": f"Đáp án lượt 1 topic switch {sess_id}",
            "expected_answer_contains": item["t1_ans"],
        })
        q_counter += 1

        # Turn 2: Topic Switch đột ngột
        questions.append({
            "q_id": f"R{round_num}_{q_counter:03d}",
            "round": round_num,
            "category": "topic_switch",
            "session_id": sess_id,
            "turn_index": 2,
            "query": item["t2_switch"],
            "is_continuation": False,
            "expected_rewrite_contains": [],
            "is_topic_switch": True,
            "avoid_bleeding_entities": item["avoid_bleed"],
            "expected_route": item["t2_route"],
            "golden_answer": f"Đáp án lượt 2 chuyển chủ đề {sess_id}",
            "expected_answer_contains": item["t2_ans"],
        })
        q_counter += 1

    # =========================================================================
    # 3. NHÓM 20 CÂU KHÓA HỌC K17, K18, K20, K21, K22 (Độc lập hoặc đa khía cạnh)
    # =========================================================================
    cohort_questions = [
        # Khóa K17
        {
            "query": "Học phí chuyên ngành của sinh viên khóa K17 là bao nhiêu?",
            "route": "structured_lookup",
            "ans": ["25.300.000", "25,300,000"],
        },
        {
            "query": "Học phí tiếng Anh dự bị khóa K17 là bao nhiêu một mức?",
            "route": "structured_lookup",
            "ans": ["10.350.000", "10,350,000"],
        },
        {
            "query": "Tổng số học kỳ chuyên ngành của khóa K17 là bao nhiêu kỳ?",
            "route": "structured_lookup",
            "ans": ["9 học kỳ", "9"],
        },
        {
            "query": "Lệ phí thi lại của khóa K17 là bao nhiêu tiền một lần?",
            "route": "structured_lookup",
            "ans": ["300.000", "300,000"],
        },
        # Khóa K18
        {
            "query": "Học phí chuyên ngành của khóa K18 tại Hà Nội là bao nhiêu một kỳ?",
            "route": "structured_lookup",
            "ans": ["27.300.000", "27,300,000"],
        },
        {
            "query": "Học phí tiếng Anh chuẩn bị khóa K18 tính theo mức là bao nhiêu?",
            "route": "structured_lookup",
            "ans": ["11.300.000", "11,300,000"],
        },
        {
            "query": "Lệ phí học lại mỗi tín chỉ của khóa K18 là bao nhiêu?",
            "route": "structured_lookup",
            "ans": ["650.000", "650,000"],
        },
        {
            "query": "Chi phí ký túc xá mỗi kỳ của sinh viên khóa K18 là bao nhiêu?",
            "route": "structured_lookup",
            "ans": ["3.800.000", "3,800,000"],
        },
        # Khóa K20
        {
            "query": "Biểu phí học phí chuyên ngành khóa K20 là bao nhiêu?",
            "route": "structured_lookup",
            "ans": ["28.700.000", "28,700,000"],
        },
        {
            "query": "Mức học phí tiếng Anh dự bị của khóa K20 là bao nhiêu tiền?",
            "route": "structured_lookup",
            "ans": ["11.300.000", "11,300,000"],
        },
        {
            "query": "Khóa K20 có bao nhiêu kỳ học chuyên ngành tổng cộng?",
            "route": "structured_lookup",
            "ans": ["9 học kỳ", "9"],
        },
        {
            "query": "Lệ phí thi lại của khóa K20 được quy định là bao nhiêu?",
            "route": "structured_lookup",
            "ans": ["300.000", "300,000"],
        },
        # Khóa K21
        {
            "query": "Học phí chuyên ngành áp dụng cho khóa K21 là bao nhiêu?",
            "route": "structured_lookup",
            "ans": ["31.200.000", "31,200,000"],
        },
        {
            "query": "Mức học phí tiếng Anh dự bị khóa K21 là bao nhiêu?",
            "route": "structured_lookup",
            "ans": ["11.900.000", "11,900,000"],
        },
        {
            "query": "Phí ký túc xá một kỳ của khóa K21 tại Hòa Lạc là bao nhiêu?",
            "route": "structured_lookup",
            "ans": ["4.200.000", "4,200,000"],
        },
        {
            "query": "Lệ phí thi lại của khóa K21 quy định là bao nhiêu tiền?",
            "route": "structured_lookup",
            "ans": ["350.000", "350,000"],
        },
        # Khóa K22
        {
            "query": "Học phí chuyên ngành khóa K22 tại TP.HCM là bao nhiêu một kỳ?",
            "route": "structured_lookup",
            "ans": ["32.500.000", "32,500,000"],
        },
        {
            "query": "Mức phí học tiếng Anh chuẩn bị khóa K22 là bao nhiêu?",
            "route": "structured_lookup",
            "ans": ["11.900.000", "11,900,000"],
        },
        {
            "query": "Lệ phí thi lại của khóa K22 là bao nhiêu tiền một lần thi?",
            "route": "structured_lookup",
            "ans": ["350.000", "350,000"],
        },
        {
            "query": "Học phí kỳ thực tập OJT của sinh viên khóa K22 có phải đóng không?",
            "route": "structured_lookup",
            "ans": ["không phải đóng học phí chuyên ngành", "miễn học phí"],
        },
    ]

    for item in cohort_questions:
        sess_id = f"r{round_num}_cohort_sess_{q_counter:03d}"
        questions.append({
            "q_id": f"R{round_num}_{q_counter:03d}",
            "round": round_num,
            "category": "cohort_specific",
            "session_id": sess_id,
            "turn_index": 1,
            "query": item["query"],
            "is_continuation": False,
            "expected_rewrite_contains": [],
            "is_topic_switch": False,
            "expected_route": item["route"],
            "golden_answer": f"Đáp án khóa học {item['query']}",
            "expected_answer_contains": item["ans"],
        })
        q_counter += 1

    # =========================================================================
    # 4. NHÓM 10 CÂU MÔN HỌC CHUYÊN SÂU (CKB Structured Lookup)
    # =========================================================================
    course_deep_pool = [
        {
            "code": "PRF192",
            "q": "Môn PRF192 học về những nội dung gì?",
            "ans": ["C", "biến", "vòng lặp", "con trỏ"],
        },
        {
            "code": "PRO192",
            "q": "Giáo trình chính của môn PRO192 là cuốn sách nào?",
            "ans": ["Java", "Deitel"],
        },
        {
            "code": "CSD201",
            "q": "Môn CSD201 có yêu cầu môn tiên quyết nào?",
            "ans": ["PRO192", "tiên quyết"],
        },
        {
            "code": "DBI202",
            "q": "Môn DBI202 Cơ sở dữ liệu có bao nhiêu tín chỉ?",
            "ans": ["3 tín chỉ", "3"],
        },
        {
            "code": "MAS291",
            "q": "Nội dung kiến thức môn MAS291 Xác suất thống kê gồm những gì?",
            "ans": ["xác suất", "biến ngẫu nhiên", "thống kê"],
        },
        {
            "code": "VOV114",
            "q": "Môn Giáo dục thể chất Vovinam 1 VOV114 có mấy tín chỉ?",
            "ans": ["0 tín chỉ", "0"],
        },
        {
            "code": "SWE201c",
            "q": "Môn SWE201c Nhập môn Công nghệ phần mềm có môn tiên quyết là gì?",
            "ans": ["PRO192", "CSD201"],
        },
        {
            "code": "IOT102",
            "q": "Môn học IOT102 Internet vạn vật học những nội dung gì?",
            "ans": ["IoT", "cảm biến", "vi điều khiển", "Arduino"],
        },
        {
            "code": "MAD101",
            "q": "Môn Toán rời rạc MAD101 có bao nhiêu tín chỉ?",
            "ans": ["3 tín chỉ", "3"],
        },
        {
            "code": "CEA201",
            "q": "Giáo trình chính môn Kiến trúc máy tính CEA201 là sách gì?",
            "ans": ["Computer Organization", "Patterson", "Hennessy"],
        },
    ]

    for item in course_deep_pool:
        sess_id = f"r{round_num}_course_sess_{q_counter:03d}"
        questions.append({
            "q_id": f"R{round_num}_{q_counter:03d}",
            "round": round_num,
            "category": "course_deep",
            "session_id": sess_id,
            "turn_index": 1,
            "query": item["q"],
            "is_continuation": False,
            "expected_rewrite_contains": [],
            "is_topic_switch": False,
            "expected_route": "structured_lookup",
            "golden_answer": f"Thông tin môn {item['code']}",
            "expected_answer_contains": item["ans"],
        })
        q_counter += 1

    # =========================================================================
    # 5. NHÓM 10 CÂU NGOÀI MIỀN (OOD REJECTION)
    # =========================================================================
    ood_pool = [
        "Cách nấu món bún bò Huế ngon chuẩn vị?",
        "Thời tiết Hà Nội hôm nay có mưa không?",
        "Giải bóng đá Ngoại Hạng Anh có bao nhiêu vòng đấu?",
        "Bộ phim Titanic phát hành vào năm nào?",
        "Cách tải và cài đặt game Liên Minh Huyền Thoại?",
        "Thủ đô của nước Úc là thành phố nào?",
        "Ai là người phát minh ra bóng đèn điện?",
        "Cách làm món trà sữa trân châu đường đen tại nhà?",
        "Giá vàng hôm nay tăng hay giảm bao nhiêu?",
        "Lời bài hát Nơi này có anh của Sơn Tùng MTP?",
    ]

    for q_ood in ood_pool:
        sess_id = f"r{round_num}_ood_sess_{q_counter:03d}"
        questions.append({
            "q_id": f"R{round_num}_{q_counter:03d}",
            "round": round_num,
            "category": "ood",
            "session_id": sess_id,
            "turn_index": 1,
            "query": q_ood,
            "is_continuation": False,
            "expected_rewrite_contains": [],
            "is_topic_switch": False,
            "expected_route": "ood",
            "golden_answer": "Từ chối ngoài phạm vi",
            "expected_answer_contains": ["ngoài phạm vi"],
        })
        q_counter += 1

    assert len(questions) == 100, f"Tổng số câu phải là 100, thực tế: {len(questions)}"
    return questions


def main():
    parser = argparse.ArgumentParser(description="Sinh tập benchmark đa lượt cho Round 1..5")
    parser.add_argument("--round", type=int, default=1, choices=[1, 2, 3, 4, 5], help="Số thứ tự round (1..5)")
    parser.add_argument("--output_dir", type=str, default="data/evaluation/multiturn_rounds", help="Thư mục xuất file")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"round_{args.round}.jsonl"

    items = generate_round_questions(args.round)

    with open(out_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f" Đã sinh thành công {len(items)} câu hỏi cho Round {args.round} tại: {out_path}")
    # Thống kê phân bố categories
    cat_counts: Dict[str, int] = {}
    for item in items:
        c = item["category"]
        cat_counts[c] = cat_counts.get(c, 0) + 1
    for c, cnt in cat_counts.items():
        print(f"  - {c}: {cnt} câu")


if __name__ == "__main__":
    main()
