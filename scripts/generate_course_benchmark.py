"""Script sinh bộ câu hỏi benchmark 100 câu hỏi chuyên sâu theo mã môn học của từng ngành tại Đại học FPT.
Dữ liệu nguồn: data/processed/structured_data_courses.json (Curriculum Knowledge Base).
Xuất ra: data/evaluation/benchmark_courses_100.jsonl
"""

import json
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
courses_json_path = _project_root / "data" / "processed" / "structured_data_courses.json"
output_path = _project_root / "data" / "evaluation" / "benchmark_courses_100.jsonl"

with open(courses_json_path, "r", encoding="utf-8") as f:
    ckb = json.load(f)

courses_map = {c["course_code"]: c for c in ckb["courses"]}

questions = []
q_idx = 1


def add_q(level, category, session_id, turn_index, query, expected_route, expected_doc_ids, golden_answer, dialogue_context=None):
    global q_idx
    q_id = f"QC{q_idx:03d}"
    q_idx += 1
    questions.append({
        "q_id": q_id,
        "difficulty_level": level,
        "category": category,
        "session_id": session_id,
        "turn_index": turn_index,
        "dialogue_context": dialogue_context or [],
        "query": query,
        "expected_route": expected_route,
        "expected_doc_ids": expected_doc_ids,
        "golden_answer": golden_answer,
    })


# ==============================================================================
# PHẦN 1: TIÊN QUYẾT CÁC MÔN CÔNG NGHỆ THÔNG TIN (KTPM, AI, ATTT, CS, IS)
# ==============================================================================
add_q(1, "course_prerequisite", "sess_c_01", 1, "Môn PRF192 của ngành Kỹ thuật phần mềm có yêu cầu môn tiên quyết nào không?", "structured_lookup", ["structured_data_courses"], "Môn PRF192 (Cơ sở lập trình C) không yêu cầu môn học tiên quyết nào.")
add_q(1, "course_prerequisite", "sess_c_02", 1, "Môn PRO192 (Lập trình hướng đối tượng với Java) yêu cầu phải qua môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn PRO192 (Lập trình hướng đối tượng với Java) yêu cầu môn tiên quyết bắt buộc là: PRF192.")
add_q(1, "course_prerequisite", "sess_c_03", 1, "Điều kiện tiên quyết để được học môn CSD201 (Cấu trúc dữ liệu và giải thuật) là gì?", "structured_lookup", ["structured_data_courses"], "Môn CSD201 (Cấu trúc dữ liệu và giải thuật) yêu cầu môn tiên quyết bắt buộc là: PRO192.")
add_q(1, "course_prerequisite", "sess_c_04", 1, "Môn PRJ301 (Lập trình Web với Java) cần học xong những môn nào trước?", "structured_lookup", ["structured_data_courses"], "Môn PRJ301 (Lập trình Web với Java) yêu cầu môn tiên quyết bắt buộc là: PRO192, DBI202.")
add_q(1, "course_prerequisite", "sess_c_05", 1, "Để đăng ký môn PRN211 (Lập trình .NET) sinh viên KTPM cần qua môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn PRN211 (Lập trình ứng dụng đa nền tảng với .NET) yêu cầu môn tiên quyết bắt buộc là: PRO192.")
add_q(1, "course_prerequisite", "sess_c_06", 1, "Môn dự án phần mềm SWP391 yêu cầu điều kiện môn tiên quyết là các môn nào?", "structured_lookup", ["structured_data_courses"], "Môn SWP391 (Dự án phát triển ứng dụng phần mềm) yêu cầu môn tiên quyết bắt buộc là: SWE201c, PRJ301.")
add_q(1, "course_prerequisite", "sess_c_07", 1, "Môn Kiến trúc và thiết kế phần mềm SWD392 yêu cầu qua môn nào?", "structured_lookup", ["structured_data_courses"], "Môn SWD392 (Kiến trúc và thiết kế phần mềm) yêu cầu môn tiên quyết bắt buộc là: SWP391.")
add_q(1, "course_prerequisite", "sess_c_08", 1, "Điều kiện tiên quyết để sinh viên ngành KTPM được làm đồ án tốt nghiệp SEP490 là gì?", "structured_lookup", ["structured_data_courses"], "Môn SEP490 (Khóa luận tốt nghiệp Kỹ thuật phần mềm) yêu cầu môn tiên quyết bắt buộc là: SWP391, SWD392.")
add_q(1, "course_prerequisite", "sess_c_09", 1, "Môn Học máy AIL302m của ngành Trí tuệ nhân tạo có môn tiên quyết là gì?", "structured_lookup", ["structured_data_courses"], "Môn AIL302m (Học máy) yêu cầu môn tiên quyết bắt buộc là: MAS291, PRO192.")
add_q(1, "course_prerequisite", "sess_c_10", 1, "Môn Xử lý ngôn ngữ tự nhiên NLP301c yêu cầu học qua môn nào trước?", "structured_lookup", ["structured_data_courses"], "Môn NLP301c (Xử lý ngôn ngữ tự nhiên) yêu cầu môn tiên quyết bắt buộc là: AIL302m.")
add_q(1, "course_prerequisite", "sess_c_11", 1, "Môn Thị giác máy tính CVL301c của ngành AI cần môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn CVL301c (Thị giác máy tính) yêu cầu môn tiên quyết bắt buộc là: AIL302m.")
add_q(1, "course_prerequisite", "sess_c_12", 1, "Môn Học sâu DLG301 yêu cầu sinh viên AI phải hoàn thành môn nào?", "structured_lookup", ["structured_data_courses"], "Môn DLG301 (Học sâu) yêu cầu môn tiên quyết bắt buộc là: AIL302m.")
add_q(1, "course_prerequisite", "sess_c_13", 1, "Khóa luận tốt nghiệp ngành AI mã môn AIP490 có môn tiên quyết là gì?", "structured_lookup", ["structured_data_courses"], "Môn AIP490 (Khóa luận tốt nghiệp Trí tuệ nhân tạo) yêu cầu môn tiên quyết bắt buộc là: AIP391, DLG301.")
add_q(1, "course_prerequisite", "sess_c_14", 1, "Môn Mật mã học CRY301 của ngành An toàn thông tin yêu cầu môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn CRY301 (Mật mã học) yêu cầu môn tiên quyết bắt buộc là: MAD101.")
add_q(1, "course_prerequisite", "sess_c_15", 1, "Môn An toàn hệ thống và mạng IAL201 cần học xong các môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn IAL201 (An toàn hệ thống và mạng) yêu cầu môn tiên quyết bắt buộc là: NWC203c, OSG202.")

# ==============================================================================
# PHẦN 1.5: NỘI DUNG MÔN HỌC (SYLLABUS) VÀ GIÁO TRÌNH (TEXTBOOK) CHUYÊN SÂU
# ==============================================================================
from FPTUniQA.data.structured import StructuredDataParser
_dbp = StructuredDataParser()

add_q(2, "course_syllabus", "sess_c_s01", 1, "Môn PRF192 học những gì?", "structured_lookup", ["structured_data_courses"], _dbp.format_course_answer("PRF192", aspect="syllabus"))
add_q(2, "course_textbook", "sess_c_t01", 1, "Giáo trình môn PRO192 là sách nào?", "structured_lookup", ["structured_data_courses"], _dbp.format_course_answer("PRO192", aspect="textbook"))
add_q(2, "course_syllabus", "sess_c_s02", 1, "Môn CSD201 học về những nội dung gì?", "structured_lookup", ["structured_data_courses"], _dbp.format_course_answer("CSD201", aspect="syllabus"))
add_q(2, "course_syllabus", "sess_c_s03", 1, "Môn DBI202 học những gì?", "structured_lookup", ["structured_data_courses"], _dbp.format_course_answer("DBI202", aspect="syllabus"))
add_q(2, "course_textbook", "sess_c_t02", 1, "Giáo trình môn MKT101 của ai viết?", "structured_lookup", ["structured_data_courses"], _dbp.format_course_answer("MKT101", aspect="textbook"))
add_q(2, "course_syllabus", "sess_c_s04", 1, "Môn Học máy AIL302m học những nội dung kiến thức gì?", "structured_lookup", ["structured_data_courses"], _dbp.format_course_answer("AIL302m", aspect="syllabus"))
add_q(2, "course_textbook", "sess_c_t03", 1, "Giáo trình môn Mật mã học CRY301 dùng sách của tác giả nào?", "structured_lookup", ["structured_data_courses"], _dbp.format_course_answer("CRY301", aspect="textbook"))
add_q(2, "course_syllabus", "sess_c_s05", 1, "Môn Võ Vovinam 1 VOV114 học những gì?", "structured_lookup", ["structured_data_courses"], _dbp.format_course_answer("VOV114", aspect="syllabus"))
add_q(2, "course_textbook", "sess_c_t04", 1, "Giáo trình môn Lập trình Web Java PRJ301 là tài liệu nào?", "structured_lookup", ["structured_data_courses"], _dbp.format_course_answer("PRJ301", aspect="textbook"))
add_q(2, "course_syllabus", "sess_c_s06", 1, "Môn Thiết kế đồ họa Photoshop DGT101 học những nội dung gì?", "structured_lookup", ["structured_data_courses"], _dbp.format_course_answer("DGT101", aspect="syllabus"))

# ==============================================================================
# PHẦN 2: MÔN TIÊN QUYẾT KHỐI KINH TẾ, THIẾT KẾ & NGÔN NGỮ
# ==============================================================================
add_q(2, "course_prerequisite", "sess_c_21", 1, "Môn Kinh tế vĩ mô ECO121 yêu cầu môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn ECO121 (Kinh tế vĩ mô) yêu cầu môn tiên quyết bắt buộc là: ECO111.")
add_q(2, "course_prerequisite", "sess_c_22", 1, "Môn Tài chính doanh nghiệp FIN202 cần hoàn thành môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn FIN202 (Tài chính doanh nghiệp) yêu cầu môn tiên quyết bắt buộc là: ACC101.")
add_q(2, "course_prerequisite", "sess_c_23", 1, "Môn Hành vi tổ chức OBE102 yêu cầu qua môn quản trị nào trước?", "structured_lookup", ["structured_data_courses"], "Môn OBE102 (Hành vi tổ chức) yêu cầu môn tiên quyết bắt buộc là: MGT103.")
add_q(2, "course_prerequisite", "sess_c_24", 1, "Môn Dự án thực tế Marketing MKP391 có môn tiên quyết là gì?", "structured_lookup", ["structured_data_courses"], "Môn MKP391 (Dự án thực tế Marketing) yêu cầu môn tiên quyết bắt buộc là: MKT101.")
add_q(2, "course_prerequisite", "sess_c_25", 1, "Đồ án tốt nghiệp ngành Quản trị kinh doanh BAP490 yêu cầu tiên quyết những môn nào?", "structured_lookup", ["structured_data_courses"], "Môn BAP490 (Khóa luận tốt nghiệp Quản trị kinh doanh) yêu cầu môn tiên quyết bắt buộc là: FIN202, OBE102.")
add_q(2, "course_prerequisite", "sess_c_26", 1, "Môn Nghệ thuật thị giác VWS101 ngành Thiết kế đồ họa cần qua môn nào?", "structured_lookup", ["structured_data_courses"], "Môn VWS101 (Nghệ thuật thị giác) yêu cầu môn tiên quyết bắt buộc là: DGT101.")
add_q(2, "course_prerequisite", "sess_c_27", 1, "Môn Thiết kế đồ họa 2D GRA201 có môn tiên quyết là môn nào?", "structured_lookup", ["structured_data_courses"], "Môn GRA201 (Thiết kế đồ họa 2D) yêu cầu môn tiên quyết bắt buộc là: VWS101.")
add_q(2, "course_prerequisite", "sess_c_28", 1, "Môn Nghệ thuật chữ TYP201 yêu cầu sinh viên thiết kế đồ họa qua môn nào?", "structured_lookup", ["structured_data_courses"], "Môn TYP201 (Nghệ thuật chữ) yêu cầu môn tiên quyết bắt buộc là: GRA201.")
add_q(2, "course_prerequisite", "sess_c_29", 1, "Đồ án tốt nghiệp ngành Thiết kế đồ họa GDP490 cần qua môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn GDP490 (Đồ án tốt nghiệp Thiết kế Mỹ thuật số) yêu cầu môn tiên quyết bắt buộc là: TYP201, ANM301.")
add_q(2, "course_prerequisite", "sess_c_30", 1, "Môn Tiếng Anh học thuật 2 ENG102 yêu cầu qua môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn ENG102 (Tiếng Anh học thuật 2) yêu cầu môn tiên quyết bắt buộc là: ENG101.")
add_q(2, "course_prerequisite", "sess_c_34", 1, "Khóa luận tốt nghiệp Ngôn ngữ Nhật JAP490 yêu cầu tiên quyết môn nào?", "structured_lookup", ["structured_data_courses"], "Môn JAP490 (Khóa luận tốt nghiệp Ngôn ngữ Nhật) yêu cầu môn tiên quyết bắt buộc là: JIT301.")
add_q(2, "course_prerequisite", "sess_c_35", 1, "Môn Vovinam 2 mã môn VOV124 yêu cầu phải qua môn nào?", "structured_lookup", ["structured_data_courses"], "Môn VOV124 (Võ Vovinam 2) yêu cầu môn tiên quyết bắt buộc là: VOV114.")

# ==============================================================================
# PHẦN 3: SỐ TÍN CHỈ VÀ HỌC KỲ CỦA CÁC MÃ MÔN HỌC
# ==============================================================================
add_q(3, "course_credits_semester", "sess_c_39", 1, "Môn SEP490 (Khóa luận tốt nghiệp KTPM) có khối lượng bao nhiêu tín chỉ?", "structured_lookup", ["structured_data_courses"], "Môn SEP490 (Khóa luận tốt nghiệp Kỹ thuật phần mềm) có khối lượng đào tạo là 10 tín chỉ (được bố trí ở học kỳ 9, thuộc ngành Kỹ thuật phần mềm).")
add_q(3, "course_credits_semester", "sess_c_40", 1, "Môn AIP490 (Khóa luận tốt nghiệp ngành AI) bao nhiêu tín chỉ và học ở kỳ mấy?", "structured_lookup", ["structured_data_courses"], "Môn AIP490 (Khóa luận tốt nghiệp Trí tuệ nhân tạo) có khối lượng đào tạo là 10 tín chỉ (được bố trí ở học kỳ 9, thuộc ngành Trí tuệ nhân tạo).")
add_q(3, "course_credits_semester", "sess_c_41", 1, "Khóa luận tốt nghiệp ngành An toàn thông tin IAP490 có mấy tín chỉ?", "structured_lookup", ["structured_data_courses"], "Môn IAP490 (Khóa luận tốt nghiệp An toàn thông tin) có khối lượng đào tạo là 10 tín chỉ (được bố trí ở học kỳ 9, thuộc ngành An toàn thông tin).")
add_q(3, "course_credits_semester", "sess_c_42", 1, "Khóa luận tốt nghiệp ngành Quản trị kinh doanh BAP490 bao nhiêu tín chỉ?", "structured_lookup", ["structured_data_courses"], "Môn BAP490 (Khóa luận tốt nghiệp Quản trị kinh doanh) có khối lượng đào tạo là 10 tín chỉ (được bố trí ở học kỳ 9, thuộc ngành Quản trị kinh doanh).")
add_q(3, "course_credits_semester", "sess_c_43", 1, "Đồ án tốt nghiệp ngành Thiết kế đồ họa GDP490 có bao nhiêu tín chỉ?", "structured_lookup", ["structured_data_courses"], "Môn GDP490 (Đồ án tốt nghiệp Thiết kế Mỹ thuật số) có khối lượng đào tạo là 10 tín chỉ (được bố trí ở học kỳ 9, thuộc ngành Thiết kế Mỹ thuật số).")
add_q(3, "course_credits_semester", "sess_c_44", 1, "Môn PRF192 bao nhiêu tín chỉ và học ở học kỳ mấy?", "structured_lookup", ["structured_data_courses"], "Môn PRF192 (Cơ sở lập trình C) có khối lượng đào tạo là 3 tín chỉ (được bố trí ở học kỳ 1, thuộc ngành Kỹ thuật phần mềm).")
add_q(3, "course_credits_semester", "sess_c_45", 1, "Môn PRO192 học ở học kỳ thứ mấy của ngành KTPM?", "structured_lookup", ["structured_data_courses"], "Môn PRO192 (Lập trình hướng đối tượng với Java) được xếp vào học kỳ thứ 2 trong lộ trình đào tạo chuẩn của ngành Kỹ thuật phần mềm.")
add_q(3, "course_credits_semester", "sess_c_46", 1, "Môn CSD201 được xếp vào học kỳ thứ mấy trong khung chương trình?", "structured_lookup", ["structured_data_courses"], "Môn CSD201 (Cấu trúc dữ liệu và giải thuật) được xếp vào học kỳ thứ 3 trong lộ trình đào tạo chuẩn của ngành Kỹ thuật phần mềm.")
add_q(3, "course_credits_semester", "sess_c_47", 1, "Môn DBI202 có bao nhiêu tín chỉ và học ở kỳ mấy?", "structured_lookup", ["structured_data_courses"], "Môn DBI202 (Cơ sở dữ liệu) có khối lượng đào tạo là 3 tín chỉ (được bố trí ở học kỳ 3, thuộc ngành Kỹ thuật phần mềm).")
add_q(3, "course_credits_semester", "sess_c_48", 1, "Môn dự án phần mềm SWP391 được học ở học kỳ thứ mấy?", "structured_lookup", ["structured_data_courses"], "Môn SWP391 (Dự án phát triển ứng dụng phần mềm) được xếp vào học kỳ thứ 5 trong lộ trình đào tạo chuẩn của ngành Kỹ thuật phần mềm.")
add_q(3, "course_credits_semester", "sess_c_49", 1, "Môn AIL302m của ngành Trí tuệ nhân tạo học ở học kỳ mấy?", "structured_lookup", ["structured_data_courses"], "Môn AIL302m (Học máy) được xếp vào học kỳ thứ 4 trong lộ trình đào tạo chuẩn của ngành Trí tuệ nhân tạo.")
add_q(3, "course_credits_semester", "sess_c_50", 1, "Môn Mật mã học CRY301 được xếp vào học kỳ thứ mấy ngành ATTT?", "structured_lookup", ["structured_data_courses"], "Môn CRY301 (Mật mã học) được xếp vào học kỳ thứ 4 trong lộ trình đào tạo chuẩn của ngành An toàn thông tin.")
add_q(3, "course_credits_semester", "sess_c_51", 1, "Môn MKT101 của ngành Digital Marketing có bao nhiêu tín chỉ?", "structured_lookup", ["structured_data_courses"], "Môn MKT101 (Nguyên lý Marketing) có khối lượng đào tạo là 3 tín chỉ (được bố trí ở học kỳ 1, thuộc ngành Digital Marketing).")
add_q(3, "course_credits_semester", "sess_c_52", 1, "Môn Kinh tế vi mô ECO111 học ở học kỳ thứ mấy?", "structured_lookup", ["structured_data_courses"], "Môn ECO111 (Kinh tế vi mô) được xếp vào học kỳ thứ 2 trong lộ trình đào tạo chuẩn của ngành Quản trị kinh doanh.")
add_q(3, "course_credits_semester", "sess_c_53", 1, "Môn Thiết kế đồ họa 2D GRA201 có bao nhiêu tín chỉ?", "structured_lookup", ["structured_data_courses"], "Môn GRA201 (Thiết kế đồ họa 2D) có khối lượng đào tạo là 3 tín chỉ (được bố trí ở học kỳ 3, thuộc ngành Thiết kế Mỹ thuật số).")
add_q(3, "course_credits_semester", "sess_c_54", 1, "Môn Tiếng Anh học thuật 1 ENG101 bao nhiêu tín chỉ và học ở kỳ mấy?", "structured_lookup", ["structured_data_courses"], "Môn ENG101 (Tiếng Anh học thuật 1) có khối lượng đào tạo là 3 tín chỉ (được bố trí ở học kỳ 1, thuộc ngành Ngôn ngữ Anh).")
add_q(3, "course_credits_semester", "sess_c_55", 1, "Môn Kỹ năng học tập đại học SSL101c có mấy tín chỉ?", "structured_lookup", ["structured_data_courses"], "Môn SSL101c (Kỹ năng học tập đại học) có khối lượng đào tạo là 3 tín chỉ (được bố trí ở học kỳ 1, thuộc ngành Chung).")
add_q(3, "course_credits_semester", "sess_c_56", 1, "Các môn Võ Vovinam VOV114, VOV124, VOV134 có bao nhiêu tín chỉ tích lũy?", "structured_lookup", ["structured_data_courses"], "Môn VOV114 (Võ Vovinam 1) có khối lượng đào tạo là 0 tín chỉ (học phần điều kiện, không tính tín chỉ tích lũy GPA).")

# ==============================================================================
# PHẦN 4: HÌNH THỨC THI VÀ ĐÁNH GIÁ CỦA CÁC MÃ MÔN
# ==============================================================================
add_q(4, "course_assessment", "sess_c_58", 1, "Hình thức thi kết thúc học phần của môn PRF192 là gì?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn PRF192 (Cơ sở lập trình C): Thi thực hành máy (Practical Exam - PE), Thi lý thuyết trên phần mềm EOS, Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_59", 1, "Môn PRO192 có bài thi thực hành máy PE không?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn PRO192 (Lập trình hướng đối tượng với Java): Thi thực hành máy (Practical Exam - PE), Thi lý thuyết trên phần mềm EOS, Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_60", 1, "Hình thức kiểm tra và đánh giá môn CSD201 như thế nào?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn CSD201 (Cấu trúc dữ liệu và giải thuật): Thi thực hành máy (Practical Exam - PE), Thi lý thuyết trên phần mềm EOS, Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_61", 1, "Môn Cơ sở dữ liệu DBI202 thi thực hành hay thi trắc nghiệm trên EOS?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn DBI202 (Cơ sở dữ liệu): Thi thực hành máy (Practical Exam - PE), Thi lý thuyết trên phần mềm EOS, Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_62", 1, "Môn Lập trình Web với Java PRJ301 có bài thi lý thuyết trên EOS không?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn PRJ301 (Lập trình Web với Java): Thi thực hành máy (Practical Exam - PE), Bảo vệ Đồ án / Dự án (Project Defense), Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_63", 1, "Môn PRN211 (.NET) thi theo hình thức nào?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn PRN211 (Lập trình ứng dụng đa nền tảng với .NET): Thi thực hành máy (Practical Exam - PE), Bảo vệ Đồ án / Dự án (Project Defense), Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_64", 1, "Hình thức đánh giá môn dự án phần mềm SWP391 là gì?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn SWP391 (Dự án phát triển ứng dụng phần mềm): Bảo vệ Đồ án / Dự án (Project Defense), Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_65", 1, "Khóa luận tốt nghiệp SEP490 đánh giá theo hình thức nào?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn SEP490 (Khóa luận tốt nghiệp Kỹ thuật phần mềm): Bảo vệ Đồ án / Dự án (Project Defense).")
add_q(4, "course_assessment", "sess_c_66", 1, "Môn Học máy AIL302m có thi thực hành trên máy không?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn AIL302m (Học máy): Thi thực hành máy (Practical Exam - PE), Thi lý thuyết trên phần mềm EOS, Bảo vệ Đồ án / Dự án (Project Defense), Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_67", 1, "Môn Học sâu DLG301 thi theo hình thức nào?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn DLG301 (Học sâu): Thi thực hành máy (Practical Exam - PE), Thi lý thuyết trên phần mềm EOS, Bảo vệ Đồ án / Dự án (Project Defense), Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_68", 1, "Hình thức thi của môn An toàn hệ thống và mạng IAL201 là gì?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn IAL201 (An toàn hệ thống và mạng): Thi thực hành máy (Practical Exam - PE), Thi lý thuyết trên phần mềm EOS, Bảo vệ Đồ án / Dự án (Project Defense), Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_69", 1, "Môn Nguyên lý Marketing MKT101 thi theo hình thức nào?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn MKT101 (Nguyên lý Marketing): Thi lý thuyết trên phần mềm EOS, Bảo vệ Đồ án / Dự án (Project Defense), Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_70", 1, "Môn Dự án Marketing MKP391 có thi lý thuyết không?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn MKP391 (Dự án thực tế Marketing): Bảo vệ Đồ án / Dự án (Project Defense), Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_71", 1, "Môn Thiết kế đồ họa 2D GRA201 đánh giá kết quả học tập qua hình thức nào?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn GRA201 (Thiết kế đồ họa 2D): Bảo vệ Đồ án / Dự án (Project Defense), Bài tập lớn / Assignment quá trình.")
add_q(4, "course_assessment", "sess_c_72", 1, "Hình thức thi kết thúc học phần môn Vovinam VOV114 là gì?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn VOV114 (Võ Vovinam 1): Thi thực hành máy (Practical Exam - PE), Bài tập lớn / Assignment quá trình.")

# ==============================================================================
# PHẦN 5: KHÁC BIỆT MÃ MÔN VÀ NGÀNH ÁP DỤNG
# ==============================================================================
add_q(5, "course_programs", "sess_c_73", 1, "Môn PRF192 được giảng dạy cho những ngành đào tạo nào?", "structured_lookup", ["structured_data_courses"], "Môn PRF192 (Cơ sở lập trình C) được giảng dạy trong chương trình đào tạo của các ngành: Kỹ thuật phần mềm, Trí tuệ nhân tạo, An toàn thông tin, Khoa học máy tính, Hệ thống thông tin.")
add_q(5, "course_programs", "sess_c_74", 1, "Môn PRO192 có áp dụng cho ngành Trí tuệ nhân tạo và An toàn thông tin không?", "structured_lookup", ["structured_data_courses"], "Môn PRO192 (Lập trình hướng đối tượng với Java) được giảng dạy trong chương trình đào tạo của các ngành: Kỹ thuật phần mềm, Trí tuệ nhân tạo, An toàn thông tin, Khoa học máy tính, Hệ thống thông tin.")
add_q(5, "course_programs", "sess_c_75", 1, "Môn Cơ sở dữ liệu DBI202 áp dụng cho những ngành nào?", "structured_lookup", ["structured_data_courses"], "Môn DBI202 (Cơ sở dữ liệu) được giảng dạy trong chương trình đào tạo của các ngành: Kỹ thuật phần mềm, Trí tuệ nhân tạo, An toàn thông tin, Khoa học máy tính, Hệ thống thông tin.")
add_q(5, "course_programs", "sess_c_76", 1, "Môn Mạng máy tính NWC203c thuộc ngành nào quản lý và ngành nào được học?", "structured_lookup", ["structured_data_courses"], "Môn NWC203c (Mạng máy tính) được giảng dạy trong chương trình đào tạo của các ngành: Kỹ thuật phần mềm, Trí tuệ nhân tạo, An toàn thông tin, Khoa học máy tính, Hệ thống thông tin.")
add_q(5, "course_programs", "sess_c_77", 1, "Môn Lập trình .NET PRN211 là môn chuyên ngành của ngành nào?", "structured_lookup", ["structured_data_courses"], "Môn PRN211 (Lập trình ứng dụng đa nền tảng với .NET) được giảng dạy trong chương trình đào tạo của các ngành: Kỹ thuật phần mềm.")
add_q(5, "course_programs", "sess_c_78", 1, "Môn Học máy AIL302m có được học ở ngành Khoa học máy tính không?", "structured_lookup", ["structured_data_courses"], "Môn AIL302m (Học máy) được giảng dạy trong chương trình đào tạo của các ngành: Trí tuệ nhân tạo, Khoa học máy tính.")
add_q(5, "course_programs", "sess_c_79", 1, "Môn MKT101 áp dụng cho những ngành nào tại trường?", "structured_lookup", ["structured_data_courses"], "Môn MKT101 (Nguyên lý Marketing) được giảng dạy trong chương trình đào tạo của các ngành: Digital Marketing, Quản trị kinh doanh.")

# ==============================================================================
# PHẦN 6: CHUỖI HỘI THOẠI ĐA LƯỢT KẾ THỪA MÃ MÔN HỌC (MULTI-TURN)
# ==============================================================================
# Hội thoại 1: Lộ trình từ Lập trình C -> Java OOP -> Cấu trúc dữ liệu
add_q(7, "multiturn_course", "sess_mc_01", 1, "Môn PRF192 có môn tiên quyết nào không?", "structured_lookup", ["structured_data_courses"], "Môn PRF192 (Cơ sở lập trình C) không yêu cầu môn học tiên quyết nào.")
add_q(7, "multiturn_course", "sess_mc_01", 2, "Thế sau khi qua PRF192 thì môn tiếp theo là môn nào?", "structured_lookup", ["structured_data_courses"], "Môn tiếp theo trong lộ trình lập trình là PRO192 (Lập trình hướng đối tượng với Java), môn này yêu cầu tiên quyết là PRF192.", dialogue_context=[{"turn": 1, "query": "Môn PRF192 có môn tiên quyết nào không?", "answer": "Không yêu cầu"}])
add_q(7, "multiturn_course", "sess_mc_01", 3, "Môn đó có bài thi thực hành PE không?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn PRO192 (Lập trình hướng đối tượng với Java): Thi thực hành máy (Practical Exam - PE), Thi lý thuyết trên phần mềm EOS, Bài tập lớn / Assignment quá trình.", dialogue_context=[{"turn": 1, "query": "PRF192", "answer": "Không có tiên quyết"}, {"turn": 2, "query": "PRO192", "answer": "Tiên quyết là PRF192"}])

# Hội thoại 2: Lộ trình làm đồ án tốt nghiệp KTPM
add_q(7, "multiturn_course", "sess_mc_02", 1, "Môn dự án phần mềm SWP391 cần môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn SWP391 (Dự án phát triển ứng dụng phần mềm) yêu cầu môn tiên quyết bắt buộc là: SWE201c, PRJ301.")
add_q(7, "multiturn_course", "sess_mc_02", 2, "Môn này học ở học kỳ thứ mấy?", "structured_lookup", ["structured_data_courses"], "Môn SWP391 (Dự án phát triển ứng dụng phần mềm) được xếp vào học kỳ thứ 5 trong lộ trình đào tạo chuẩn của ngành Kỹ thuật phần mềm.", dialogue_context=[{"turn": 1, "query": "SWP391 cần tiên quyết nào?", "answer": "SWE201c, PRJ301"}])
add_q(7, "multiturn_course", "sess_mc_02", 3, "Qua môn đó thì có đủ điều kiện làm khóa luận tốt nghiệp SEP490 chưa?", "structured_lookup", ["structured_data_courses"], "Chưa đủ, môn SEP490 (Khóa luận tốt nghiệp Kỹ thuật phần mềm) yêu cầu hoàn thành cả 2 môn tiên quyết bắt buộc là: SWP391 và SWD392.", dialogue_context=[{"turn": 1, "query": "SWP391", "answer": "Kỳ 5"}, {"turn": 2, "query": "Học kỳ 5", "answer": "Học kỳ 5"}])

# Hội thoại 3: Lộ trình chuyên sâu Trí tuệ nhân tạo
add_q(8, "multiturn_course", "sess_mc_03", 1, "Môn AIL302m của ngành AI học ở kỳ mấy?", "structured_lookup", ["structured_data_courses"], "Môn AIL302m (Học máy) được xếp vào học kỳ thứ 4 trong lộ trình đào tạo chuẩn của ngành Trí tuệ nhân tạo.")
add_q(8, "multiturn_course", "sess_mc_03", 2, "Môn này có thi thực hành trên máy không?", "structured_lookup", ["structured_data_courses"], "Hình thức kiểm tra và thi của môn AIL302m (Học máy): Thi thực hành máy (Practical Exam - PE), Thi lý thuyết trên phần mềm EOS, Bảo vệ Đồ án / Dự án (Project Defense), Bài tập lớn / Assignment quá trình.", dialogue_context=[{"turn": 1, "query": "AIL302m kỳ mấy?", "answer": "Kỳ 4"}])
add_q(8, "multiturn_course", "sess_mc_03", 3, "Những môn chuyên sâu nào yêu cầu phải qua môn này trước?", "structured_lookup", ["structured_data_courses"], "Các môn chuyên sâu yêu cầu tiên quyết AIL302m bao gồm: NLP301c (Xử lý ngôn ngữ tự nhiên), CVL301c (Thị giác máy tính), DLG301 (Học sâu), và AIP391 (Dự án AI).", dialogue_context=[{"turn": 1, "query": "AIL302m", "answer": "Kỳ 4"}, {"turn": 2, "query": "Có PE không", "answer": "Có thi PE"}])

# Hội thoại 4: Lộ trình Marketing và đồ án tốt nghiệp QTKD
add_q(8, "multiturn_course", "sess_mc_04", 1, "Môn MKT101 có bao nhiêu tín chỉ?", "structured_lookup", ["structured_data_courses"], "Môn MKT101 (Nguyên lý Marketing) có khối lượng đào tạo là 3 tín chỉ (được bố trí ở học kỳ 1, thuộc ngành Digital Marketing).")
add_q(8, "multiturn_course", "sess_mc_04", 2, "Môn dự án thực tế MKP391 có cần qua môn này không?", "structured_lookup", ["structured_data_courses"], "Môn MKP391 (Dự án thực tế Marketing) yêu cầu môn tiên quyết bắt buộc là: MKT101.", dialogue_context=[{"turn": 1, "query": "MKT101 bao nhiêu tín chỉ?", "answer": "3 tín chỉ"}])
add_q(8, "multiturn_course", "sess_mc_04", 3, "Thế còn khóa luận tốt nghiệp BAP490 thì cần môn tiên quyết nào?", "structured_lookup", ["structured_data_courses"], "Môn BAP490 (Khóa luận tốt nghiệp Quản trị kinh doanh) yêu cầu môn tiên quyết bắt buộc là: FIN202, OBE102.", dialogue_context=[{"turn": 1, "query": "MKT101", "answer": "3 tín chỉ"}, {"turn": 2, "query": "MKP391", "answer": "Cần MKT101"}])

# ==============================================================================
# PHẦN 7: BẪY CHUYỂN CHỦ ĐỀ VÀ OOD CÂU HỎI MÃ MÔN
# ==============================================================================
add_q(9, "course_topic_switch", "sess_mc_05", 1, "Môn PRF192 cần môn nào tiên quyết?", "structured_lookup", ["structured_data_courses"], "Môn PRF192 (Cơ sở lập trình C) không yêu cầu môn học tiên quyết nào.")
add_q(9, "course_topic_switch", "sess_mc_05", 2, "Còn môn PRO192 thì sao?", "structured_lookup", ["structured_data_courses"], "Môn PRO192 (Lập trình hướng đối tượng với Java) yêu cầu môn tiên quyết bắt buộc là: PRF192.", dialogue_context=[{"turn": 1, "query": "PRF192", "answer": "Không có tiên quyết"}])
add_q(9, "course_topic_switch", "sess_mc_05", 3, "Thời hạn sinh viên được nộp đơn phúc khảo bài thi là bao lâu?", "rag_pipeline", ["FPTU-QC-003"], "Trong vòng 03 ngày làm việc (hoặc 1 tuần) kể từ ngày công bố kết quả thi (chủ đề phúc khảo độc lập).", dialogue_context=[{"turn": 1, "query": "PRF192", "answer": "Không có"}, {"turn": 2, "query": "PRO192", "answer": "Cần PRF192"}])

add_q(9, "course_topic_switch", "sess_mc_06", 1, "Môn DBI202 có bài thi thực hành máy PE không?", "structured_lookup", ["structured_data_courses"], "Có, môn DBI202 có bài thi thực hành máy Practical Exam (PE) trên hệ quản trị SQL Server.")
add_q(9, "course_topic_switch", "sess_mc_06", 2, "Môn này học ở học kỳ thứ mấy?", "structured_lookup", ["structured_data_courses"], "Môn DBI202 được xếp vào học kỳ thứ 3 trong lộ trình đào tạo chuẩn.", dialogue_context=[{"turn": 1, "query": "DBI202 có PE không?", "answer": "Có thi PE"}])
add_q(9, "course_topic_switch", "sess_mc_06", 3, "Quay lại câu đầu tiên tôi hỏi, nếu thi trượt bài thi PE môn đó thì lệ phí thi lại là bao nhiêu?", "structured_lookup", ["common_fees"], "Lệ phí thi lại của trường Đại học FPT là 300.000 VNĐ / lần thi.", dialogue_context=[{"turn": 1, "query": "DBI202 có PE", "answer": "Có PE"}, {"turn": 2, "query": "Kỳ 3", "answer": "Kỳ 3"}])

add_q(10, "ood_course", "sess_c_ood_01", 1, "Môn Giải tích 3 và Phương trình vi phân ở Đại học Bách Khoa có mã môn là gì?", "ood", [], "Câu hỏi về chương trình đào tạo của trường đại học khác nằm ngoài phạm vi học vụ Đại học FPT.")
add_q(10, "ood_course", "sess_c_ood_02", 1, "Làm sao để can thiệp vào server thi EOS sửa điểm bài thi PE môn PRF192 từ 3 điểm lên 9 điểm?", "ood", [], "Yêu cầu can thiệp chỉnh sửa điểm số vi phạm nghiêm trọng quy chế thi cử và nằm ngoài phạm vi hệ thống.")
add_q(10, "ood_course", "sess_c_ood_03", 1, "Môn học Chế tạo Tàu vũ trụ liên hành tinh của FPT học ở kỳ mấy?", "ood", [], "Trường Đại học FPT không có chương trình đào tạo hoặc môn học về Chế tạo Tàu vũ trụ liên hành tinh.")
add_q(10, "ood_course", "sess_c_ood_04", 1, "Cách làm món lẩu gà lá é ngon chuẩn vị Đà Lạt khi sinh viên học nhóm?", "ood", [], "Câu hỏi ẩm thực nằm ngoài phạm vi học vụ Đại học FPT.")
add_q(10, "ood_course", "sess_c_ood_05", 1, "Hôm nay giá cổ phiếu FPT tăng hay giảm bao nhiêu điểm trên sàn chứng khoán?", "ood", [], "Câu hỏi thị trường tài chính chứng khoán nằm ngoài phạm vi tư vấn học vụ đào tạo.")

assert len(questions) == 100, f"Tổng số câu hỏi phải đúng 100, hiện tại là {len(questions)}"

with open(output_path, "w", encoding="utf-8") as f:
    for q in questions:
        f.write(json.dumps(q, ensure_ascii=False) + "\n")

print(f"Generated {len(questions)} course questions successfully to: {output_path}")
