"""Router điều phối truy vấn: Structured Lookup vs RAG Pipeline vs Clarification vs OOD. Phụ trách: TV3.

Chiến lược điều phối:
1. intent == "tuition_lookup":
   - Đủ slot (program + cohort): Chuyển sang "structured_lookup" tra thẳng vào bảng học phí mock (Zero Hallucination).
   - Thiếu slot (ví dụ thiếu cohort hoặc program): Chuyển sang "clarification" để hỏi làm rõ (mầm mống cho Multi-turn Tuần 5).
2. intent in ["policy_lookup", "graduation_lookup"]: Chuyển sang "rag_pipeline" tra cứu tài liệu quy chế.
3. intent == "OOD": Chuyển sang "ood" trả về thông báo từ chối lịch sự.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from contracts import ParsedQuery
from FPTUniQA.query.campus_matcher import match_campus
from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.query.router")

RouteType = Literal["structured_lookup", "rag_pipeline", "clarification", "ood", "uncertain"]

MOCK_TUITION_PATH = Path(__file__).parent / "mock_tuition_table.json"

# Đường dẫn dữ liệu cấu trúc thực tế (TV1)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STRUCTURED_DATA_PATH = Path("data/processed/structured_data.json")
if not STRUCTURED_DATA_PATH.exists():
    STRUCTURED_DATA_PATH = _PROJECT_ROOT / "data/processed/structured_data.json"

STRUCTURED_CREDITS_PATH = Path("data/processed/structured_data_credits.json")
if not STRUCTURED_CREDITS_PATH.exists():
    STRUCTURED_CREDITS_PATH = _PROJECT_ROOT / "data/processed/structured_data_credits.json"

_STRUCTURED_DATA_CACHE = None
_STRUCTURED_CREDITS_CACHE = None


class RouteResult(str):
    """Chuỗi kết quả định tuyến có thể so sánh trực tiếp như str (ví dụ route == 'structured_lookup')
    đồng thời hỗ trợ unpack tuple (route, clarification_msg) và truy cập thuộc tính .clarification và .level (1-10).
    """

    def __new__(cls, route: str, clarification: Optional[str] = None, level: int = 1):
        instance = super().__new__(cls, route)
        instance.route = route
        instance.clarification = clarification
        instance.level = level
        return instance

    def __iter__(self):
        return iter((str(self), self.clarification))


def load_mock_tuition_table() -> list:
    """Đọc dữ liệu bảng học phí giả lập trong namespace TV3."""
    if not MOCK_TUITION_PATH.exists():
        logger.warning(f"Không tìm thấy file bảng học phí tại {MOCK_TUITION_PATH}")
        return []
    with open(MOCK_TUITION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_real_structured_data() -> Optional[Dict[str, Any]]:
    """Nạp bảng dữ liệu học phí có cấu trúc 190 biểu phí từ TV1."""
    global _STRUCTURED_DATA_CACHE
    if _STRUCTURED_DATA_CACHE is not None:
        return _STRUCTURED_DATA_CACHE
    if STRUCTURED_DATA_PATH.exists():
        try:
            with open(STRUCTURED_DATA_PATH, "r", encoding="utf-8") as f:
                _STRUCTURED_DATA_CACHE = json.load(f)
                return _STRUCTURED_DATA_CACHE
        except Exception as e:
            logger.warning(f"Lỗi khi đọc file structured_data.json: {e}")
    return None


def load_real_credits_data() -> Optional[Dict[str, Any]]:
    """Nạp bảng dữ liệu số tín chỉ theo ngành từ TV1."""
    global _STRUCTURED_CREDITS_CACHE
    if _STRUCTURED_CREDITS_CACHE is not None:
        return _STRUCTURED_CREDITS_CACHE
    if STRUCTURED_CREDITS_PATH.exists():
        try:
            with open(STRUCTURED_CREDITS_PATH, "r", encoding="utf-8") as f:
                _STRUCTURED_CREDITS_CACHE = json.load(f)
                return _STRUCTURED_CREDITS_CACHE
        except Exception as e:
            logger.warning(f"Lỗi khi đọc file structured_data_credits.json: {e}")
    return None


def determine_query_level(
    parsed: ParsedQuery,
    route: str,
    history: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """Xác định cấp độ phức tạp truy vấn (Levels 1 - 10) theo phân loại kiến trúc hệ thống."""
    # Level 10: Ngoài phạm vi (OOD)
    if route == "ood" or parsed.intent == "OOD":
        return 10

    # Nếu có lịch sử hội thoại đa lượt
    if history and len(history) > 0:
        query_text = parsed.normalized_query or parsed.original_query or ""
        # Kiểm tra Topic Switch (Level 9)
        from FPTUniQA.query.rewriting import detect_topic_switch
        switch_info = detect_topic_switch(query_text, history)
        if switch_info.get("is_topic_switch"):
            return 9

        # Nếu là câu hỏi tiếp nối sâu (composite cross-topic)
        if any(w in query_text.lower() for w in ["ojt", "tốt nghiệp", "học bổng", "tín chỉ"]):
            return 8

        # Câu tỉnh lược / thay thế tham số thông thường (Level 7)
        return 7

    # Các cấp độ đơn lượt (Single-turn)
    if route == "clarification":
        return 4

    query_lower = (parsed.normalized_query or parsed.original_query or "").lower()

    if route == "structured_lookup":
        # Tra cứu có so sánh chính sách / ưu đãi vùng miền (Level 3)
        if any(w in query_lower for w in ["ưu đãi", "giảm", "khác biệt", "so sánh", "chênh lệch"]):
            return 3
        # Tra cứu số liệu chuẩn (Level 1)
        return 1

    # Nhánh RAG Pipeline
    # Level 6: Điều kiện tốt nghiệp & chuẩn đầu ra OJT
    if parsed.intent == "graduation_lookup" or any(w in query_lower for w in ["tốt nghiệp", "chuẩn đầu ra", "đồ án", "khóa luận", "ojt", "thực tập"]):
        return 6

    # Level 5: Quy chế xử lý học vụ & cảnh báo & buộc thôi học
    if any(w in query_lower for w in ["cảnh báo", "kỷ luật", "đình chỉ", "thôi học", "buộc thôi học", "nợ môn", "điểm f", "phúc khảo"]):
        return 5

    # Level 3: Tham số biến thể theo cơ sở / năm
    if any(w in query_lower for w in ["cơ sở", "campus", "khóa", "năm học", "hà nội", "cần thơ", "đà nẵng", "quy nhơn", "hồ chí minh"]):
        return 3

    # Level 2: Tra cứu sự kiện / quy chế đơn lẻ cơ bản
    return 2


def route_query(
    parsed: ParsedQuery,
    history: Optional[List[Dict[str, Any]]] = None,
) -> RouteResult:
    """
    Phân loại tuyến đường thực thi dựa trên đối tượng ParsedQuery (Contract 3) và lịch sử hội thoại.
    Hỗ trợ gán nhãn mức độ phức tạp từ Level 1 đến Level 10.
    """
    # 1. Nhánh ngoài phạm vi (OOD) -> Level 10
    if parsed.intent == "OOD":
        return RouteResult("ood", None, level=10)

    # 0. Kiểm tra ngưỡng tin cậy an toàn (Tuần 6 Guardrail)
    if parsed.confidence is not None and parsed.confidence < 0.5:
        return RouteResult(
            "uncertain",
            "Hệ thống chưa chắc chắn về câu hỏi này (độ tin cậy phân tích thấp). Vui lòng diễn đạt rõ hơn hoặc cung cấp thêm thông tin học vụ cụ thể.",
            level=10,
        )

    # 2. Nhánh tra cứu học phí / số liệu (tuition_lookup)
    if parsed.intent == "tuition_lookup":
        slots = parsed.slots or {}
        has_program = bool(slots.get("program")) and slots.get("program") not in ["chung", "chuyên ngành"]
        has_cohort = bool(slots.get("cohort"))
        has_campus = bool(slots.get("campus"))
        q_text = (parsed.normalized_query or parsed.original_query or "").lower()

        # Kiểm tra các câu hỏi về lệ phí chung hoặc chính sách ưu đãi phân hiệu
        is_regional_discount = any(w in q_text for w in ["ưu đãi", "giảm", "bao nhiêu %", "phần trăm", "hỗ trợ học phí", "chính sách ưu đãi"]) and any(c in q_text for c in ["quy nhơn", "cần thơ", "đà nẵng", "phân hiệu", "cơ sở"])
        is_ojt_fee = ("ojt" in q_text or "thực tập" in q_text) and ("học phí" in q_text or "phí" in q_text or "đóng" in q_text)
        is_common_fee = (slots.get("topic") == "common_fee") or any(w in q_text for w in ["thi lại", "học lại", "ký túc xá", "lệ phí tốt nghiệp", "lệ phí cấp bằng"]) or is_regional_discount or is_ojt_fee

        # Câu hỏi tra cứu biểu phí toàn khóa (cohort-wide): có cohort và yêu cầu biểu phí chung/chuyên ngành/toàn khóa
        is_cohort_wide = has_cohort and any(w in q_text for w in ["chuyên ngành", "toàn khóa", "biểu phí chung", "tất cả các ngành", "khung học phí"])

        # Đủ ngành và khóa tuyển sinh (hoặc phân hiệu) hoặc biểu phí chung -> Tra cứu bảng số liệu (Zero Hallucination)
        if ((has_program and (has_cohort or has_campus)) or is_common_fee or is_cohort_wide):
            lvl = determine_query_level(parsed, "structured_lookup", history)
            return RouteResult("structured_lookup", None, level=lvl)

        # Thiếu slot -> Hỏi làm rõ thông tin (Level 4)
        if has_program and not has_cohort and not has_campus:
            program = slots.get("program")
            return RouteResult(
                "clarification",
                f"Bạn đang hỏi về học phí ngành {program}. Vui lòng cho biết bạn muốn tra cứu cho khóa tuyển sinh hoặc phân hiệu nào (ví dụ: khóa 2026 tại Cần Thơ)?",
                level=4,
            )
        elif has_cohort and not has_program:
            cohort = slots.get("cohort")
            return RouteResult(
                "clarification",
                f"Bạn đang hỏi về học phí khóa {cohort}. Vui lòng cho biết bạn muốn tra cứu cho ngành học nào (ví dụ: AI, CNTT, KTPM)?",
                level=4,
            )
        else:
            return RouteResult(
                "clarification",
                "Vui lòng cung cấp thêm ngành học và khóa tuyển sinh (ví dụ: ngành AI khóa 2026) để tôi tra cứu học phí chính xác cho bạn.",
                level=4,
            )

    # 2.5. Nhánh tra cứu mã môn học / học phần (course_lookup)
    slots = parsed.slots or {}
    q_raw = parsed.normalized_query or parsed.original_query or ""
    c_code = slots.get("course_code")
    if not c_code:
        m = re.search(r"\b([a-zA-Z]{3}\d{3}[a-zA-Z]?)\b", q_raw)
        if m:
            c_code = m.group(1).upper()

    from FPTUniQA.data.structured import StructuredDataParser
    db_p = StructuredDataParser()
    known_codes = {c["course_code"].upper() for c in db_p.courses_data.get("courses", [])}

    if (parsed.intent == "course_lookup" or (c_code and c_code in known_codes)):
        lvl = determine_query_level(parsed, "structured_lookup", history)
        return RouteResult("structured_lookup", None, level=lvl)

    # 3. Nhánh quy chế và tốt nghiệp -> Chuyển vào RAG Pipeline
    lvl = determine_query_level(parsed, "rag_pipeline", history)
    return RouteResult("rag_pipeline", None, level=lvl)


def _match_campus(raw_campus: str) -> Optional[str]:
    """Chuẩn hóa tên phân hiệu cơ sở đào tạo thông qua campus_matcher dùng chung."""
    return match_campus(raw_campus)


def execute_structured_lookup(slots_or_parsed: Any) -> Dict[str, Any]:
    """
    Tra cứu trực tiếp vào bảng số liệu có cấu trúc (Zero Hallucination).
    1. Ưu tiên tra cứu structured_data.json (190 biểu phí chính thức năm 2026/K22 theo 5 phân hiệu từ TV1).
    2. Nếu câu hỏi liên quan đến tín chỉ hoặc có thông tin tín chỉ, kết hợp structured_data_credits.json.
    3. Fallback sang mock_tuition_table.json cho các trường hợp đặc biệt / mock tests cũ.
    """
    if hasattr(slots_or_parsed, "slots"):
        slots = slots_or_parsed.slots or {}
    elif isinstance(slots_or_parsed, dict):
        slots = slots_or_parsed.get("slots", slots_or_parsed) if "slots" in slots_or_parsed and not any(k in slots_or_parsed for k in ["program", "cohort", "campus"]) else slots_or_parsed
    else:
        slots = {}

    raw_program = str(slots.get("program") or "").strip()
    raw_cohort = str(slots.get("cohort") or "").strip()
    raw_campus = str(slots.get("campus") or "").strip()
    raw_topic = str(slots.get("topic") or "").strip()

    # Bổ trợ trích xuất campus từ query gốc nếu slots chưa có
    if not raw_campus:
        for attr in ["original_query", "normalized_query"]:
            val = getattr(slots_or_parsed, attr, None)
            if val:
                found_c = _match_campus(str(val))
                if found_c:
                    raw_campus = found_c
                    break

    # Chuẩn hóa tên ngành
    program_alias_map = {
        "ai": "Trí tuệ nhân tạo",
        "trí tuệ nhân tạo": "Trí tuệ nhân tạo",
        "tri tue nhan tao": "Trí tuệ nhân tạo",
        "cntt": "Công nghệ thông tin",
        "công nghệ thông tin": "Công nghệ thông tin",
        "cong nghe thong tin": "Công nghệ thông tin",
        "ktpm": "Kỹ thuật phần mềm",
        "kỹ thuật phần mềm": "Kỹ thuật phần mềm",
        "ky thuat phan mem": "Kỹ thuật phần mềm",
        "attt": "An toàn thông tin",
        "an toàn thông tin": "An toàn thông tin",
        "an toan thong tin": "An toàn thông tin",
        "khdl": "Khoa học dữ liệu và ứng dụng",
        "khoa học dữ liệu": "Khoa học dữ liệu và ứng dụng",
        "khoa học dữ liệu và ứng dụng": "Khoa học dữ liệu và ứng dụng",
        "vi mạch": "Vi mạch bán dẫn",
        "bán dẫn": "Vi mạch bán dẫn",
        "vi mạch bán dẫn": "Vi mạch bán dẫn",
        "ô tô": "Công nghệ ô tô số (Automotive)",
        "công nghệ ô tô số": "Công nghệ ô tô số (Automotive)",
        "httt": "Hệ thống thông tin",
        "hệ thống thông tin": "Hệ thống thông tin",
        "đồ họa": "Thiết kế đồ họa và mỹ thuật số",
        "mỹ thuật số": "Thiết kế đồ họa và mỹ thuật số",
        "thiết kế đồ họa": "Thiết kế đồ họa và mỹ thuật số",
        "truyền thông": "Truyền thông đa phương tiện",
        "truyền thông đa phương tiện": "Truyền thông đa phương tiện",
        "qtkd": "Quản trị kinh doanh",
        "quản trị kinh doanh": "Quản trị kinh doanh",
        "kdqt": "Kinh doanh quốc tế",
        "kinh doanh quốc tế": "Kinh doanh quốc tế",
        "marketing": "Marketing",
        "ngôn ngữ anh": "Ngôn ngữ Anh",
        "tiếng anh": "Ngôn ngữ Anh",
        "ngôn ngữ hàn": "Ngôn ngữ Hàn Quốc",
        "ngôn ngữ hàn quốc": "Ngôn ngữ Hàn Quốc",
        "tiếng hàn": "Ngôn ngữ Hàn Quốc",
        "ngôn ngữ trung": "Ngôn ngữ Trung Quốc",
        "ngôn ngữ trung quốc": "Ngôn ngữ Trung Quốc",
        "tiếng trung": "Ngôn ngữ Trung Quốc",
        "ngôn ngữ nhật": "Ngôn ngữ Nhật",
        "tiếng nhật": "Ngôn ngữ Nhật",
        "luật": "Luật",
        "luật kinh tế": "Luật kinh tế",
    }

    target_program = raw_program
    for alias, full_name in program_alias_map.items():
        if alias.lower() == raw_program.lower() or alias.lower() in raw_program.lower():
            target_program = full_name
            break

    target_campus = _match_campus(raw_campus)

    # 1. Tra cứu trong real structured_data.json
    real_data = load_real_structured_data()

    # Trích xuất chuỗi câu hỏi để phục vụ tra cứu biểu phí chung
    query_str = ""
    for attr in ["original_query", "normalized_query"]:
        val = getattr(slots_or_parsed, attr, None)
        if val:
            query_str = str(val).lower()
            break
    if not query_str and isinstance(slots_or_parsed, dict):
        query_str = str(slots_or_parsed.get("query", "")).lower()

    # 0. Tra cứu môn học theo Curriculum Knowledge Base (CKB) nếu có mã môn
    course_code = slots.get("course_code")
    if not course_code:
        c_match = re.search(r"\b([A-Z]{3}\d{3}[a-z]?)\b", query_str.upper())
        if c_match:
            course_code = c_match.group(1).upper()

    if course_code:
        from FPTUniQA.data.structured import StructuredDataParser
        db_parser = StructuredDataParser()
        c_info = db_parser.get_course(course_code)
        if c_info:
            aspect = slots.get("course_aspect")
            if not aspect or aspect == "general":
                if any(w in query_str for w in ["học những gì", "học gì", "nội dung", "kiến thức", "chủ đề", "kỹ năng", "dạy những gì", "học cái gì", "học môn này được gì"]):
                    aspect = "syllabus"
                elif any(w in query_str for w in ["giáo trình", "sách", "tài liệu", "sách giáo trình", "tác giả", "ai viết", "nhà xuất bản"]):
                    aspect = "textbook"
                elif any(w in query_str for w in ["tiên quyết", "trước", "cần qua môn", "yêu cầu"]):
                    aspect = "prerequisite"
                elif any(w in query_str for w in ["tín chỉ", "bao nhiêu tín", "số tín"]):
                    aspect = "credits"
                elif any(w in query_str for w in ["thi", "kiểm tra", "pe", "eos", "đánh giá", "thực hành", "hình thức", "bảo vệ"]):
                    aspect = "assessment"
                elif any(w in query_str for w in ["kỳ", "học kỳ", "kỳ mấy", "kỳ thứ"]):
                    aspect = "semester"
                elif any(w in query_str for w in ["ngành", "chuyên ngành"]):
                    aspect = "programs"

            ans = db_parser.format_course_answer(course_code, aspect=aspect)
            return {
                "found": True,
                "answer": ans,
                "text": ans,
                "data": c_info,
                "source": "Curriculum Knowledge Base (CKB)",
            }

    # Tra cứu các loại lệ phí phổ biến (common_fees)
    if real_data and "common_fees" in real_data:
        c_fees = real_data["common_fees"]
        if "thi lại" in query_str:
            fee = c_fees.get("retake_exam_fee_vnd", 300000)
            ans = f"Lệ phí thi lại của trường Đại học FPT là {fee:,} VNĐ / lần thi."
            return {"found": True, "answer": ans, "text": ans, "data": {"fee": fee}, "source": "Quy định biểu phí ĐH FPT (common_fees)"}
        elif "học lại" in query_str:
            fee = c_fees.get("relearn_per_credit_vnd", 650000)
            ans = f"Lệ phí đăng ký học lại của Đại học FPT là {fee:,} VNĐ / tín chỉ."
            return {"found": True, "answer": ans, "text": ans, "data": {"fee": fee}, "source": "Quy định biểu phí ĐH FPT (common_fees)"}
        elif "ký túc xá" in query_str or "ktx" in query_str:
            fee = c_fees.get("dormitory_fuhl_per_term_vnd", 4000000)
            ans = f"Phí ký túc xá tại phân hiệu FUHL Hòa Lạc là {fee:,} VNĐ / học kỳ."
            return {"found": True, "answer": ans, "text": ans, "data": {"fee": fee}, "source": "Quy định biểu phí ĐH FPT (common_fees)"}
        elif "tốt nghiệp" in query_str and ("lệ phí" in query_str or "phí" in query_str or "cấp bằng" in query_str):
            fee = c_fees.get("graduation_fee_vnd", 1500000)
            ans = f"Lệ phí công nhận tốt nghiệp và cấp bằng là {fee:,} VNĐ."
            return {"found": True, "answer": ans, "text": ans, "data": {"fee": fee}, "source": "Quy định biểu phí ĐH FPT (common_fees)"}
        elif "ojt" in query_str and ("học phí" in query_str or "đóng" in query_str or "phí" in query_str):
            ans = "Theo quy định đào tạo của Đại học FPT, trong giai đoạn thực tập tại doanh nghiệp (OJT - On the Job Training), sinh viên không phải đóng học phí chuyên ngành mà chỉ đóng chi phí quản lý thực tập (hoặc miễn học phí tùy chương trình)."
            return {"found": True, "answer": ans, "text": ans, "data": {"fee": 0}, "source": "Quy chế đào tạo và thực tập OJT ĐH FPT"}

    # Tra cứu chính sách ưu đãi phân hiệu (regional_discount_policy)
    if real_data and "regional_discount_policy" in real_data:
        discounts = real_data["regional_discount_policy"]
        if any(k in query_str for k in ["ưu đãi", "giảm", "hỗ trợ học phí", "chính sách ưu đãi", "bao nhiêu %", "phần trăm"]):
            for camp, rate in discounts.items():
                if camp.lower() in query_str:
                    pct = int(rate * 100)
                    ans = f"Theo chính sách ưu đãi phân hiệu của Đại học FPT, sinh viên theo học tại phân hiệu {camp} được hỗ trợ ưu đãi học phí là {pct}%."
                    return {"found": True, "answer": ans, "text": ans, "data": {"campus": camp, "discount_rate": rate}, "source": "Chính sách ưu đãi phân hiệu ĐH FPT"}
            if "cần thơ" in query_str or "đà nẵng" in query_str:
                ans = "Theo chính sách ưu đãi phân hiệu của Đại học FPT, sinh viên theo học tại phân hiệu Cần Thơ hoặc Đà Nẵng được hỗ trợ ưu đãi học phí là 30%."
                return {"found": True, "answer": ans, "text": ans, "data": {"discount_rate": 0.3}, "source": "Chính sách ưu đãi phân hiệu ĐH FPT"}

    # Tra cứu biểu phí theo khóa (fpt_cohort_fees)
    if real_data and "fpt_cohort_fees" in real_data:
        c_fees_list = real_data["fpt_cohort_fees"]
        target_cohort_clean = raw_cohort.upper().strip()
        for item in c_fees_list:
            if target_cohort_clean == item.get("cohort"):
                spec_fee = item.get("specialized_term_tuition_vnd", 0)
                prep_fee = item.get("prep_english_per_level_vnd", 0)
                cam = item.get("campus", "ALL")
                ans = (
                    f"Biểu phí tuyển sinh Đại học FPT khóa {target_cohort_clean} (Cơ sở: {cam}):\n"
                    f"- Học phí chuyên ngành: {spec_fee:,} VNĐ / học kỳ (tổng 9 học kỳ chuyên ngành).\n"
                    f"- Học phí tiếng Anh chuẩn bị: {prep_fee:,} VNĐ / mức (level) (tối đa 6 mức)."
                )
                if not target_program or target_program in ["chuyên ngành", "chung"]:
                    return {"found": True, "answer": ans, "text": ans, "data": item, "source": f"Biểu phí khóa {target_cohort_clean} ĐH FPT"}

    if real_data and "tuition_by_campus" in real_data:
        tuition_by_campus = real_data["tuition_by_campus"]

        # Tìm tên ngành khớp nhất trong dataset
        matched_major = None
        for camp_name, rows in tuition_by_campus.items():
            for row in rows:
                major_name = row.get("major_name", "")
                if (
                    target_program.lower() == major_name.lower()
                    or target_program.lower() in major_name.lower()
                    or major_name.lower() in target_program.lower()
                ):
                    matched_major = major_name
                    break
            if matched_major:
                break

        if matched_major:
            # Tra cứu số tín chỉ nếu có
            credits_text = ""
            credits_data = load_real_credits_data()
            if credits_data and "programs" in credits_data:
                prog_credits = credits_data["programs"]
                for p_name, p_info in prog_credits.items():
                    if p_name.lower() in matched_major.lower() or matched_major.lower() in p_name.lower():
                        credits_text = f"\n- Tổng số tín chỉ chương trình đào tạo: {p_info.get('total_credits', 0)} tín chỉ (Lý thuyết: {p_info.get('theory_credits', 0)}, Thực hành: {p_info.get('practice_credits', 0)})."
                        break

            # Nếu người dùng có chỉ định phân hiệu
            if target_campus and target_campus in tuition_by_campus:
                camp_rows = tuition_by_campus[target_campus]
                row_match = next((r for r in camp_rows if r.get("major_name") == matched_major), None)
                if row_match:
                    ans = (
                        f"Theo biểu phí chính thức tuyển sinh Đại học FPT phân hiệu {target_campus} "
                        f"(Khóa {row_match.get('cohort', 'K22')} - Năm học {row_match.get('academic_year', '2026')}):\n"
                        f"- Ngành đào tạo: {matched_major}\n"
                        f"- Mức học phí sinh viên Khu vực 1 (KV1): {row_match['tuition_kv1_vnd']:,} VNĐ/học kỳ\n"
                        f"- Mức học phí sinh viên các khu vực khác: {row_match['tuition_other_kv_vnd']:,} VNĐ/học kỳ"
                        f"{credits_text}"
                    )
                    return {
                        "found": True,
                        "answer": ans,
                        "text": ans,
                        "data": row_match,
                        "source": f"Biểu phí tuyển sinh ĐH FPT phân hiệu {target_campus} (Khóa 2026/K22)",
                    }

            # Nếu không chỉ định phân hiệu -> Trả về biểu phí tổng hợp cả 5 phân hiệu
            lines = [
                f"Theo biểu phí chính thức tuyển sinh Đại học FPT (Khóa 2026 / K22) cho ngành {matched_major}:"
            ]
            matched_records = []
            for c_name in ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Cần Thơ", "Quy Nhơn"]:
                c_rows = tuition_by_campus.get(c_name, [])
                r_found = next((r for r in c_rows if r.get("major_name") == matched_major), None)
                if r_found:
                    matched_records.append(r_found)
                    discount_note = ""
                    if c_name in ["Đà Nẵng", "Cần Thơ"]:
                        discount_note = " (Ưu đãi 30%)"
                    elif c_name == "Quy Nhơn":
                        discount_note = " (Ưu đãi 50%)"
                    lines.append(
                        f"• Phân hiệu {c_name}{discount_note}: "
                        f"{r_found['tuition_other_kv_vnd']:,} VNĐ/kỳ (KV1: {r_found['tuition_kv1_vnd']:,} VNĐ/kỳ)"
                    )

            if credits_text:
                lines.append(credits_text)
            lines.append("\n(Lưu ý: Mức học phí áp dụng cho sinh viên nhập học năm 2026 theo từng học kỳ chuyên ngành).")

            ans = "\n".join(lines)
            return {
                "found": True,
                "answer": ans,
                "text": ans,
                "data": matched_records,
                "source": f"Biểu phí tuyển sinh ĐH FPT (Khóa 2026/K22) - {matched_major}",
            }

    # 2. Fallback sang mock_tuition_table.json
    table = load_mock_tuition_table()
    raw_cohort_clean = re.search(r"\d{4}", raw_cohort)
    target_cohort = raw_cohort_clean.group(0) if raw_cohort_clean else raw_cohort

    for row in table:
        row_program = str(row.get("program", "")).strip().upper()
        row_cohort = str(row.get("cohort", "")).strip().upper()

        if (
            target_program.upper() == row_program
            or row_program in target_program.upper()
        ) and (not target_cohort or row_cohort == target_cohort or target_cohort.endswith(row_cohort)):
            amount_formatted = f"{row['tuition_per_term_vnd']:,} {row['currency']}"
            answer = (
                f"Theo biểu phí chính thức của Đại học FPT, học phí chuyên ngành {row['program_name']} ({row['program']}) "
                f"cho sinh viên Khóa {row['cohort']} là {amount_formatted}/học kỳ. "
                f"Thời gian đào tạo chuẩn gồm {row['total_terms']} học kỳ chuyên ngành. ({row['note']})"
            )
            return {
                "found": True,
                "answer": answer,
                "text": answer,
                "data": row,
                "source": f"Biểu phí tuyển sinh ĐH FPT - Khóa {row['cohort']} ({row['program']})",
            }

    not_found_msg = f"Hiện tại chưa có dữ liệu học phí chính xác cho ngành {target_program} trong hệ thống biểu phí."
    return {
        "found": False,
        "answer": not_found_msg,
        "text": not_found_msg,
        "data": None,
        "source": "Biểu phí tuyển sinh ĐH FPT",
    }
