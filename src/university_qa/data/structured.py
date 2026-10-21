"""Parser bảng học phí, tra cứu số học và tính toán chi phí tín chỉ. Phụ trách: TV1."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from university_qa.utils.io import read_json


class StructuredDataParser:
    """Xử lý tra cứu dữ liệu dạng bảng có cấu trúc (học phí, lệ phí, chuẩn đầu ra ĐH FPT)."""

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

    def calculate_total_tuition(self, major_name: str, total_credits: int) -> Optional[int]:
        """Tính tổng học phí dự kiến dựa trên số tín chỉ."""
        matches = self.get_tuition_by_major(major_name)
        if not matches:
            return None
        credit_price = matches[0].get("credit_price_vnd", 0)
        return credit_price * total_credits
