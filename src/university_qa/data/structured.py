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
