import os
import sys
import json
import hashlib
import re

sys.stdout.reconfigure(encoding="utf-8")

def normalize_text(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"[?!.,:;\"\'`]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t

def text_hash(text: str) -> str:
    return hashlib.md5(normalize_text(text).encode("utf-8")).hexdigest()

def load_v1_hashes():
    v1_hashes = set()
    v1_dir = os.path.join("data", "evaluation", "multiturn_rounds")
    if os.path.exists(v1_dir):
        for fname in os.listdir(v1_dir):
            if fname.endswith(".jsonl"):
                fpath = os.path.join(v1_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            d = json.loads(line)
                            q = d.get("query", "")
                            if q:
                                v1_hashes.add(text_hash(q))
    return v1_hashes

def main():
    v1_hashes = load_v1_hashes()
    print(f"Loaded {len(v1_hashes)} unique queries from v1 benchmark.")
    
    # Load truth databases
    with open("data/processed/structured_data.json", "r", encoding="utf-8") as f:
        struct_data = json.load(f)
    with open("data/processed/structured_data_courses.json", "r", encoding="utf-8") as f:
        courses_data = json.load(f)
        
    courses_by_code = {c["course_code"].upper(): c for c in courses_data.get("courses", [])}
    tuition_by_campus = struct_data.get("tuition_by_campus", {})
    cohort_fees = {c["cohort"]: c for c in struct_data.get("fpt_cohort_fees", [])}
    common_fees = struct_data.get("common_fees", {})
    
    out_dir = os.path.join("data", "evaluation", "benchmark_v2")
    os.makedirs(out_dir, exist_ok=True)
    
    all_v2_hashes = set()
    total_generated = 0

    # We will generate 10 batches (B01 - B10), each exactly 50 questions
    
    # =========================================================================
    # BATCH 01: multi_turn_continuation (25 sessions x 2 turns = 50 questions)
    # Chủ đề: Khóa học công nghệ mới (OSG202, NWC203c, PRJ301, AIL302m, NLP301c, CRY301...)
    # =========================================================================
    b01_items = []
    b01_scenarios = [
        ("OSG202", "Hệ điều hành OSG202", "Môn Hệ điều hành OSG202 học những nội dung gì?", ["hệ điều hành", "tiến trình", "bộ nhớ", "luồng"],
         "Môn này có thực hành bài tập Lab không?", ["OSG202"], ["thực hành", "Lab", "PE", "EOS"]),
        ("NWC203c", "Mạng máy tính NWC203c", "Môn Mạng máy tính NWC203c có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"],
         "Môn này học giáo trình chính nào?", ["NWC203c"], ["Kurose", "Ross", "Computer Networking", "Top-Down"]),
        ("PRJ301", "Lập trình Java Web PRJ301", "Môn Lập trình Java Web PRJ301 có môn tiên quyết là gì?", ["PRO192", "CSD201", "DBI202"],
         "Môn này sinh viên làm đồ án hay thi PE?", ["PRJ301"], ["PE", "thực hành", "đánh giá"]),
        ("PRN211", "Lập trình C# .NET PRN211", "Môn Lập trình C# PRN211 học vào học kỳ thứ mấy?", ["kỳ 5", "5"],
         "Môn này gồm bao nhiêu tín chỉ?", ["PRN211"], ["3 tín chỉ", "3"]),
        ("SWP391", "Dự án phát triển phần mềm SWP391", "Môn Dự án phần mềm SWP391 có cần môn tiên quyết không?", ["SWE201c", "PRJ301", "tiên quyết"],
         "Hình thức đánh giá môn này gồm những gì?", ["SWP391"], ["bảo vệ", "đồ án", "project", "thực hành"]),
        ("SWT301", "Kiểm thử phần mềm SWT301", "Nội dung đào tạo của môn Kiểm thử phần mềm SWT301 là gì?", ["kiểm thử", "test", "automation", "unit test"],
         "Tên cuốn giáo trình chính thức dùng cho môn này là gì?", ["SWT301"], ["Foundations of Software Testing", "Aditya Mathur", "Testing"]),
        ("SWR302", "Đặc tả yêu cầu phần mềm SWR302", "Môn SWR302 Đặc tả yêu cầu phần mềm có mấy tín chỉ?", ["3 tín chỉ", "3"],
         "Môn này thuộc học kỳ nào trong khung chương trình?", ["SWR302"], ["kỳ 5", "5"]),
        ("AIL302m", "Học máy AIL302m", "Môn Học máy AIL302m học những thuật toán nào?", ["Machine Learning", "hồi quy", "phân lớp", "cụm", "học máy"],
         "Giáo trình môn này do ai biên soạn?", ["AIL302m"], ["Tom Mitchell", "Machine Learning", "Pattern Recognition"]),
        ("NLP301c", "Xử lý ngôn ngữ tự nhiên NLP301c", "Môn Xử lý ngôn ngữ tự nhiên NLP301c có môn tiên quyết là gì?", ["AIL302m", "MAS291", "tiên quyết"],
         "Môn này học về những nội dung trọng tâm gì?", ["NLP301c"], ["ngôn ngữ", "text", "transformer", "bert", "tiếng"]),
        ("CVL301c", "Thị giác máy tính CVL301c", "Môn Thị giác máy tính CVL301c có mấy tín chỉ đào tạo?", ["3 tín chỉ", "3"],
         "Môn này được bố trí học ở kỳ mấy?", ["CVL301c"], ["kỳ 5", "5"]),
        ("DLG301", "Học sâu DLG301", "Môn Học sâu DLG301 giảng dạy những kiến trúc nào?", ["Deep Learning", "CNN", "RNN", "học sâu", "mạng nơ-ron"],
         "Môn này có yêu cầu môn học trước không?", ["DLG301"], ["AIL302m", "tiên quyết", "không"]),
        ("CRY301", "Mật mã học CRY301", "Môn Mật mã học CRY301 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"],
         "Giáo trình môn này là cuốn sách nào?", ["CRY301"], ["Cryptography", "Network Security", "Stallings"]),
        ("IAL201", "An toàn mạng IAL201", "Môn An toàn mạng IAL201 học những gì?", ["tường lửa", "firewall", "bảo mật", "mạng", "tấn công"],
         "Môn này có bài thi thực hành PE không?", ["IAL201"], ["thực hành", "PE", "EOS", "đánh giá", "không"]),
        ("MKT101", "Marketing căn bản MKT101", "Môn Marketing căn bản MKT101 có mấy tín chỉ?", ["3 tín chỉ", "3"],
         "Giáo trình chính môn này của tác giả nào?", ["MKT101"], ["Philip Kotler", "Armstrong", "Principles of Marketing"]),
        ("MGT103", "Nhập môn quản trị MGT103", "Môn Nhập môn quản trị MGT103 học nội dung gì?", ["quản trị", "lập kế hoạch", "tổ chức", "lãnh đạo"],
         "Môn này học vào kỳ thứ mấy?", ["MGT103"], ["kỳ 1", "1", "kỳ 2", "2"]),
        ("ECO111", "Kinh tế vi mô ECO111", "Môn Kinh tế vi mô ECO111 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"],
         "Giáo trình bắt buộc của môn học này có tên là gì?", ["ECO111"], ["Microeconomics", "Mankiw", "Pindyck"]),
        ("ECO121", "Kinh tế vĩ mô ECO121", "Môn Kinh tế vĩ mô ECO121 học những chủ đề nào?", ["GDP", "lạm phát", "thất nghiệp", "chính sách tiền tệ"],
         "Môn này có cần qua môn vi mô trước không?", ["ECO121"], ["ECO111", "tiên quyết", "không"]),
        ("FIN202", "Tài chính doanh nghiệp FIN202", "Môn Tài chính doanh nghiệp FIN202 có mấy tín chỉ?", ["3 tín chỉ", "3"],
         "Môn này thuộc ngành đào tạo nào?", ["FIN202"], ["Quản trị kinh doanh", "QTKD"]),
        ("DGT101", "Nhập môn thiết kế đồ họa DGT101", "Môn Nhập môn thiết kế DGT101 học những công cụ gì?", ["Photoshop", "Illustrator", "thiết kế", "đồ họa"],
         "Môn này có số lượng tín chỉ là bao nhiêu?", ["DGT101"], ["3 tín chỉ", "3"]),
        ("GRA201", "Đồ họa máy tính GRA201", "Môn Đồ họa máy tính GRA201 có mấy tín chỉ?", ["3 tín chỉ", "3"],
         "Môn này có môn tiên quyết là môn nào?", ["GRA201"], ["VWS101", "tiên quyết"]),
        ("ENG101", "Tiếng Anh học thuật 1 ENG101", "Môn Tiếng Anh học thuật ENG101 có mấy tín chỉ?", ["3 tín chỉ", "3"],
         "Môn này học vào học kỳ thứ mấy?", ["ENG101"], ["kỳ 1", "1"]),
        ("JAP101", "Tiếng Nhật sơ cấp 1 JAP101", "Môn Tiếng Nhật 1 JAP101 đào tạo khối lượng mấy tín chỉ?", ["3 tín chỉ", "3"],
         "Môn này học bảng chữ cái nào?", ["JAP101"], ["Hiragana", "Katakana", "chữ cái", "tiếng Nhật"]),
        ("KOR101", "Tiếng Hàn sơ cấp 1 KOR101", "Môn Tiếng Hàn 1 KOR101 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"],
         "Môn này sử dụng cuốn giáo trình nào để giảng dạy?", ["KOR101"], ["Seoul", "tiếng Hàn", "Korean"]),
        ("VOV124", "Vovinam 2 VOV124", "Môn Giáo dục thể chất Vovinam 2 VOV124 có mấy tín chỉ?", ["0 tín chỉ", "0"],
         "Môn này có điều kiện tiên quyết là môn nào?", ["VOV124"], ["VOV114", "tiên quyết"]),
        ("MIL111", "Quân sự 1 MIL111", "Học phần Giáo dục quốc phòng MIL111 tính bao nhiêu tín chỉ?", ["0 tín chỉ", "0"],
         "Học phần này học ở học kỳ thứ mấy?", ["MIL111"], ["kỳ 1", "1"])
    ]
    
    for idx, (code, title, t1, t1_ans, t2, t2_rew, t2_ans) in enumerate(b01_scenarios, 1):
        s_id = f"v2_b01_sess_{idx:03d}"
        q1_id = f"V2_B01_{2*idx-1:03d}"
        q2_id = f"V2_B01_{2*idx:03d}"
        b01_items.append({
            "q_id": q1_id, "batch": "batch_01", "category": "multi_turn_continuation",
            "session_id": s_id, "turn_index": 1, "query": t1, "is_continuation": False,
            "expected_rewrite_contains": [], "is_topic_switch": False, "expected_route": "structured_lookup",
            "golden_answer": f"Thông tin môn {code} trong CKB.", "expected_answer_contains": t1_ans
        })
        b01_items.append({
            "q_id": q2_id, "batch": "batch_01", "category": "multi_turn_continuation",
            "session_id": s_id, "turn_index": 2, "query": t2, "is_continuation": True,
            "expected_rewrite_contains": t2_rew, "is_topic_switch": False, "expected_route": "structured_lookup",
            "golden_answer": f"Thông tin bổ trợ môn {code}.", "expected_answer_contains": t2_ans
        })

    # =========================================================================
    # BATCH 02: topic_switch (25 sessions x 2 turns = 50 questions)
    # Kiểm tra chuyển đổi ngữ cảnh đột ngột, không bị dính context bleeding
    # =========================================================================
    b02_items = []
    b02_scenarios = [
        ("Lệ phí thi lại của trường Đại học FPT là bao nhiêu tiền?", ["300.000", "300,000"],
         "Môn Lập trình C# PRN211 có bao nhiêu tín chỉ?", "structured_lookup", ["3 tín chỉ", "3"], ["thi lại", "lệ phí"]),
        ("Học phí chuyên ngành khóa K18 là bao nhiêu?", ["27.300.000", "27,300,000", "25.300.000", "25,300,000"],
         "Thời hạn nộp đơn phúc khảo bài thi là mấy ngày?", "rag_pipeline", ["ngày", "phúc khảo"], ["K18", "học phí"]),
        ("Giai đoạn thực tập doanh nghiệp OJT diễn ra ở kỳ học thứ mấy?", ["kỳ 6", "6", "học kỳ 6"],
         "Chi phí ký túc xá phân hiệu Hòa Lạc là bao nhiêu một kỳ?", "structured_lookup", ["4.000.000", "4,000,000"], ["ojt", "thực tập"]),
        ("Điều kiện để đạt học bổng FPT University là gì?", ["học bổng", "điểm", "xét"],
         "Môn Mạng máy tính NWC203c có môn tiên quyết không?", "structured_lookup", ["CSI104", "tiên quyết", "không"], ["học bổng"]),
        ("Quy định về việc bảo lưu học tập tại trường như thế nào?", ["bảo lưu", "học kỳ", "đơn"],
         "Phí cấp bản sao bảng điểm là bao nhiêu?", "structured_lookup", ["50.000", "50,000"], ["bảo lưu"]),
        ("Môn CSD201 Cấu trúc dữ liệu học về những gì?", ["cây", "đồ thị", "sắp xếp", "ngăn xếp"],
         "Khóa K21 phải đóng bao nhiêu tiền lệ phí thi lại một lần?", "structured_lookup", ["350.000", "350,000"], ["CSD201", "cấu trúc dữ liệu"]),
        ("Chuẩn đầu ra tiếng Anh ngành CNTT yêu cầu chứng chỉ gì?", ["IELTS", "TOEFL", "VSTEP"],
         "Môn Vovinam 2 VOV124 có mấy tín chỉ?", "structured_lookup", ["0 tín chỉ", "0"], ["tiếng Anh", "chuẩn đầu ra"]),
        ("Quy chế thôi học áp dụng khi sinh viên nhận bao nhiêu lần cảnh báo học tập?", ["cảnh báo", "buộc thôi học", "lần"],
         "Chính sách ưu đãi học phí tại phân hiệu Quy Nhơn là bao nhiêu %?", "structured_lookup", ["50%", "50"], ["cảnh báo", "thôi học"]),
        ("Ký túc xá khóa K20 giá bao nhiêu một kỳ?", ["4.000.000", "4,000,000"],
         "Môn Học máy AIL302m học giáo trình nào?", "structured_lookup", ["Mitchell", "Machine Learning"], ["ký túc xá", "K20"]),
        ("Khóa K22 học bao nhiêu học kỳ chuyên ngành?", ["9 học kỳ", "9"],
         "Quy định về việc mang tài liệu vào phòng thi EOS như thế nào?", "rag_pipeline", ["tài liệu", "quy chế", "thi"], ["K22", "học kỳ"]),
        ("Học phí ngành AI tại TP.HCM khóa 2026 là bao nhiêu?", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"],
         "Môn Mật mã học CRY301 có mấy tín chỉ?", "structured_lookup", ["3 tín chỉ", "3"], ["học phí", "AI", "TP.HCM"]),
        ("Lệ phí học lại một tín chỉ khóa K17 là bao nhiêu?", ["600.000", "600,000"],
         "Cách tính điểm trung bình tích lũy GPA tại FPT?", "rag_pipeline", ["GPA", "tích lũy", "tín chỉ"], ["K17", "học lại"]),
        ("Môn Nhập môn quản trị MGT103 học những gì?", ["quản trị", "lãnh đạo", "kế hoạch"],
         "Lệ phí công nhận tốt nghiệp và cấp bằng là bao nhiêu?", "structured_lookup", ["1.500.000", "1,500,000"], ["MGT103"]),
        ("Môn Giáo dục quốc phòng MIL111 có mấy tín chỉ?", ["0 tín chỉ", "0"],
         "Ưu đãi phân hiệu Cần Thơ được giảm bao nhiêu phần trăm?", "structured_lookup", ["30%", "30"], ["quân sự", "MIL111"]),
        ("Trong giai đoạn OJT sinh viên có phải đóng học phí chuyên ngành không?", ["không phải đóng học phí chuyên ngành", "miễn học phí"],
         "Môn Lập trình Java Web PRJ301 học những công nghệ gì?", "structured_lookup", ["Java", "Servlet", "JSP", "Web"], ["OJT", "học phí"]),
        ("Khóa K19 có mức phí tiếng Anh chuẩn bị là bao nhiêu một mức?", ["11.300.000", "11,300,000", "10.350.000"],
         "Quy định về trang phục sinh viên khi đến trường Đại học FPT?", "rag_pipeline", ["trang phục", "đồng phục", "áo cam"], ["K19", "tiếng Anh"]),
        ("Môn Kiểm thử phần mềm SWT301 có bài thi thực hành PE không?", ["PE", "thực hành", "đánh giá"],
         "Lệ phí thi lại của khóa K22 là bao nhiêu?", "structured_lookup", ["350.000", "350,000"], ["SWT301", "kiểm thử"]),
        ("Sinh viên nợ bao nhiêu tín chỉ thì không được làm đồ án tốt nghiệp?", ["tín chỉ", "nợ môn", "đồ án"],
         "Ký túc xá khóa K21 tại Hòa Lạc giá bao nhiêu?", "structured_lookup", ["4.200.000", "4,200,000"], ["đồ án", "nợ"]),
        ("Môn Kinh tế vi mô ECO111 có mấy tín chỉ?", ["3 tín chỉ", "3"],
         "Chính sách học bổng Nguyễn Văn Đạo xét theo tiêu chí nào?", "rag_pipeline", ["học bổng", "Nguyễn Văn Đạo", "kỳ thi"], ["ECO111"]),
        ("Phân hiệu Đà Nẵng được ưu đãi học phí bao nhiêu phần trăm?", ["30%", "30"],
         "Môn Dự án phần mềm SWP391 học vào kỳ thứ mấy?", "structured_lookup", ["kỳ 5", "5", "kỳ 6", "6"], ["Đà Nẵng", "ưu đãi"]),
        ("Khóa K17 có bao nhiêu kỳ học chuyên ngành tất cả?", ["9 học kỳ", "9"],
         "Hồ sơ chuyển ngành học tại Đại học FPT gồm những gì?", "rag_pipeline", ["chuyển ngành", "đơn", "phòng đào tạo"], ["K17", "học kỳ"]),
        ("Môn Tiếng Anh học thuật ENG101 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"],
         "Tiền ký túc xá khóa K18 là bao nhiêu một kỳ?", "structured_lookup", ["3.800.000", "3,800,000"], ["ENG101"]),
        ("Điểm thi PE được phúc khảo trong vòng bao nhiêu ngày?", ["ngày", "phúc khảo"],
         "Môn Thiết kế đồ họa DGT101 có mấy tín chỉ?", "structured_lookup", ["3 tín chỉ", "3"], ["phúc khảo", "điểm thi"]),
        ("Khóa K22 phí ký túc xá là bao nhiêu tiền một học kỳ?", ["4.500.000", "4,500,000"],
         "Thủ tục đăng ký học đi lại như thế nào?", "rag_pipeline", ["học lại", "đăng ký", "học vụ"], ["K22", "ký túc xá"]),
        ("Môn Tiếng Nhật 1 JAP101 có môn tiên quyết không?", ["không", "tiên quyết"],
         "Lệ phí thi lại của khóa K20 là bao nhiêu?", "structured_lookup", ["300.000", "300,000"], ["JAP101"])
    ]
    
    for idx, (t1, t1_ans, t2, t2_route, t2_ans, avoid_kw) in enumerate(b02_scenarios, 1):
        s_id = f"v2_b02_sess_{idx:03d}"
        q1_id = f"V2_B02_{2*idx-1:03d}"
        q2_id = f"V2_B02_{2*idx:03d}"
        b02_items.append({
            "q_id": q1_id, "batch": "batch_02", "category": "topic_switch_turn1",
            "session_id": s_id, "turn_index": 1, "query": t1, "is_continuation": False,
            "expected_rewrite_contains": [], "is_topic_switch": False, "expected_route": "structured_lookup" if any(w in t1.lower() for w in ["bao nhiêu", "mấy tín"]) else "rag_pipeline",
            "golden_answer": "Câu hỏi chủ đề ban đầu.", "expected_answer_contains": t1_ans
        })
        b02_items.append({
            "q_id": q2_id, "batch": "batch_02", "category": "topic_switch",
            "session_id": s_id, "turn_index": 2, "query": t2, "is_continuation": False,
            "expected_rewrite_contains": [], "is_topic_switch": True, "expected_route": t2_route,
            "golden_answer": "Câu hỏi chuyển đổi chủ đề hoàn toàn độc lập.", "expected_answer_contains": t2_ans,
            "avoid_bleed": avoid_kw
        })

    # =========================================================================
    # BATCH 03: cohort_deep (50 câu hỏi độc lập về K17 - K22)
    # =========================================================================
    b03_items = []
    cohort_specs = [
        ("K17", 25300000, 10350000, 600000, 300000, 3600000),
        ("K18", 27300000, 11300000, 650000, 300000, 3800000),
        ("K19", 28700000, 11300000, 650000, 300000, 4000000),
        ("K20", 28700000, 11300000, 650000, 300000, 4000000),
        ("K21", 31200000, 11900000, 700000, 350000, 4200000),
        ("K22", 32500000, 11900000, 750000, 350000, 4500000),
    ]
    
    b03_q_templates = [
        ("Học phí chuyên ngành một kỳ của sinh viên khóa {c} là bao nhiêu?", lambda c, s, p, r, t, d: [f"{s:,}", f"{s:,}".replace(",", ".")]),
        ("Học phí tiếng Anh dự bị khóa {c} thu bao nhiêu tiền một level?", lambda c, s, p, r, t, d: [f"{p:,}", f"{p:,}".replace(",", ".")]),
        ("Lệ phí học lại một tín chỉ của khóa {c} quy định là bao nhiêu?", lambda c, s, p, r, t, d: [f"{r:,}", f"{r:,}".replace(",", ".")]),
        ("Lệ phí thi lại của sinh viên khóa {c} là bao nhiêu tiền một lần?", lambda c, s, p, r, t, d: [f"{t:,}", f"{t:,}".replace(",", ".")]),
        ("Mức phí ký túc xá mỗi học kỳ cho khóa {c} là bao nhiêu?", lambda c, s, p, r, t, d: [f"{d:,}", f"{d:,}".replace(",", ".")]),
        ("Khóa {c} đào tạo tổng cộng bao nhiêu học kỳ chuyên ngành?", lambda c, s, p, r, t, d: ["9 học kỳ", "9"]),
        ("Khung chương trình tiếng Anh chuẩn bị khóa {c} có tối đa mấy mức?", lambda c, s, p, r, t, d: ["6 mức", "6 level", "6"]),
        ("Biểu phí chuyên ngành chính thức của khóa {c} là bao nhiêu?", lambda c, s, p, r, t, d: [f"{s:,}", f"{s:,}".replace(",", ".")]),
    ]
    
    cnt = 0
    for c, s, p, r, t, d in cohort_specs:
        for q_tmpl, ans_fn in b03_q_templates:
            if cnt >= 50:
                break
            cnt += 1
            query_text = q_tmpl.format(c=c)
            ans_exp = ans_fn(c, s, p, r, t, d)
            b03_items.append({
                "q_id": f"V2_B03_{cnt:03d}", "batch": "batch_03", "category": "cohort_specific",
                "session_id": f"v2_b03_sess_{cnt:03d}", "turn_index": 1, "query": query_text,
                "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
                "expected_route": "structured_lookup", "golden_answer": f"Biểu phí khóa {c}",
                "expected_answer_contains": ans_exp
            })
    # Fill remaining to reach 50
    while len(b03_items) < 50:
        cnt += 1
        c = "K22" if cnt % 2 == 0 else "K21"
        query_text = f"Tổng chi phí chuyên ngành toàn khóa của sinh viên khóa {c} là bao nhiêu?"
        b03_items.append({
            "q_id": f"V2_B03_{cnt:03d}", "batch": "batch_03", "category": "cohort_specific",
            "session_id": f"v2_b03_sess_{cnt:03d}", "turn_index": 1, "query": query_text,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": "structured_lookup", "golden_answer": f"Chi phí toàn khóa {c}",
            "expected_answer_contains": ["học kỳ", "chuyên ngành"]
        })

    # =========================================================================
    # BATCH 04: course_deep_extended (50 câu CKB các môn chưa dùng ở v1)
    # =========================================================================
    b04_items = []
    b04_courses = [
        ("OSG202", "Hệ điều hành", "Môn Hệ điều hành OSG202 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"]),
        ("NWC203c", "Mạng máy tính", "Môn Mạng máy tính NWC203c học những chủ đề gì?", ["mạng", "network", "giao thức", "tcp/ip"]),
        ("PRJ301", "Lập trình Java Web", "Môn Lập trình Java Web PRJ301 có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("PRN211", "Lập trình C#", "Môn Lập trình C# PRN211 học giáo trình gì?", ["C#", "Pro C#", "Troelsen", ".NET"]),
        ("SWP391", "Dự án phần mềm", "Môn SWP391 Dự án phần mềm có bao nhiêu tín chỉ đào tạo?", ["3 tín chỉ", "3"]),
        ("SWT301", "Kiểm thử phần mềm", "Môn Kiểm thử phần mềm SWT301 có môn tiên quyết là môn nào?", ["SWE201c", "tiên quyết"]),
        ("SWR302", "Đặc tả yêu cầu phần mềm", "Môn SWR302 học những nội dung gì?", ["yêu cầu", "requirement", "SRS", "UML", "đặc tả"]),
        ("SWD392", "Thiết kế kiến trúc phần mềm", "Môn SWD392 Thiết kế kiến trúc phần mềm có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("SEP490", "Khóa luận tốt nghiệp KTPM", "Môn SEP490 Khóa luận tốt nghiệp KTPM có bao nhiêu tín chỉ?", ["10 tín chỉ", "10"]),
        ("AIL302m", "Học máy", "Môn Học máy AIL302m có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"]),
        ("NLP301c", "Xử lý ngôn ngữ tự nhiên", "Môn NLP301c học vào học kỳ thứ mấy?", ["kỳ 6", "6", "kỳ 7", "7"]),
        ("CVL301c", "Thị giác máy tính", "Môn Thị giác máy tính CVL301c có môn tiên quyết là gì?", ["AIL302m", "tiên quyết"]),
        ("DLG301", "Học sâu", "Môn Học sâu DLG301 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"]),
        ("AIP391", "Dự án AI", "Môn AIP391 Dự án ứng dụng AI có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("AIP490", "Khóa luận tốt nghiệp AI", "Môn Khóa luận tốt nghiệp AI AIP490 tính bao nhiêu tín chỉ?", ["10 tín chỉ", "10"]),
        ("CRY301", "Mật mã học", "Môn Mật mã học CRY301 có bao nhiêu tín chỉ đào tạo?", ["3 tín chỉ", "3"]),
        ("IAL201", "An toàn mạng", "Môn An toàn mạng IAL201 học giáo trình chính nào?", ["Network Security", "Stallings", "giáo trình"]),
        ("IAR301", "Ứng cứu sự cố", "Môn IAR301 Ứng cứu sự cố an toàn thông tin có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("FOR301", "Điều tra số máy tính", "Môn Điều tra số FOR301 học những nội dung trọng tâm gì?", ["forensics", "điều tra", "chứng cứ số", "dấu vết"]),
        ("IAP490", "Khóa luận tốt nghiệp ATTT", "Môn Khóa luận tốt nghiệp ATTT IAP490 có mấy tín chỉ?", ["10 tín chỉ", "10"]),
        ("MKT101", "Marketing căn bản", "Môn Marketing căn bản MKT101 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"]),
        ("MGT103", "Nhập môn quản trị", "Môn Nhập môn quản trị MGT103 có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("ECO111", "Kinh tế vi mô", "Môn Kinh tế vi mô ECO111 học những nội dung gì?", ["cung cầu", "thị trường", "giá cả", "độ co giãn"]),
        ("ECO121", "Kinh tế vĩ mô", "Môn Kinh tế vĩ mô ECO121 có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("ACC101", "Nguyên lý kế toán", "Môn ACC101 Nguyên lý kế toán đào tạo mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("FIN202", "Tài chính doanh nghiệp", "Môn Tài chính doanh nghiệp FIN202 có môn tiên quyết không?", ["ACC101", "tiên quyết"]),
        ("OBE102", "Hành vi tổ chức", "Môn Hành vi tổ chức OBE102 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"]),
        ("MKP391", "Dự án Marketing", "Môn Dự án Marketing MKP391 có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("BAP490", "Khóa luận QTKD", "Môn Khóa luận tốt nghiệp QTKD BAP490 có bao nhiêu tín chỉ?", ["10 tín chỉ", "10"]),
        ("DGT101", "Nhập môn thiết kế", "Môn Nhập môn thiết kế DGT101 có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("VWS101", "Vẽ tay mỹ thuật", "Môn Vẽ tay VWS101 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"]),
        ("GRA201", "Đồ họa máy tính", "Môn Đồ họa máy tính GRA201 có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("TYP201", "Nghệ thuật chữ", "Môn Nghệ thuật chữ Typography TYP201 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"]),
        ("ANM301", "Hoạt hình 2D/3D", "Môn Hoạt hình 2D ANM301 học những nội dung gì?", ["hoạt hình", "chuyển động", "animation", "frame"]),
        ("GDP490", "Khóa luận Thiết kế", "Môn Khóa luận tốt nghiệp Thiết kế đồ họa GDP490 có mấy tín chỉ?", ["10 tín chỉ", "10"]),
        ("ENG101", "Tiếng Anh học thuật 1", "Môn Tiếng Anh học thuật 1 ENG101 có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("ENG102", "Tiếng Anh học thuật 2", "Môn Tiếng Anh học thuật 2 ENG102 có môn tiên quyết là gì?", ["ENG101", "tiên quyết"]),
        ("ENB301", "Tiếng Anh thương mại", "Môn Tiếng Anh thương mại ENB301 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"]),
        ("ENT301", "Biên phiên dịch tiếng Anh", "Môn Biên dịch tiếng Anh ENT301 có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("ENP490", "Khóa luận Ngôn ngữ Anh", "Môn Khóa luận tốt nghiệp Ngôn ngữ Anh ENP490 có bao nhiêu tín chỉ?", ["10 tín chỉ", "10"]),
        ("JAP101", "Tiếng Nhật 1", "Môn Tiếng Nhật 1 JAP101 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"]),
        ("JAP102", "Tiếng Nhật 2", "Môn Tiếng Nhật 2 JAP102 có môn tiên quyết là gì?", ["JAP101", "tiên quyết"]),
        ("JIT301", "Tiếng Nhật CNTT", "Môn Tiếng Nhật CNTT JIT301 có mấy tín chỉ?", ["3 tín chỉ", "3"]),
        ("JAP490", "Khóa luận Ngôn ngữ Nhật", "Môn Khóa luận tốt nghiệp Ngôn ngữ Nhật JAP490 có mấy tín chỉ?", ["10 tín chỉ", "10"]),
        ("KOR101", "Tiếng Hàn 1", "Môn Tiếng Hàn 1 KOR101 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"]),
        ("KOR102", "Tiếng Hàn 2", "Môn Tiếng Hàn 2 KOR102 có môn tiên quyết là gì?", ["KOR101", "tiên quyết"]),
        ("KOR490", "Khóa luận Ngôn ngữ Hàn", "Môn Khóa luận tốt nghiệp Ngôn ngữ Hàn KOR490 có mấy tín chỉ?", ["10 tín chỉ", "10"]),
        ("VOV124", "Vovinam 2", "Môn Giáo dục thể chất Vovinam 2 VOV124 có mấy tín chỉ?", ["0 tín chỉ", "0"]),
        ("VOV134", "Vovinam 3", "Môn Giáo dục thể chất Vovinam 3 VOV134 có mấy tín chỉ?", ["0 tín chỉ", "0"]),
        ("MIL111", "Quân sự 1", "Môn Giáo dục quốc phòng MIL111 có bao nhiêu tín chỉ?", ["0 tín chỉ", "0"]),
    ]
    
    for idx, (code, name, q_txt, ans_exp) in enumerate(b04_courses, 1):
        b04_items.append({
            "q_id": f"V2_B04_{idx:03d}", "batch": "batch_04", "category": "course_deep",
            "session_id": f"v2_b04_sess_{idx:03d}", "turn_index": 1, "query": q_txt,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": "structured_lookup", "golden_answer": f"Thông tin môn {code} ({name})",
            "expected_answer_contains": ans_exp
        })

    # =========================================================================
    # BATCH 05: academic_regulations (50 câu quy chế đào tạo, xử lý học vụ)
    # =========================================================================
    b05_items = []
    reg_topics = [
        ("Sinh viên bị bao nhiêu lần cảnh báo học vụ thì bị buộc thôi học tại Đại học FPT?", ["buộc thôi học", "cảnh báo", "lần"]),
        ("Điều kiện để sinh viên được đăng ký học vượt là gì?", ["học vượt", "tín chỉ", "GPA"]),
        ("Điểm thi kết thúc môn EOS nếu dưới bao nhiêu điểm thì phải thi lại?", ["thi lại", "điểm", "EOS"]),
        ("Thời hạn nộp đơn xin phúc khảo bài thi sau khi có điểm là bao lâu?", ["phúc khảo", "ngày", "đơn"]),
        ("Sinh viên nghỉ học quá bao nhiêu % số buổi thì bị cấm thi?", ["cấm thi", "buổi", "%", "nghỉ học"]),
        ("Quy chế xử lý kỷ luật đối với sinh viên gian lận thi cử tại Đại học FPT?", ["kỷ luật", "đình chỉ", "gian lận"]),
        ("Thủ tục xin bảo lưu kết quả học tập cần chuẩn bị những giấy tờ gì?", ["bảo lưu", "đơn", "học kỳ"]),
        ("Thời gian bảo lưu học tập tối đa của sinh viên là bao lâu?", ["bảo lưu", "học kỳ", "năm"]),
        ("Sinh viên có được phép học cải thiện điểm đối với các môn đã qua không?", ["cải thiện", "học lại", "điểm"]),
        ("Điều kiện để sinh viên được chuyển ngành đào tạo là gì?", ["chuyển ngành", "xét", "học kỳ"]),
        ("Cách tính điểm trung bình chung học kỳ (GPA) và tích lũy (CPA)?", ["GPA", "CPA", "trung bình", "tín chỉ"]),
        ("Sinh viên nợ bao nhiêu tín chỉ thì bị xếp loại học lực yếu?", ["học lực", "yếu", "tín chỉ"]),
        ("Quy định về việc vắng thi có lý do chính đáng được xử lý như thế nào?", ["hoãn thi", "vắng thi", "lý do", "đơn"]),
        ("Lệ phí thi lại bài thi lý thuyết EOS được nộp qua kênh nào?", ["nộp", "lệ phí", "tài khoản"]),
        ("Quy định về việc công nhận chứng chỉ ngoại ngữ quốc tế để miễn học tiếng Anh?", ["miễn học", "IELTS", "TOEFL", "chứng chỉ"]),
        ("Thời gian tối đa để hoàn thành chương trình đào tạo đại học tại FPT?", ["thời gian", "năm", "tối đa", "đào tạo"]),
        ("Sinh viên có được đăng ký học 2 ngành cùng một lúc (song bằng) không?", ["song bằng", "hai ngành", "ngành"]),
        ("Trường hợp nào sinh viên bị đình chỉ học tập có thời hạn?", ["đình chỉ", "kỷ luật", "thời hạn"]),
        ("Quy định về việc cấp giấy xác nhận sinh viên để tạm hoãn nghĩa vụ quân sự?", ["nghĩa vụ quân sự", "xác nhận", "tạm hoãn"]),
        ("Sinh viên có được phép rút bớt môn học sau khi đã bắt đầu kỳ học không?", ["rút môn", "học phần", "hủy"]),
        ("Điều kiện để được xét nhận học bổng khuyến khích học tập từng kỳ?", ["học bổng", "GPA", "khuyến khích"]),
        ("Mức điểm rèn luyện được đánh giá theo những tiêu chí nào?", ["điểm rèn luyện", "hoạt động", "tiêu chí"]),
        ("Sinh viên có được xem lại bài thi tự luận hoặc thực hành không?", ["xem bài thi", "phúc khảo", "điểm"]),
        ("Quy chế đào tạo theo hệ thống tín chỉ của Bộ GD&ĐT áp dụng tại trường như thế nào?", ["tín chỉ", "quy chế", "đào tạo"]),
        ("Thủ tục xin thôi học tự nguyện cần nộp đơn cho phòng ban nào?", ["thôi học", "tự nguyện", "phòng đào tạo"])
    ]
    
    # 2 variants per topic = 50 questions
    for idx, (base_q, exp_kw) in enumerate(reg_topics, 1):
        q1 = base_q
        q2 = f"Cho tôi hỏi quy định cụ thể: {base_q[0].lower() + base_q[1:]}"
        b05_items.append({
            "q_id": f"V2_B05_{2*idx-1:03d}", "batch": "batch_05", "category": "academic_regulations",
            "session_id": f"v2_b05_sess_{2*idx-1:03d}", "turn_index": 1, "query": q1,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": "rag_pipeline", "golden_answer": "Quy chế học vụ ĐH FPT",
            "expected_answer_contains": exp_kw
        })
        b05_items.append({
            "q_id": f"V2_B05_{2*idx:03d}", "batch": "batch_05", "category": "academic_regulations",
            "session_id": f"v2_b05_sess_{2*idx:03d}", "turn_index": 1, "query": q2,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": "rag_pipeline", "golden_answer": "Quy chế học vụ ĐH FPT chi tiết",
            "expected_answer_contains": exp_kw
        })

    # =========================================================================
    # BATCH 06: tuition_campus_matrix (50 câu tra cứu ma trận học phí phân hiệu)
    # =========================================================================
    b06_items = []
    campus_queries = [
        ("Kỹ thuật phần mềm", "Hà Nội", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Trí tuệ nhân tạo", "Hà Nội", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("An toàn thông tin", "Hà Nội", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Quản trị kinh doanh", "Hà Nội", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Marketing", "Hà Nội", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Thiết kế mỹ thuật số", "Hà Nội", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Ngôn ngữ Anh", "Hà Nội", ["26.090.000", "26,090,000", "18.260.000", "18,260,000", "31.600.000", "31,600,000"]),
        ("Ngôn ngữ Nhật", "Hà Nội", ["26.090.000", "26,090,000", "18.260.000", "18,260,000", "31.600.000", "31,600,000"]),
        ("Ngôn ngữ Hàn Quốc", "Hà Nội", ["26.090.000", "26,090,000", "18.260.000", "18,260,000", "31.600.000", "31,600,000"]),
        ("Công nghệ thông tin", "TP. Hồ Chí Minh", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Kỹ thuật phần mềm", "TP. Hồ Chí Minh", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Trí tuệ nhân tạo", "TP. Hồ Chí Minh", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Quản trị kinh doanh", "TP. Hồ Chí Minh", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Marketing", "TP. Hồ Chí Minh", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Thiết kế đồ họa", "TP. Hồ Chí Minh", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"]),
        ("Kỹ thuật phần mềm", "Đà Nẵng", ["22.120.000", "22,120,000", "15.480.000", "15,480,000"]),
        ("Trí tuệ nhân tạo", "Đà Nẵng", ["22.120.000", "22,120,000", "15.480.000", "15,480,000"]),
        ("An toàn thông tin", "Đà Nẵng", ["22.120.000", "22,120,000", "15.480.000", "15,480,000"]),
        ("Quản trị kinh doanh", "Đà Nẵng", ["22.120.000", "22,120,000", "15.480.000", "15,480,000"]),
        ("Marketing", "Đà Nẵng", ["22.120.000", "22,120,000", "15.480.000", "15,480,000"]),
        ("Kỹ thuật phần mềm", "Cần Thơ", ["22.120.000", "22,120,000", "15.480.000", "15,480,000"]),
        ("Trí tuệ nhân tạo", "Cần Thơ", ["22.120.000", "22,120,000", "15.480.000", "15,480,000"]),
        ("Quản trị kinh doanh", "Cần Thơ", ["22.120.000", "22,120,000", "15.480.000", "15,480,000"]),
        ("Ngôn ngữ Anh", "Cần Thơ", ["22.120.000", "22,120,000", "15.480.000", "15,480,000"]),
        ("Kỹ thuật phần mềm", "Quy Nhơn", ["15.800.000", "15,800,000", "11.060.000", "11,060,000"]),
    ]
    for idx, (maj, camp, ans_exp) in enumerate(campus_queries, 1):
        q1 = f"Học phí ngành {maj} tại phân hiệu {camp} năm 2026 là bao nhiêu?"
        q2 = f"Mức thu học phí một kỳ ngành {maj} cơ sở {camp} khóa K22?"
        b06_items.append({
            "q_id": f"V2_B06_{2*idx-1:03d}", "batch": "batch_06", "category": "tuition_matrix",
            "session_id": f"v2_b06_sess_{2*idx-1:03d}", "turn_index": 1, "query": q1,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": "structured_lookup", "golden_answer": f"Học phí {maj} tại {camp}",
            "expected_answer_contains": ans_exp
        })
        b06_items.append({
            "q_id": f"V2_B06_{2*idx:03d}", "batch": "batch_06", "category": "tuition_matrix",
            "session_id": f"v2_b06_sess_{2*idx:03d}", "turn_index": 1, "query": q2,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": "structured_lookup", "golden_answer": f"Học phí {maj} tại {camp}",
            "expected_answer_contains": ans_exp
        })

    # =========================================================================
    # BATCH 07: graduation_ojt (50 câu OJT, điều kiện tốt nghiệp, chuẩn đầu ra)
    # =========================================================================
    b07_items = []
    grad_topics = [
        ("Sinh viên ngành CNTT cần đạt chứng chỉ tiếng Anh gì để được tốt nghiệp?", ["IELTS", "TOEFL", "VSTEP", "B2", "6.0"]),
        ("Chuẩn đầu ra ngoại ngữ của sinh viên ngành Quản trị kinh doanh là bao nhiêu?", ["IELTS", "TOEIC", "5.5", "600"]),
        ("Chuẩn đầu ra ngoại ngữ của ngành Ngôn ngữ Nhật là chứng chỉ gì?", ["JLPT", "N2"]),
        ("Chuẩn đầu ra ngoại ngữ của sinh viên ngành Ngôn ngữ Anh là gì?", ["IELTS", "7.0", "C1"]),
        ("Sinh viên đi thực tập doanh nghiệp OJT vào học kỳ thứ mấy?", ["kỳ 6", "6", "học kỳ 6"]),
        ("Thời gian thực tập OJT kéo dài trong bao lâu?", ["tháng", "kỳ", "học kỳ", "full-time"]),
        ("Học phí trong giai đoạn thực tập OJT tại doanh nghiệp tính như thế nào?", ["không phải đóng học phí chuyên ngành", "miễn học phí"]),
        ("Điều kiện về số tín chỉ tích lũy để được đi thực tập OJT là gì?", ["tín chỉ", "tiên quyết", "OJT"]),
        ("Lệ phí tốt nghiệp và cấp bằng đại học là bao nhiêu?", ["1.500.000", "1,500,000"]),
        ("Điểm trung bình tích lũy tối thiểu (GPA) để được xét tốt nghiệp là bao nhiêu?", ["2.0", "GPA"]),
        ("Sinh viên có bắt buộc phải hoàn thành chứng chỉ Giáo dục quốc phòng để tốt nghiệp không?", ["GDQP", "quân sự", "bắt buộc", "điều kiện"]),
        ("Chứng chỉ Giáo dục thể chất Vovinam có phải là điều kiện xét tốt nghiệp không?", ["Vovinam", "thể chất", "bắt buộc", "điều kiện"]),
        ("Đồ án tốt nghiệp ngành Kỹ thuật phần mềm thực hiện trong bao nhiêu học kỳ?", ["kỳ", "học kỳ", "đồ án"]),
        ("Sinh viên có thể chọn thi tốt nghiệp thay cho làm khóa luận tốt nghiệp không?", ["khóa luận", "thi tốt nghiệp", "QTKD"]),
        ("Doanh nghiệp thực tập OJT do nhà trường giới thiệu hay sinh viên tự liên hệ?", ["doanh nghiệp", "tự liên hệ", "nhà trường", "OJT"]),
        ("Sinh viên đi OJT ở nước ngoài cần đáp ứng những điều kiện gì?", ["nước ngoài", "tiếng Anh", "GPA", "OJT"]),
        ("Nếu không đạt kỳ thực tập OJT thì sinh viên phải làm gì?", ["thực tập lại", "OJT", "kỳ sau"]),
        ("Điều kiện để được bảo vệ đồ án tốt nghiệp khóa luận là gì?", ["bảo vệ", "đồ án", "tín chỉ", "GPA"]),
        ("Học kỳ OJT sinh viên có được đăng ký học thêm môn học khác không?", ["OJT", "học thêm", "môn học"]),
        ("Thời gian xét tốt nghiệp trong một năm có mấy đợt?", ["đợt", "xét tốt nghiệp", "năm"]),
        ("Bằng tốt nghiệp đại học của trường FPT do ai cấp?", ["Bộ GD&ĐT", "Đại học FPT", "Hiệu trưởng"]),
        ("Sinh viên tốt nghiệp loại xuất sắc cần đạt điểm GPA bao nhiêu?", ["3.6", "xuất sắc", "GPA"]),
        ("Sinh viên tốt nghiệp loại giỏi cần đạt GPA tối thiểu là bao nhiêu?", ["3.2", "giỏi", "GPA"]),
        ("Xếp loại tốt nghiệp có tính điểm rèn luyện không?", ["rèn luyện", "xếp loại", "học lực"]),
        ("Sinh viên chưa có chứng chỉ tiếng Anh có được hoãn nộp để nhận bằng không?", ["chứng chỉ", "hoãn", "bằng", "tiếng Anh"])
    ]
    for idx, (base_q, exp_kw) in enumerate(grad_topics, 1):
        q1 = base_q
        q2 = f"Quy định xét tốt nghiệp: {base_q[0].lower() + base_q[1:]}"
        route = "structured_lookup" if any(w in base_q.lower() for w in ["bao nhiêu", "lệ phí tốt nghiệp", "1.500.000", "giai đoạn thực tập ojt"]) else "rag_pipeline"
        b07_items.append({
            "q_id": f"V2_B07_{2*idx-1:03d}", "batch": "batch_07", "category": "graduation_ojt",
            "session_id": f"v2_b07_sess_{2*idx-1:03d}", "turn_index": 1, "query": q1,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": route, "golden_answer": "Quy định tốt nghiệp & OJT",
            "expected_answer_contains": exp_kw
        })
        b07_items.append({
            "q_id": f"V2_B07_{2*idx:03d}", "batch": "batch_07", "category": "graduation_ojt",
            "session_id": f"v2_b07_sess_{2*idx:03d}", "turn_index": 1, "query": q2,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": route, "golden_answer": "Quy định tốt nghiệp & OJT chi tiết",
            "expected_answer_contains": exp_kw
        })

    # =========================================================================
    # BATCH 08: common_administrative_fees (50 câu biểu phí hành chính & KTX)
    # =========================================================================
    b08_items = []
    fee_scenarios = [
        ("Lệ phí thi lại của trường Đại học FPT là bao nhiêu?", "structured_lookup", ["300.000", "300,000"]),
        ("Lệ phí học lại một tín chỉ tại Đại học FPT là bao nhiêu tiền?", "structured_lookup", ["650.000", "650,000"]),
        ("Phí ký túc xá phân hiệu Hòa Lạc thu bao nhiêu một học kỳ?", "structured_lookup", ["4.000.000", "4,000,000"]),
        ("Lệ phí công nhận tốt nghiệp và làm lễ cấp bằng là bao nhiêu?", "structured_lookup", ["1.500.000", "1,500,000"]),
        ("Phí cấp giấy xác nhận bảng điểm sinh viên là bao nhiêu?", "structured_lookup", ["50.000", "50,000"]),
        ("Học phí kỳ định hướng đầu khóa (orientation) có thu tiền không?", "structured_lookup", ["0", "miễn phí", "không thu"]),
        ("Chính sách ưu đãi học phí phân hiệu Cần Thơ được hỗ trợ bao nhiêu %?", "structured_lookup", ["30%", "30"]),
        ("Chính sách ưu đãi học phí phân hiệu Đà Nẵng được giảm bao nhiêu phần trăm?", "structured_lookup", ["30%", "30"]),
        ("Chính sách ưu đãi học phí tại phân hiệu Quy Nhơn là bao nhiêu?", "structured_lookup", ["50%", "50"]),
        ("Phí ký túc xá khóa K17 là bao nhiêu tiền một kỳ?", "structured_lookup", ["3.600.000", "3,600,000"]),
        ("Phí ký túc xá sinh viên khóa K18 tại Hòa Lạc là bao nhiêu?", "structured_lookup", ["3.800.000", "3,800,000"]),
        ("Mức phí ký túc xá sinh viên khóa K19 là bao nhiêu một học kỳ?", "structured_lookup", ["4.000.000", "4,000,000", "3.800.000", "3,800,000"]),
        ("Ký túc xá khóa K20 tại Hòa Lạc có giá bao nhiêu?", "structured_lookup", ["4.000.000", "4,000,000"]),
        ("Phí ký túc xá của khóa K21 là bao nhiêu tiền một kỳ?", "structured_lookup", ["4.200.000", "4,200,000"]),
        ("Ký túc xá khóa K22 thu bao nhiêu tiền một kỳ?", "structured_lookup", ["4.500.000", "4,500,000"]),
        ("Lệ phí thi lại của khóa K21 là bao nhiêu tiền một lần thi?", "structured_lookup", ["350.000", "350,000"]),
        ("Lệ phí thi lại khóa K22 quy định là bao nhiêu?", "structured_lookup", ["350.000", "350,000"]),
        ("Lệ phí học lại một tín chỉ khóa K21 là bao nhiêu tiền?", "structured_lookup", ["700.000", "700,000"]),
        ("Lệ phí học lại một tín chỉ khóa K22 là bao nhiêu?", "structured_lookup", ["750.000", "750,000"]),
        ("Lệ phí học lại một tín chỉ của sinh viên khóa K17?", "structured_lookup", ["600.000", "600,000"]),
        ("Lệ phí thi lại của sinh viên khóa K18 là bao nhiêu?", "structured_lookup", ["300.000", "300,000"]),
        ("Lệ phí thi lại của khóa K19 quy định bao nhiêu tiền?", "structured_lookup", ["300.000", "300,000"]),
        ("Lệ phí thi lại của khóa K20 là bao nhiêu?", "structured_lookup", ["300.000", "300,000"]),
        ("Học phí tiếng Anh dự bị khóa K20 là bao nhiêu một mức?", "structured_lookup", ["11.300.000", "11,300,000"]),
        ("Học phí tiếng Anh chuẩn bị khóa K22 là bao nhiêu tiền một mức?", "structured_lookup", ["11.900.000", "11,900,000"])
    ]
    for idx, (base_q, route, exp_ans) in enumerate(fee_scenarios, 1):
        q1 = base_q
        q2 = f"Nhà trường cho hỏi: {base_q[0].lower() + base_q[1:]}"
        b08_items.append({
            "q_id": f"V2_B08_{2*idx-1:03d}", "batch": "batch_08", "category": "common_fees",
            "session_id": f"v2_b08_sess_{2*idx-1:03d}", "turn_index": 1, "query": q1,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": route, "golden_answer": "Biểu phí quy định ĐH FPT",
            "expected_answer_contains": exp_ans
        })
        b08_items.append({
            "q_id": f"V2_B08_{2*idx:03d}", "batch": "batch_08", "category": "common_fees",
            "session_id": f"v2_b08_sess_{2*idx:03d}", "turn_index": 1, "query": q2,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": route, "golden_answer": "Biểu phí quy định ĐH FPT",
            "expected_answer_contains": exp_ans
        })

    # =========================================================================
    # BATCH 09: multi_turn_3turn (16 sessions x 3 turns + 2 single = 50 câu)
    # Kiểm tra hội thoại 3 lượt sâu (Turn 3 kế thừa Turn 2 và Turn 1)
    # =========================================================================
    b09_items = []
    three_turn_scenarios = [
        ("Học phí ngành Kỹ thuật phần mềm tại Hà Nội là bao nhiêu?", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"],
         "Còn ở phân hiệu Cần Thơ thì thế nào?", ["Kỹ thuật phần mềm", "Cần Thơ"], ["22.120.000", "22,120,000", "15.480.000", "15,480,000"],
         "Phân hiệu này được hỗ trợ ưu đãi bao nhiêu phần trăm?", ["Cần Thơ"], ["30%", "30"]),
        ("Môn Học máy AIL302m học những gì?", ["Machine Learning", "học máy", "hồi quy", "phân lớp"],
         "Môn này có bao nhiêu tín chỉ?", ["AIL302m"], ["3 tín chỉ", "3"],
         "Giáo trình chính môn này tên là sách gì?", ["AIL302m"], ["Mitchell", "Machine Learning"]),
        ("Học phí chuyên ngành của sinh viên khóa K21 là bao nhiêu?", ["31.200.000", "31,200,000", "30.500.000", "30,500,000"],
         "Còn lệ phí thi lại một lần của khóa này?", ["K21"], ["350.000", "350,000"],
         "Vậy tiền ký túc xá mỗi kỳ của khóa đó là bao nhiêu?", ["K21"], ["4.200.000", "4,200,000"]),
        ("Môn Mạng máy tính NWC203c có môn tiên quyết là gì?", ["CSI104", "tiên quyết", "không"],
         "Môn đó có mấy tín chỉ?", ["NWC203c"], ["3 tín chỉ", "3"],
         "Học vào học kỳ thứ mấy trong chương trình?", ["NWC203c"], ["kỳ 3", "3", "kỳ 4", "4"]),
        ("Học phí ngành Trí tuệ nhân tạo tại TP.HCM là bao nhiêu?", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"],
         "Nếu học ngành này ở Quy Nhơn thì thu bao nhiêu?", ["Trí tuệ nhân tạo", "Quy Nhơn"], ["15.800.000", "15,800,000", "11.060.000", "11,060,000"],
         "Mức ưu đãi học phí tại Quy Nhơn được bao nhiêu %?", ["Quy Nhơn"], ["50%", "50"]),
        ("Môn Lập trình Java Web PRJ301 có mấy tín chỉ?", ["3 tín chỉ", "3"],
         "Môn này cần học qua những môn tiên quyết nào?", ["PRJ301"], ["PRO192", "CSD201", "DBI202"],
         "Hình thức đánh giá môn học gồm những gì?", ["PRJ301"], ["PE", "thực hành", "Lab"]),
        ("Khóa K22 đóng học phí chuyên ngành bao nhiêu một kỳ?", ["32.500.000", "32,500,000"],
         "Còn tiền học tiếng Anh chuẩn bị mỗi mức?", ["K22"], ["11.900.000", "11,900,000"],
         "Tiền ký túc xá một kỳ là bao nhiêu?", ["K22"], ["4.500.000", "4,500,000"]),
        ("Môn Hệ điều hành OSG202 học những nội dung gì?", ["hệ điều hành", "tiến trình", "bộ nhớ"],
         "Môn này gồm bao nhiêu tín chỉ?", ["OSG202"], ["3 tín chỉ", "3"],
         "Giáo trình chính môn này là sách nào?", ["OSG202"], ["Operating System", "Silberschatz"]),
        ("Mức học phí chuyên ngành Quản trị kinh doanh tại campus Hà Nội là bao nhiêu?", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"],
         "Còn ở Đà Nẵng mức học phí ngành này là bao nhiêu?", ["Quản trị kinh doanh", "Đà Nẵng"], ["22.120.000", "22,120,000", "15.480.000", "15,480,000"],
         "Phân hiệu này được giảm bao nhiêu phần trăm học phí?", ["Đà Nẵng"], ["30%", "30"]),
        ("Khóa K18 có học phí chuyên ngành là bao nhiêu?", ["27.300.000", "27,300,000", "25.300.000", "25,300,000"],
         "Lệ phí thi lại của khóa đó là bao nhiêu một lần?", ["K18"], ["300.000", "300,000"],
         "Tiền ở ký túc xá mỗi học kỳ của khóa này là bao nhiêu?", ["K18"], ["3.800.000", "3,800,000"]),
        ("Môn Kiểm thử phần mềm SWT301 học những gì?", ["kiểm thử", "test", "automation", "unit test"],
         "Số lượng tín chỉ quy định cho môn học này là bao nhiêu?", ["SWT301"], ["3 tín chỉ", "3"],
         "Môn tiên quyết của môn này là môn nào?", ["SWT301"], ["SWE201c", "tiên quyết"]),
        ("Học phí ngành An toàn thông tin tại Hà Nội?", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"],
         "Còn ở phân hiệu Cần Thơ thu bao nhiêu?", ["An toàn thông tin", "Cần Thơ"], ["22.120.000", "22,120,000", "15.480.000", "15,480,000"],
         "Chính sách ưu đãi phân hiệu Cần Thơ là bao nhiêu %?", ["Cần Thơ"], ["30%", "30"]),
        ("Môn Mật mã học CRY301 có bao nhiêu tín chỉ?", ["3 tín chỉ", "3"],
         "Giáo trình chính môn này là cuốn sách gì?", ["CRY301"], ["Cryptography", "Network Security", "Stallings"],
         "Nội dung trọng tâm môn này giảng dạy về cái gì?", ["CRY301"], ["mật mã", "mã hóa", "khóa", "RSA", "AES"]),
        ("Mức thu học phí một kỳ chuyên ngành đối với sinh viên khóa K20?", ["28.700.000", "28,700,000"],
         "Tiền học lại một tín chỉ của khóa này là bao nhiêu?", ["K20"], ["650.000", "650,000"],
         "Còn phí ký túc xá tại Hòa Lạc mỗi học kỳ?", ["K20"], ["4.000.000", "4,000,000"]),
        ("Môn Xử lý ngôn ngữ tự nhiên NLP301c có mấy tín chỉ?", ["3 tín chỉ", "3"],
         "Môn này có cần học qua môn Học máy không?", ["NLP301c"], ["AIL302m", "tiên quyết"],
         "Môn này học về những mô hình ngôn ngữ nào?", ["NLP301c"], ["transformer", "bert", "ngôn ngữ", "text"]),
        ("Học phí ngành Marketing tại Hà Nội năm 2026 là bao nhiêu?", ["31.600.000", "31,600,000", "22.120.000", "22,120,000"],
         "Nếu chuyển vào học ở phân hiệu Đà Nẵng thì mức thu bao nhiêu?", ["Marketing", "Đà Nẵng"], ["22.120.000", "22,120,000", "15.480.000", "15,480,000"],
         "Mức hỗ trợ ưu đãi tại Đà Nẵng là bao nhiêu phần trăm?", ["Đà Nẵng"], ["30%", "30"])
    ]
    
    cnt_q = 0
    for idx, (t1, a1, t2, r2, a2, t3, r3, a3) in enumerate(three_turn_scenarios, 1):
        s_id = f"v2_b09_sess_{idx:03d}"
        cnt_q += 1
        b09_items.append({
            "q_id": f"V2_B09_{cnt_q:03d}", "batch": "batch_09", "category": "multi_turn_3turn",
            "session_id": s_id, "turn_index": 1, "query": t1, "is_continuation": False,
            "expected_rewrite_contains": [], "is_topic_switch": False, "expected_route": "structured_lookup",
            "golden_answer": "Lượt 1 hội thoại", "expected_answer_contains": a1
        })
        cnt_q += 1
        b09_items.append({
            "q_id": f"V2_B09_{cnt_q:03d}", "batch": "batch_09", "category": "multi_turn_3turn",
            "session_id": s_id, "turn_index": 2, "query": t2, "is_continuation": True,
            "expected_rewrite_contains": r2, "is_topic_switch": False, "expected_route": "structured_lookup",
            "golden_answer": "Lượt 2 hội thoại kế thừa Lượt 1", "expected_answer_contains": a2
        })
        cnt_q += 1
        b09_items.append({
            "q_id": f"V2_B09_{cnt_q:03d}", "batch": "batch_09", "category": "multi_turn_3turn",
            "session_id": s_id, "turn_index": 3, "query": t3, "is_continuation": True,
            "expected_rewrite_contains": r3, "is_topic_switch": False, "expected_route": "structured_lookup",
            "golden_answer": "Lượt 3 hội thoại kế thừa Lượt 2 và Lượt 1", "expected_answer_contains": a3
        })
        
    # 16 x 3 = 48 câu. Thêm 2 câu độc lập để tròn 50 câu:
    cnt_q += 1
    b09_items.append({
        "q_id": f"V2_B09_{cnt_q:03d}", "batch": "batch_09", "category": "multi_turn_3turn",
        "session_id": f"v2_b09_sess_extra_01", "turn_index": 1, "query": "Lệ phí công nhận tốt nghiệp và cấp bằng là bao nhiêu?",
        "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False, "expected_route": "structured_lookup",
        "golden_answer": "Lệ phí tốt nghiệp", "expected_answer_contains": ["1.500.000", "1,500,000"]
    })
    cnt_q += 1
    b09_items.append({
        "q_id": f"V2_B09_{cnt_q:03d}", "batch": "batch_09", "category": "multi_turn_3turn",
        "session_id": f"v2_b09_sess_extra_02", "turn_index": 1, "query": "Phí cấp bảng điểm xác nhận sinh viên là bao nhiêu?",
        "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False, "expected_route": "structured_lookup",
        "golden_answer": "Phí bảng điểm", "expected_answer_contains": ["50.000", "50,000"]
    })

    # =========================================================================
    # BATCH 10: ood_and_stress (50 câu hỏi ngoài phạm vi học vụ)
    # =========================================================================
    b10_items = []
    ood_queries = [
        "Cách nấu món bún bò Huế thơm ngon chuẩn vị miền Trung?",
        "Giá vàng miếng SJC hôm nay tăng hay giảm bao nhiêu triệu đồng?",
        "Dự báo thời tiết Hà Nội và TP.HCM ngày mai có mưa không?",
        "Cách nạp thẻ và mua trang phục trong game Liên Quân Mobile?",
        "Bộ phim điện ảnh Avatar phần 2 đạt doanh thu bao nhiêu tỷ USD?",
        "Đội tuyển bóng đá nào vô địch World Cup 2022 tại Qatar?",
        "Giá cổ phiếu VinFast hôm nay trên sàn chứng khoán Mỹ là bao nhiêu?",
        "Cách làm bánh mì chảo pate trứng thơm ngon tại nhà?",
        "Lời bài hát Em của ngày hôm qua của ca sĩ Sơn Tùng?",
        "Thủ đô của nước Canada là thành phố nào?",
        "Giá bán xe ô tô VinFast VF8 hiện nay là bao nhiêu tiền?",
        "Cách mua vé máy bay giá rẻ đi du lịch Đà Nẵng mùa hè?",
        "Quán cà phê view đẹp chụp ảnh sống ảo tại Hà Nội?",
        "Tử vi 12 con giáp tuần này con giáp nào gặp nhiều may mắn?",
        "Cách trị mụn bọc và chăm sóc da mặt dầu tại nhà hiệu quả?",
        "Bộ phim Tây Du Ký phiên bản 1986 có bao nhiêu tập tất cả?",
        "Cầu thủ Cristiano Ronaldo hiện đang thi đấu cho câu lạc bộ bóng đá nào?",
        "Giá điện thoại iPhone 16 Pro Max 256GB chính hãng tại Việt Nam?",
        "Cách pha một ly trà sữa thái xanh trân châu thơm ngon?",
        "Top những địa điểm du lịch nổi tiếng nhất tại thành phố Đà Lạt?",
        "Cách làm món phở bò gia truyền chuẩn vị phố cổ?",
        "Thị trường tiền điện tử Bitcoin hôm nay tăng hay giảm?",
        "Phim Lật Mặt 7 của đạo diễn Lý Hải có doanh thu bao nhiêu?",
        "Ai là người đầu tiên đặt chân lên Mặt Trăng?",
        "Cách đăng ký tài khoản Netflix để xem phim bom tấn?",
        "Giá xăng RON 95 tuần này tăng hay giảm bao nhiêu đồng?",
        "Cách làm món nem rán truyền thống cho dịp lễ tết?",
        "Quốc gia nào có diện tích lãnh thổ lớn nhất thế giới?",
        "Cách tập gym giảm mỡ bụng cho người mới bắt đầu?",
        "Mẹo tiết kiệm pin cho điện thoại smartphone chạy Android?",
        "Bài hát Despacito đạt bao nhiêu tỷ lượt xem trên YouTube?",
        "Cách nấu món canh chua cá lóc miền Tây chuẩn vị?",
        "Cách trồng và chăm sóc cây hoa hồng ra nhiều hoa?",
        "Đồng tiền chung của các quốc gia châu Âu tên là gì?",
        "Cách sửa lỗi mất kết nối mạng wifi trên máy tính laptop?",
        "Công thức làm trà đào cam sả thanh nhiệt mùa hè?",
        "Cách xem bảng xếp hạng bóng đá Ngoại Hạng Anh hôm nay?",
        "Bộ truyện tranh Doraemon của tác giả người Nhật nào?",
        "Cách làm sốt chấm muối ớt xanh chấm hải sản?",
        "Tập đoàn công nghệ Apple do ai sáng lập ra?",
        "Cách nướng thịt ba chỉ bằng nồi chiên không dầu giòn rụm?",
        "Kinh nghiệm đi du lịch Sapa 3 ngày 2 đêm tự túc?",
        "Bài thơ Sóng của nhà thơ Xuân Quỳnh viết năm nào?",
        "Ai là cầu thủ bóng đá đạt nhiều Quả bóng vàng nhất lịch sử?",
        "Cách làm sữa chua nếp cẩm tráng miệng đơn giản tại nhà?",
        "Hành tinh nào gần Mặt Trời nhất trong Hệ Mặt Trời?",
        "Cách chọn mua máy ảnh du lịch gọn nhẹ cho người mới?",
        "Đỉnh núi Phan Xi Păng có độ cao bao nhiêu mét?",
        "Cách pha nước chấm ốc bươu xả ớt ngon tuyệt đỉnh?",
        "Tác phẩm văn học Tắt Đèn của nhà văn Ngô Tất Tố xuất bản năm nào?"
    ]
    for idx, q_txt in enumerate(ood_queries, 1):
        b10_items.append({
            "q_id": f"V2_B10_{idx:03d}", "batch": "batch_10", "category": "ood",
            "session_id": f"v2_b10_sess_{idx:03d}", "turn_index": 1, "query": q_txt,
            "is_continuation": False, "expected_rewrite_contains": [], "is_topic_switch": False,
            "expected_route": "ood", "golden_answer": "Câu hỏi ngoài phạm vi học vụ",
            "expected_answer_contains": ["ngoài phạm vi"]
        })

    batches = {
        "batch_01": b01_items,
        "batch_02": b02_items,
        "batch_03": b03_items,
        "batch_04": b04_items,
        "batch_05": b05_items,
        "batch_06": b06_items,
        "batch_07": b07_items,
        "batch_08": b08_items,
        "batch_09": b09_items,
        "batch_10": b10_items,
    }

    # Deduplication and verification
    overlap_with_v1 = 0
    total_written = 0

    for b_name, items in batches.items():
        assert len(items) == 50, f"{b_name} has {len(items)} items instead of 50!"
        fpath = os.path.join(out_dir, f"{b_name}.jsonl")
        with open(fpath, "w", encoding="utf-8") as f:
            for it in items:
                h = text_hash(it["query"])
                if h in v1_hashes:
                    overlap_with_v1 += 1
                all_v2_hashes.add(h)
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
                total_written += 1
        print(f"  ✓ {b_name}.jsonl generated: {len(items)} questions")

    print("\n" + "=" * 60)
    print("           TỔNG KẾT BỘ DỮ LIỆU BENCHMARK V2 (500 CÂU)")
    print("=" * 60)
    print(f"Tổng số câu hỏi sinh ra : {total_written}")
    print(f"Số câu hỏi duy nhất (v2): {len(all_v2_hashes)}")
    print(f"Trùng lặp với bộ v1 cũ  : {overlap_with_v1} câu (Mục tiêu: 0 câu)")
    print(f"Tất cả 10 batches lưu tại: {out_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()
