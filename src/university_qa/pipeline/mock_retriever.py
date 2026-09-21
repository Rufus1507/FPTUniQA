"""Mock Retriever giả lập cho Tuần 1 tuân thủ đúng Retrieval Contract. Phụ trách: TV3.

Được đặt trong package pipeline để phục vụ kiểm thử End-to-End TV3 trong khi chờ TV2 bàn giao tầng retrieval chính thức.
"""

from typing import Any, Dict, List, Optional


# Kho dữ liệu giả lập quy chế thực tế của Đại học FPT
MOCK_FPTU_KNOWLEDGE_BASE: List[Dict] = [
    {
        "doc_id": "FPTU-QC-001",
        "title": "Quy chế cảnh báo học vụ và đình chỉ học tập",
        "category": "quy_che",
        "content": (
            "Sinh viên bị cảnh cáo học vụ nếu thuộc một trong các trường hợp: "
            "(1) Điểm trung bình học kỳ (GPA) dưới 1.0 đối với học kỳ đầu tiên, hoặc dưới 1.2 đối với các học kỳ tiếp theo; "
            "(2) Điểm trung bình tích lũy (CGPA) dưới 1.2 đối với năm nhất, dưới 1.4 đối với năm hai, dưới 1.6 đối với năm ba trở đi. "
            "Sinh viên bị cảnh cáo học vụ 3 lần liên tiếp sẽ bị buộc thôi học."
        ),
        "source": "Sổ tay sinh viên ĐH FPT 2024 - Mục 4.2: Cảnh báo học tập, Trang 22",
        "base_score": 0.95,
        "keywords": ["cảnh báo", "cảnh cáo", "thôi học", "buộc thôi học", "kỷ luật", "gpa", "cgpa"],
    },
    {
        "doc_id": "FPTU-QC-002",
        "title": "Điều kiện xét công nhận tốt nghiệp đại học",
        "category": "quy_che",
        "content": (
            "Điều kiện công nhận tốt nghiệp hệ đại học chính quy tại ĐH FPT bao gồm: "
            "(1) Tích lũy đủ số tín chỉ và hoàn thành tất cả học phần trong khung chương trình đào tạo; "
            "(2) Điểm trung bình tích lũy toàn khóa (CGPA) đạt từ 2.00 trở lên theo thang điểm 4; "
            "(3) Đạt chuẩn đầu ra tiếng Anh mức 4 theo Khung năng lực ngoại ngữ 6 bậc (tương đương IELTS 5.5 hoặc TOEIC 550); "
            "(4) Hoàn thành học phần Giáo dục Quốc phòng - An ninh, Giáo dục Thể chất và kỳ thực tập doanh nghiệp (OJT); "
            "(5) Không trong thời gian bị kỷ luật từ mức đình chỉ học tập trở lên."
        ),
        "source": "Quy chế Đào tạo ĐH FPT 2024 - Điều 28: Tốt nghiệp, Trang 45",
        "base_score": 0.92,
        "keywords": ["tốt nghiệp", "điều kiện tốt nghiệp", "chuẩn đầu ra", "bằng tốt nghiệp", "ra trường"],
    },
    {
        "doc_id": "FPTU-HP-003",
        "title": "Chính sách học phí và thời hạn nộp học phí",
        "category": "hoc_phi_hoc_bong",
        "content": (
            "Học phí tại ĐH FPT được thu theo từng học kỳ chuyên ngành hoặc học kỳ tiếng Anh dự bị. "
            "Mỗi học kỳ chính gồm 4 tháng. Học phí chuyên ngành tiêu chuẩn là 28.700.000 VNĐ/học kỳ (áp dụng cơ sở Hà Nội/TP.HCM). "
            "Sinh viên phải hoàn tất học phí trước ngày học đầu tiên của kỳ ít nhất 7 ngày qua cổng FAP hoặc ngân hàng liên kết. "
            "Sinh viên đóng học phí muộn sẽ bị hủy lịch đăng ký học phần của kỳ đó."
        ),
        "source": "Quy định Thu chi tài chính ĐH FPT - Quyết định 104/QĐ-ĐHFPT 2024",
        "base_score": 0.90,
        "keywords": ["học phí", "tiền học", "đóng tiền", "hạn nộp học phí", "chi phí", "học kỳ"],
    },
    {
        "doc_id": "FPTU-HB-004",
        "title": "Chính sách Học bổng Tài năng & Học bổng Khuyến khích",
        "category": "hoc_phi_hoc_bong",
        "content": (
            "Học bổng Nguyễn Văn Đạo cấp từ 30%, 50%, 70% đến 100% học phí toàn khóa. "
            "Để duy trì học bổng qua từng kỳ, sinh viên phải duy trì kết quả học tập GPA kỳ đạt từ 2.8 trở lên (với học bổng 30-50%) "
            "hoặc GPA từ 3.2 trở lên (với học bổng 70-100%), đồng thời không bị điểm F ở bất kỳ môn nào và điểm rèn luyện tốt."
        ),
        "source": "Quy chế Học bổng ĐH FPT - Quyết định 215/QĐ-ĐHFPT 2024",
        "base_score": 0.88,
        "keywords": ["học bổng", "nguyễn văn đạo", "duy trì học bổng", "khuyến khích"],
    },
    {
        "doc_id": "FPTU-SYL-005",
        "title": "Quy định về môn học tiên quyết và đăng ký học phần",
        "category": "syllabus",
        "content": (
            "Môn tiên quyết (Prerequisite course) là môn học sinh viên bắt buộc phải học và đạt điểm qua (>= 4.0/10) "
            "trước khi được phép đăng ký học môn học kế tiếp. Ví dụ: PRF192 là tiên quyết của PRO192; CSD201 là tiên quyết của LAB211. "
            "Mỗi kỳ học, sinh viên được xếp lịch học mặc định theo tiến độ lớp chuẩn, có thể đăng ký bổ sung tối đa 2 môn nếu không trùng lịch."
        ),
        "source": "Syllabus Cấu trúc chương trình ngành Kỹ thuật Phần mềm FPTU 2024",
        "base_score": 0.85,
        "keywords": ["tiên quyết", "môn học", "học phần", "đăng ký", "prf192", "pro192", "csd201"],
    },
    {
        "doc_id": "FPTU-SYL-006",
        "title": "Quy chế làm Khóa luận Tốt nghiệp (Capstone Project)",
        "category": "syllabus",
        "content": (
            "Khóa luận tốt nghiệp (SEP490 / Capstone Project) được thực hiện theo nhóm từ 3 đến 5 sinh viên trong thời gian 15 tuần. "
            "Điều kiện để được nhận đồ án tốt nghiệp: Sinh viên đã hoàn thành tối thiểu 90% số tín chỉ toàn khóa, "
            "đã hoàn thành kỳ thực tập doanh nghiệp (OJT) và không nợ các môn chuyên ngành bắt buộc cấp độ 5 trở lên."
        ),
        "source": "Quy định Hướng dẫn và Đánh giá Đồ án Tốt nghiệp CNTT - ĐH FPT 2024",
        "base_score": 0.83,
        "keywords": ["đồ án", "khóa luận", "capstone", "sep490", "tốt nghiệp nhóm", "ojt"],
    },
    {
        "doc_id": "FPTU-QC-007",
        "title": "Quy định kiểm tra, thi lại và học lại",
        "category": "quy_che",
        "content": (
            "Điểm tổng kết môn học gồm: Điểm chuyên cần (vắng không quá 20% tổng số buổi), điểm bài tập/assignment, điểm thực hành (practical exam) và điểm thi cuối kỳ (final exam). "
            "Nếu sinh viên có điểm thi cuối kỳ dưới 4.0/10 hoặc điểm trung bình môn dưới 5.0/10 thì bị tính là không đạt (Fail) và phải đóng học phí đăng ký học lại môn đó, trường không tổ chức thi lại."
        ),
        "source": "Quy chế Đào tạo ĐH FPT 2024 - Điều 19: Thi và đánh giá kết quả, Trang 31",
        "base_score": 0.80,
        "keywords": ["thi lại", "học lại", "điểm liệt", "điểm thi", "chuyên cần", "vắng", "final exam"],
    },
    {
        "doc_id": "FPTU-HP-AI-2026",
        "title": "Biểu phí chuyên ngành Trí tuệ Nhân tạo (AI) - Khóa 2026",
        "category": "hoc_phi_hoc_bong",
        "content": (
            "Học phí chuyên ngành Trí tuệ Nhân tạo (AI) áp dụng cho sinh viên nhập học Khóa 2026 là 32.500.000 VNĐ/học kỳ. "
            "Mức học phí duy trì cố định trong suốt 9 học kỳ chuyên ngành của chương trình đào tạo."
        ),
        "source": "Quyết định 312/QĐ-ĐHFPT - Biểu phí tuyển sinh Khóa 2026",
        "base_score": 0.96,
        "cohort": "2026",
        "program": "AI",
        "keywords": ["học phí", "ai", "trí tuệ nhân tạo", "2026", "khoá 2026", "tiền học"],
    },
    {
        "doc_id": "FPTU-HP-AI-2023",
        "title": "Biểu phí chuyên ngành Trí tuệ Nhân tạo (AI) - Khóa 2023",
        "category": "hoc_phi_hoc_bong",
        "content": (
            "Học phí chuyên ngành Trí tuệ Nhân tạo (AI) áp dụng cho sinh viên nhập học Khóa 2023 là 27.300.000 VNĐ/học kỳ. "
            "Sinh viên khóa 2023 hoàn thành học phí theo mức quy định cũ tại thời điểm nhập học."
        ),
        "source": "Quyết định 118/QĐ-ĐHFPT - Biểu phí tuyển sinh Khóa 2023",
        "base_score": 0.94,
        "cohort": "2023",
        "program": "AI",
        "keywords": ["học phí", "ai", "trí tuệ nhân tạo", "2023", "khoá 2023", "tiền học"],
    },
]


def retrieve(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.3,
    parsed_query: Optional[Any] = None,
) -> List[Dict]:
    """
    Truy xuất danh sách kết quả mock cho Tuần 1-3 tuân thủ đúng Retrieval Contract.
    Tính toán độ trùng khớp từ khóa cơ bản và lọc chính xác theo các slots từ ParsedQuery
    (ví dụ cohort, program) để ngăn chặn tài liệu khác khóa gây nhiễu.
    """
    q_lower = query.lower()
    scored_results = []

    # Trích xuất các điều kiện lọc từ parsed_query nếu có
    target_cohort = None
    target_program = None
    if parsed_query and hasattr(parsed_query, "slots"):
        target_cohort = parsed_query.slots.get("cohort")
        target_program = parsed_query.slots.get("program")

    for item in MOCK_FPTU_KNOWLEDGE_BASE:
        # Lọc nghiêm ngặt: nếu truy vấn hỏi khóa cụ thể mà tài liệu thuộc khóa khác -> bỏ qua ngay
        if target_cohort and item.get("cohort") and item["cohort"] != target_cohort:
            continue

        match_count = sum(1 for kw in item["keywords"] if kw in q_lower)
        # Nếu có từ khóa trùng khớp thì lấy base_score chuẩn hóa, ngược lại gán 0.0 (OOD)
        if match_count > 0:
            score = min(0.98, max(0.50, item["base_score"]))
            # Tăng độ ưu tiên nếu khớp chính xác slot program hoặc cohort
            if target_cohort and item.get("cohort") == target_cohort:
                score = min(0.99, score + 0.03)
            if target_program and item.get("program") == target_program:
                score = min(0.99, score + 0.03)
        else:
            score = 0.0

        # Lọc theo ngưỡng điểm score_threshold
        if score < score_threshold:
            continue

        scored_results.append({
            "doc_id": item["doc_id"],
            "text": item["content"],
            "content": item["content"],
            "score": round(score, 2),
            "retrieval_strategy": "mock",
            "metadata": {
                "effective_date": item.get("cohort", "2024-01-01"),
                "applies_to_cohort": item.get("cohort", "ALL"),
                "doc_type": item["category"],
            },
            "title": item["title"],
            "category": item["category"],
            "source": item["source"],
            "_match_count": match_count,
        })

    scored_results.sort(key=lambda x: (x["_match_count"], x["score"]), reverse=True)

    clean_results = []
    for r in scored_results[:top_k]:
        clean_item = {k: v for k, v in r.items() if not k.startswith("_")}
        clean_results.append(clean_item)

    return clean_results
