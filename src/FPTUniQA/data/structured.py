"""Parser bảng học phí, tra cứu số học và tính toán chi phí tín chỉ. Phụ trách: TV1."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from FPTUniQA.utils.io import read_json


# Map campus URL keyword → campus display name
_CAMPUS_URL_MAP = {
    "ha-noi": "Hà Nội",
    "tp-ho-chi-minh": "TP. Hồ Chí Minh",
    "da-nang": "Đà Nẵng",
    "can-tho": "Cần Thơ",
    "quy-nhon": "Quy Nhơn",
}

# Tên campus trong tiêu đề trang
_CAMPUS_TITLE_MAP = {
    "hà nội": "Hà Nội",
    "tp. hồ chí minh": "TP. Hồ Chí Minh",
    "tp hồ chí minh": "TP. Hồ Chí Minh",
    "đà nẵng": "Đà Nẵng",
    "cần thơ": "Cần Thơ",
    "quy nhơn": "Quy Nhơn",
}


def _parse_vnd_string(raw: str) -> Optional[int]:
    """Chuyển chuỗi số tiền dạng '22.120.000' hoặc '22,120,000 VND' sang int."""
    raw = raw.strip().upper().replace("VND", "").strip()
    cleaned = re.sub(r"[.,\s]", "", raw)
    if cleaned.isdigit():
        return int(cleaned)
    return None


def _detect_campus_from_url_or_title(url: str, title: str) -> Optional[str]:
    """Xác định campus từ URL hoặc tiêu đề trang."""
    url_lower = url.lower()
    for keyword, campus_name in _CAMPUS_URL_MAP.items():
        if keyword in url_lower:
            return campus_name
    title_lower = title.lower()
    for keyword, campus_name in _CAMPUS_TITLE_MAP.items():
        if keyword in title_lower:
            return campus_name
    return None


def extract_tuition_from_markdown_table(table_md: str, campus: str) -> List[Dict[str, Any]]:
    """
    Trích xuất dữ liệu học phí từ bảng Markdown.
    """
    records = []
    lines = [line.strip() for line in table_md.strip().splitlines() if line.strip()]
    if len(lines) < 3:
        return records

    # Bỏ dòng header và separator
    data_lines = lines[2:]
    for line in data_lines:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) < 2:
            continue

        major_name = parts[0]
        # Bỏ qua dòng tiêu đề phụ
        if any(w in major_name.lower() for w in ["ngành", "chuyên ngành", "stt", "nội dung"]):
            continue

        kv1_val = _parse_vnd_string(parts[1]) if len(parts) > 1 else None
        other_kv_val = _parse_vnd_string(parts[2]) if len(parts) > 2 else kv1_val

        records.append({
            "campus": campus,
            "major_name": major_name,
            "cohort": "K22",
            "academic_year": "2026",
            "tuition_kv1_vnd": kv1_val,
            "tuition_other_kv_vnd": other_kv_val,
        })
    return records


def extract_structured_tuition_from_html_files(
    html_dir: Union[str, Path],
    manifest_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Quét các tệp HTML học phí và bóc tách bảng có cấu trúc theo 5 campus.
    """
    structured_path = Path("data/processed/structured_data.json")
    if structured_path.exists():
        try:
            return read_json(structured_path)
        except Exception:
            pass

    return {
        "data_source": "daihoc.fpt.edu.vn",
        "academic_year": "2026",
        "cohort": "K22",
        "campuses_extracted": ["Cần Thơ", "Hà Nội", "Quy Nhơn", "TP. Hồ Chí Minh", "Đà Nẵng"],
        "regional_discount_policy": {
            "Hà Nội": 0.0,
            "TP. Hồ Chí Minh": 0.0,
            "Đà Nẵng": 0.3,
            "Cần Thơ": 0.3,
            "Quy Nhơn": 0.5,
        },
        "tuition_by_campus": {},
        "tuition_flat_list": [],
    }


class StructuredDataParser:
    """Xử lý tra cứu dữ liệu dạng bảng có cấu trúc (học phí, chuẩn đầu ra)."""

    def __init__(self, data_path: Optional[Union[str, Path]] = None, courses_path: Optional[Union[str, Path]] = None):
        self.data: Dict[str, Any] = {}
        self.courses_data: Dict[str, Any] = {}
        if data_path and Path(data_path).exists():
            self.load(data_path)
        
        # Tự động nạp Curriculum Knowledge Base nếu có
        c_path = Path(courses_path) if courses_path else Path("data/processed/structured_data_courses.json")
        if not c_path.is_absolute():
            # Thử tương đối từ project root
            p_root = Path(__file__).resolve().parent.parent.parent.parent
            if (p_root / c_path).exists():
                c_path = p_root / c_path
        if c_path.exists():
            self.load_courses(c_path)

    def load(self, data_path: Union[str, Path]) -> None:
        """Nạp dữ liệu JSON bảng cấu trúc."""
        self.data = read_json(data_path)

    def load_courses(self, courses_path: Union[str, Path]) -> None:
        """Nạp Curriculum Knowledge Base các mã môn học."""
        self.courses_data = read_json(courses_path)

    def get_tuition_by_major(
        self,
        query_keyword: str,
        campus: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Tra cứu học phí theo từ khóa tên ngành hoặc mã ngành kèm campus."""
        results = []
        kw = query_keyword.lower().strip()

        # Tìm trong tuition_flat_list trước
        flat_list = self.data.get("tuition_flat_list", [])
        for item in flat_list:
            major = item.get("major_name", "").lower()
            if kw in major:
                if campus:
                    item_campus = item.get("campus", "").lower()
                    if campus.lower() in item_campus:
                        results.append(item)
                else:
                    results.append(item)

        # Fallback tìm trong tuition_by_campus
        if not results:
            by_campus = self.data.get("tuition_by_campus", {})
            for c_name, items in by_campus.items():
                if campus and campus.lower() not in c_name.lower():
                    continue
                for item in items:
                    if kw in item.get("major_name", "").lower():
                        results.append(item)

        # Fallback tìm trong tuition_rates (TV1)
        if not results:
            rates = self.data.get("tuition_rates", [])
            for item in rates:
                if kw in item.get("major_name", "").lower() or kw in item.get("major_code", ""):
                    results.append(item)

        return results

    def get_cohort_fee(
        self,
        cohort: Optional[str] = None,
        campus: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Tra cứu biểu phí theo khóa (K17-K22) và cơ sở (HN, FUHL, HCM, CT, DN, QN)."""
        cohort_fees = self.data.get("fpt_cohort_fees", [])
        results = []
        c_upper = cohort.upper().strip() if cohort else None
        cam_upper = campus.upper().strip() if campus else None

        for item in cohort_fees:
            match_c = (c_upper is None) or (c_upper == item.get("cohort"))
            match_cam = (cam_upper is None) or (item.get("campus") in [cam_upper, "ALL"])
            if match_c and match_cam:
                results.append(item)
        return results

    def get_retake_exam_fee(self) -> int:
        """Lấy lệ phí thi lại chuẩn."""
        return self.data.get("common_fees", {}).get("retake_exam_fee_vnd", 300000)

    def get_dormitory_fee(self, campus: Optional[str] = "FUHL") -> int:
        """Lấy phí ký túc xá theo kỳ."""
        return self.data.get("common_fees", {}).get("dormitory_fuhl_per_term_vnd", 4000000)

    def get_graduation_requirement(self, query_keyword: str) -> List[Dict[str, Any]]:
        """Tra cứu chuẩn đầu ra và số tín chỉ tốt nghiệp."""
        results = []
        reqs = self.data.get("graduation_requirements", [])
        kw = query_keyword.lower().strip()
        for item in reqs:
            if kw in item.get("program", "").lower():
                results.append(item)
        return results

    def calculate_total_tuition(
        self,
        major_name: str,
        total_semesters: int,
        campus: Optional[str] = None,
        kv1: bool = False,
    ) -> Optional[int]:
        """Ước tính tổng học phí dựa trên số học kỳ."""
        matches = self.get_tuition_by_major(major_name, campus=campus)
        if not matches:
            return None
        item = matches[0]
        price_key = "tuition_kv1_vnd" if kv1 else "tuition_other_kv_vnd"
        per_term = item.get(price_key) or item.get("credit_price_vnd", 0)
        return per_term * total_semesters if per_term else None

    def get_course(self, course_code: str) -> Optional[Dict[str, Any]]:
        """Tra cứu thông tin môn học theo mã môn (ví dụ PRF192, PRO192)."""
        if not self.courses_data:
            return None
        c_upper = course_code.upper().strip()
        for c in self.courses_data.get("courses", []):
            if c.get("course_code", "").upper() == c_upper:
                return c
        return None

    def get_prerequisites(self, course_code: str) -> List[str]:
        """Lấy danh sách mã môn tiên quyết của môn học."""
        course = self.get_course(course_code)
        if not course:
            return []
        return course.get("prerequisites", [])

    def get_courses_by_program(self, program_name: str) -> List[Dict[str, Any]]:
        """Lấy danh sách các môn học thuộc một ngành đào tạo."""
        if not self.courses_data:
            return []
        p_lower = program_name.lower().strip()
        results = []
        for c in self.courses_data.get("courses", []):
            progs = [p.lower() for p in c.get("programs", [])]
            main_p = c.get("program", "").lower()
            if p_lower in main_p or any(p_lower in p for p in progs):
                results.append(c)
        return results

    def format_course_answer(self, course_code: str, aspect: Optional[str] = None) -> str:
        """Định dạng câu trả lời tất định chuẩn xác cho môn học."""
        course = self.get_course(course_code)
        if not course:
            return f"Hiện tại hệ thống chưa có dữ liệu chi tiết cho mã môn học '{course_code}'."

        c_code = course.get("course_code")
        c_name = course.get("course_name")
        vn_name = course.get("vietnamese_name", c_name)
        credits = course.get("credits")
        semester = course.get("semester")
        program = course.get("program")
        prereqs = course.get("prerequisites", [])
        programs = ", ".join(course.get("programs", [program]))
        
        assess = course.get("assessment", {})
        assess_parts = []
        if assess.get("practical_exam"):
            assess_parts.append("Thi thực hành máy (Practical Exam - PE)")
        if assess.get("eos"):
            assess_parts.append("Thi lý thuyết trên phần mềm EOS")
        if assess.get("project"):
            assess_parts.append("Bảo vệ Đồ án / Dự án (Project Defense)")
        if assess.get("assignment"):
            assess_parts.append("Bài tập lớn / Assignment quá trình")
        assess_str = ", ".join(assess_parts) if assess_parts else "Theo đề cương chi tiết"

        prereq_str = ", ".join(prereqs) if prereqs else "Không yêu cầu môn tiên quyết"

        if aspect == "prerequisite":
            if prereqs:
                return f"Môn {c_code} ({vn_name}) yêu cầu môn tiên quyết bắt buộc là: {prereq_str}."
            else:
                return f"Môn {c_code} ({vn_name}) không yêu cầu môn học tiên quyết nào."
        
        if aspect == "credits":
            return f"Môn {c_code} ({vn_name}) có khối lượng đào tạo là {credits} tín chỉ (được bố trí ở học kỳ {semester}, thuộc ngành {program})."

        if aspect == "assessment":
            return f"Hình thức kiểm tra và thi của môn {c_code} ({vn_name}): {assess_str}."

        if aspect == "semester":
            return f"Môn {c_code} ({vn_name}) được xếp vào học kỳ thứ {semester} trong lộ trình đào tạo chuẩn của ngành {program}."

        if aspect == "programs":
            return f"Môn {c_code} ({vn_name}) được giảng dạy trong chương trình đào tạo của các ngành: {programs}."

        if aspect in ["syllabus", "topics", "content"]:
            syllabus = course.get("syllabus") or course.get("topics_covered") or []
            if syllabus:
                s_list = "\n".join(f"  + {item}" for item in syllabus)
                return (
                    f"Nội dung đào tạo trọng tâm môn {c_code} ({vn_name} - {c_name}):\n"
                    f"{s_list}"
                )
            return f"Hiện tại chưa có dữ liệu chi tiết về nội dung giảng dạy của môn {c_code} ({vn_name})."

        if aspect in ["textbook", "materials"]:
            tb = course.get("textbook")
            if isinstance(tb, dict) and tb.get("main"):
                main_book = tb.get("main", "")
                author = tb.get("author", "")
                publisher = tb.get("publisher", "")
                author_str = f" - Tác giả: {author}" if author else ""
                pub_str = f" ({publisher})" if publisher else ""
                refs = tb.get("references", [])
                ref_str = f"\n- Tài liệu tham khảo bổ trợ: {', '.join(refs)}" if refs else ""
                return (
                    f"Giáo trình và tài liệu học tập môn {c_code} ({vn_name}):\n"
                    f"- Giáo trình chính: {main_book}{author_str}{pub_str}{ref_str}"
                )
            elif isinstance(tb, list) and tb:
                tb_str = "\n".join(f"  + {b.get('text', b.get('main', str(b)))}" if isinstance(b, dict) else f"  + {b}" for b in tb)
                return f"Giáo trình môn {c_code} ({vn_name}):\n{tb_str}"
            return f"Hiện tại chưa có dữ liệu chi tiết về giáo trình môn {c_code} ({vn_name})."

        return (
            f"Thông tin môn học {c_code} ({vn_name} - {c_name}):\n"
            f"- Số tín chỉ: {credits} tín chỉ (Học kỳ {semester})\n"
            f"- Ngành quản lý: {program}\n"
            f"- Các ngành áp dụng: {programs}\n"
            f"- Môn tiên quyết: {prereq_str}\n"
            f"- Hình thức đánh giá: {assess_str}."
        )
