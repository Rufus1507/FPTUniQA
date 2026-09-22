"""Parser bảng học phí, tra cứu số học và tính toán chi phí tín chỉ. Phụ trách: TV1."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from university_qa.utils.io import read_json


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
    # Xóa tất cả dấu chấm và dấu phẩy
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
    Trích xuất dữ liệu học phí từ một bảng Markdown dạng:
    | Ngành/Chuyên ngành | KV1 | Các KV khác |
    |---|---|---|
    | Công nghệ thông tin | 22.120.000 | 31.600.000 |
    ...

    Args:
        table_md: Nội dung bảng ở định dạng Markdown.
        campus: Tên campus.

    Returns:
        Danh sách dict mỗi dòng trong bảng học phí.
    """
    rows = []
    lines = [ln.strip() for ln in table_md.splitlines() if ln.strip()]
    header = []
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if not cells:
            continue
        # Bỏ dòng phân cách |---|---|
        if all(re.match(r"^-+$", c) for c in cells):
            continue
        if not header:
            header = cells
            continue

        if len(cells) < 2:
            continue

        major_name = cells[0]
        # Bỏ qua dòng nhóm ngành (không có số tiền)
        if len(cells) == 1 or not any(char.isdigit() for char in "".join(cells[1:])):
            continue

        record: Dict[str, Any] = {
            "campus": campus,
            "major_name": major_name,
            "cohort": "K22",
            "academic_year": "2026",
        }

        # Ánh xạ các cột từ header
        for col_idx, col_name in enumerate(header[1:], start=1):
            if col_idx < len(cells):
                amount = _parse_vnd_string(cells[col_idx])
                if amount is not None:
                    col_key = col_name.lower().replace(" ", "_").replace("/", "_")
                    record[col_key] = amount

        # Trích xuất khu vực ưu đãi từ tên cột
        # Chuẩn: cột KV1, cột "Các KV khác"
        for col_idx, col_name in enumerate(header[1:], start=1):
            if col_idx >= len(cells):
                break
            amount = _parse_vnd_string(cells[col_idx])
            if amount is None:
                continue
            col_lower = col_name.lower()
            if "kv1" in col_lower or "khu vực 1" in col_lower:
                record["tuition_kv1_vnd"] = amount
            elif "khác" in col_lower or "kv khác" in col_lower or "khu vực khác" in col_lower:
                record["tuition_other_kv_vnd"] = amount

        if major_name and ("tuition_kv1_vnd" in record or "tuition_other_kv_vnd" in record):
            rows.append(record)

    return rows


def extract_structured_tuition_from_html_files(
    html_dir: Union[str, Path],
    manifest_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Duyệt thư mục HTML và trích xuất toàn bộ dữ liệu bảng học phí K22
    cho tất cả campus.

    Returns:
        Dict có cấu trúc phù hợp cho data/processed/structured_data.json
    """
    try:
        from bs4 import BeautifulSoup
        from university_qa.data.html_extractor import extract_from_html, _extract_tables_as_markdown
    except ImportError:
        return {}

    html_dir = Path(html_dir)

    # Nạp manifest để lấy URL → filename mapping
    url_by_file: Dict[str, str] = {}
    if manifest_path:
        mp = Path(manifest_path)
        if mp.exists():
            with open(mp, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    raw_file = rec.get("raw_file", "")
                    url = rec.get("url", "")
                    if raw_file and url:
                        url_by_file[Path(raw_file).name] = url

    all_tuition_rows: List[Dict[str, Any]] = []
    seen_campuses: set = set()

    html_files = sorted(html_dir.glob("*.html"))
    for fpath in html_files:
        url = url_by_file.get(fpath.name, "")
        if "hoc-phi" not in url.lower() and "học phí" not in fpath.name.lower():
            continue  # chỉ xử lý file học phí

        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        tables_md = _extract_tables_as_markdown(soup)

        campus = _detect_campus_from_url_or_title(url, title)
        if not campus:
            continue

        seen_campuses.add(campus)

        for table_md in tables_md:
            rows = extract_tuition_from_markdown_table(table_md, campus)
            all_tuition_rows.extend(rows)

    # Phát hiện ưu đãi vùng miền từ biểu phí
    # Hà Nội và HCM: giá chuẩn (không ưu đãi)
    # Đà Nẵng, Cần Thơ: giảm ~30%
    # Quy Nhơn: giảm ~50%
    regional_discount = {
        "Hà Nội": 0.0,
        "TP. Hồ Chí Minh": 0.0,
        "Đà Nẵng": 0.3,
        "Cần Thơ": 0.3,
        "Quy Nhơn": 0.5,
    }

    return {
        "data_source": "daihoc.fpt.edu.vn",
        "academic_year": "2026",
        "cohort": "K22",
        "note": "Học phí áp dụng cho tân sinh viên khóa K22 nhập học năm 2026",
        "campuses_extracted": sorted(seen_campuses),
        "regional_discount_policy": regional_discount,
        "tuition_by_campus": _group_tuition_by_campus(all_tuition_rows),
        "tuition_flat_list": all_tuition_rows,
        # Giữ lại graduation_requirements từ file cũ nếu có
        "graduation_requirements": [
            {
                "program": "Kỹ sư Công nghệ Thông tin",
                "total_credits": 150,
                "mandatory_credits": 120,
                "elective_credits": 30,
                "internship_credits": 10,
                "thesis_credits": 10,
                "min_gpa": 2.0,
                "foreign_language": "TOEIC 550 hoặc IELTS 5.5",
            },
            {
                "program": "Cử nhân Quản trị Kinh doanh",
                "total_credits": 135,
                "mandatory_credits": 105,
                "elective_credits": 30,
                "internship_credits": 6,
                "thesis_credits": 9,
                "min_gpa": 2.0,
                "foreign_language": "TOEIC 500 hoặc IELTS 5.0",
            },
        ],
    }


def _group_tuition_by_campus(rows: List[Dict[str, Any]]) -> Dict[str, List]:
    """Nhóm danh sách học phí theo campus."""
    result: Dict[str, List] = {}
    for row in rows:
        campus = row.get("campus", "Unknown")
        if campus not in result:
            result[campus] = []
        result[campus].append(row)
    return result


# ---------------------------------------------------------------------------- #
# StructuredDataParser — giữ nguyên interface cũ để tương thích TV2/TV3
# ---------------------------------------------------------------------------- #

class StructuredDataParser:
    """Xử lý tra cứu dữ liệu dạng bảng có cấu trúc (học phí, chuẩn đầu ra)."""

    def __init__(self, data_path: Optional[Union[str, Path]] = None):
        self.data: Dict[str, Any] = {}
        if data_path and Path(data_path).exists():
            self.load(data_path)

    def load(self, data_path: Union[str, Path]) -> None:
        """Nạp dữ liệu JSON bảng cấu trúc."""
        self.data = read_json(data_path)

    def get_tuition_by_major(
        self,
        query_keyword: str,
        campus: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Tra cứu học phí theo từ khóa tên ngành, tùy chọn lọc thêm theo campus.

        Args:
            query_keyword: Tên ngành / chuyên ngành cần tra cứu.
            campus: Tên campus (ví dụ: "Hà Nội", "Đà Nẵng"). None = tất cả.
        """
        results = []
        kw = query_keyword.lower().strip()

        # Tìm trong flat list mới
        flat_list = self.data.get("tuition_flat_list", [])
        for item in flat_list:
            major_lower = item.get("major_name", "").lower()
            if kw in major_lower:
                if campus is None or item.get("campus", "").lower() == campus.lower():
                    results.append(item)

        # Fallback: tìm trong tuition_rates cũ (tương thích backward)
        if not results:
            rates = self.data.get("tuition_rates", [])
            for item in rates:
                if kw in item.get("major_name", "").lower() or kw in item.get("major_code", ""):
                    results.append(item)

        return results

    def get_tuition_by_campus(self, campus: str) -> List[Dict[str, Any]]:
        """Tra cứu toàn bộ biểu học phí của một campus."""
        campus_data = self.data.get("tuition_by_campus", {})
        # Khớp không phân biệt hoa/thường
        for key, items in campus_data.items():
            if key.lower() == campus.lower() or campus.lower() in key.lower():
                return items
        return []

    def calculate_total_tuition(
        self,
        major_name: str,
        total_semesters: int,
        campus: Optional[str] = None,
        kv1: bool = False,
    ) -> Optional[int]:
        """
        Ước tính tổng học phí dựa trên số học kỳ.

        Args:
            major_name: Tên ngành.
            total_semesters: Số học kỳ dự kiến.
            campus: Campus (nếu None, lấy giá trị đầu tiên tìm thấy).
            kv1: True nếu sinh viên thuộc Khu vực 1 (được ưu đãi giá KV1).
        """
        matches = self.get_tuition_by_major(major_name, campus)
        if not matches:
            return None
        item = matches[0]
        price_key = "tuition_kv1_vnd" if kv1 else "tuition_other_kv_vnd"
        per_semester = item.get(price_key) or item.get("estimated_term_tuition_vnd", 0)
        return per_semester * total_semesters if per_semester else None
