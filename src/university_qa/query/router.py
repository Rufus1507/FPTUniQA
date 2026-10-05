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
from typing import Any, Dict, Literal, Optional, Tuple

from contracts import ParsedQuery
from university_qa.utils.logger import get_logger

logger = get_logger("university_qa.query.router")

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
    đồng thời hỗ trợ unpack tuple (route, clarification_msg) và truy cập thuộc tính .clarification.
    """

    def __new__(cls, route: str, clarification: Optional[str] = None):
        instance = super().__new__(cls, route)
        instance.route = route
        instance.clarification = clarification
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


def route_query(parsed: ParsedQuery) -> RouteResult:
    """
    Phân loại tuyến đường thực thi dựa trên đối tượng ParsedQuery (Contract 3).

    Trả về RouteResult:
        - "uncertain": Khi confidence < 0.5 (Guardrail an toàn Tuần 6)
        - "structured_lookup": Tra cứu trực tiếp bảng học phí
        - "rag_pipeline": Tra cứu quy chế qua mock_retriever
        - "clarification": Hỏi làm rõ khi thiếu slot cần thiết
        - "ood": Ngoài phạm vi đào tạo
    """
    # 0. Kiểm tra ngưỡng tin cậy an toàn (Tuần 6 Guardrail)
    # Nếu confidence < 0.5 (dù intent không phải OOD) -> tự động coi như không đủ tin cậy
    if parsed.confidence is not None and parsed.confidence < 0.5:
        return RouteResult(
            "uncertain",
            "Hệ thống chưa chắc chắn về câu hỏi này (độ tin cậy phân tích thấp). Vui lòng diễn đạt rõ hơn hoặc cung cấp thêm thông tin học vụ cụ thể.",
        )

    # 1. Nhánh ngoài phạm vi (OOD)
    if parsed.intent == "OOD":
        return RouteResult("ood", None)

    # 2. Nhánh tra cứu học phí / số liệu (tuition_lookup)
    if parsed.intent == "tuition_lookup":
        slots = parsed.slots or {}
        has_program = bool(slots.get("program"))
        has_cohort = bool(slots.get("cohort"))

        has_campus = bool(slots.get("campus"))

        # Đủ ngành và khóa tuyển sinh (hoặc phân hiệu) -> Tra cứu trực tiếp bảng số liệu (Zero Hallucination)
        if has_program and (has_cohort or has_campus):
            return RouteResult("structured_lookup", None)

        # Thiếu slot -> Hỏi làm rõ thông tin thay vì đoán bừa (chống ảo giác, mầm cho Tuần 5)
        if has_program and not has_cohort and not has_campus:
            program = slots.get("program")
            return RouteResult(
                "clarification",
                f"Bạn đang hỏi về học phí ngành {program}. Vui lòng cho biết bạn muốn tra cứu cho khóa tuyển sinh hoặc phân hiệu nào (ví dụ: khóa 2026 tại Cần Thơ)?",
            )
        elif has_cohort and not has_program:
            cohort = slots.get("cohort")
            return RouteResult(
                "clarification",
                f"Bạn đang hỏi về học phí khóa {cohort}. Vui lòng cho biết bạn muốn tra cứu cho ngành học nào (ví dụ: AI, CNTT, KTPM)?",
            )
        else:
            return RouteResult(
                "clarification",
                "Vui lòng cung cấp thêm ngành học và khóa tuyển sinh (ví dụ: ngành AI khóa 2026) để tôi tra cứu học phí chính xác cho bạn.",
            )

    # 3. Nhánh quy chế và tốt nghiệp -> Chuyển vào RAG Pipeline
    if parsed.intent in ["policy_lookup", "graduation_lookup"]:
        return RouteResult("rag_pipeline", None)

    return RouteResult("rag_pipeline", None)


def _match_campus(raw_campus: str) -> Optional[str]:
    """Chuẩn hóa tên phân hiệu cơ sở đào tạo, hỗ trợ có dấu, không dấu và chịu lỗi encoding ký tự từ terminal."""
    if not raw_campus:
        return None
    c_lower = raw_campus.strip().lower()

    # 1. Cần Thơ
    if any(k in c_lower for k in ["cần thơ", "can tho", "cantho", "cầntho"]) or re.search(r"c[aần\?]?n\s*th[oơ\?]", c_lower):
        return "Cần Thơ"
    # 2. Quy Nhơn
    if any(k in c_lower for k in ["quy nhơn", "quy nhon", "quynhon", "bình định", "binh dinh"]) or re.search(r"quy\s*nh[oơ\?]", c_lower):
        return "Quy Nhơn"
    # 3. Đà Nẵng
    if any(k in c_lower for k in ["đà nẵng", "da nang", "danang", "đn", "dn"]) or re.search(r"d[aà\?]\s*n[aẵ\?]ng", c_lower):
        return "Đà Nẵng"
    # 4. TP. Hồ Chí Minh
    if any(k in c_lower for k in ["hồ chí minh", "ho chi minh", "hcm", "tphcm", "tp.hcm", "sài gòn", "sai gon"]) or re.search(r"h[oồ\?]\s*ch[ií\?]\s*m[ií\?]nh", c_lower):
        return "TP. Hồ Chí Minh"
    # 5. Hà Nội
    if any(k in c_lower for k in ["hà nội", "ha noi", "hanoi", "hòa lạc", "hoa lac", "hn"]) or re.search(r"h[aà\?]\s*n[oộ\?]i", c_lower):
        return "Hà Nội"

    return None


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
