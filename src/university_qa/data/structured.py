"""Parser bảng học phí, tra cứu số học và tính toán chi phí tín chỉ. Phụ trách: TV1."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from university_qa.utils.io import read_json


class StructuredDataParser:
    """Xử lý tra cứu dữ liệu dạng bảng có cấu trúc (học phí, chuẩn đầu ra)."""

    def __init__(self, data_path: Optional[Union[str, Path]] = None):
        self.data: Dict[str, Any] = {}
        if data_path and Path(data_path).exists():
            self.load(data_path)

    def load(self, data_path: Union[str, Path]) -> None:
        """Nạp dữ liệu JSON bảng cấu trúc."""
        self.data = read_json(data_path)

    def get_tuition_by_major(self, query_keyword: str) -> List[Dict[str, Any]]:
        """Tra cứu học phí theo từ khóa tên ngành hoặc mã ngành."""
        results = []
        rates = self.data.get("tuition_rates", [])
        kw = query_keyword.lower().strip()
        for item in rates:
            if kw in item.get("major_name", "").lower() or kw in item.get("major_code", ""):
                results.append(item)
        return results

    def calculate_total_tuition(self, major_name: str, total_credits: int) -> Optional[int]:
        """Tính tổng học phí dự kiến dựa trên số tín chỉ."""
        matches = self.get_tuition_by_major(major_name)
        if not matches:
            return None
        credit_price = matches[0].get("credit_price_vnd", 0)
        return credit_price * total_credits
