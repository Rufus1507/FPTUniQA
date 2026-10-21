"""Chuẩn hóa từ viết tắt, thuật ngữ quy chế và chính tả tiếng Việt. Phụ trách: TV3."""

import re
import unicodedata
from typing import Dict, Optional, Tuple


class QueryNormalizer:
    """Chuẩn hóa câu truy vấn của sinh viên trước khi đưa vào bộ tìm kiếm."""

    ACRONYMS: Dict[str, str] = {
        r"\bctđt\b": "chương trình đào tạo",
        r"\bđkhp\b": "đăng ký học phần",
        r"\bgpa\b": "điểm trung bình tích lũy",
        r"\bcntt\b": "công nghệ thông tin",
        r"\bktpm\b": "kỹ thuật phần mềm",
        r"\bkhmt\b": "khoa học máy tính",
        r"\bqtkd\b": "quản trị kinh doanh",
        r"\bsv\b": "sinh viên",
        r"\bcs\b": "cơ sở",
        r"\bhb\b": "học bổng",
        r"\bhp\b": "học phí",
        r"\btin chi\b": "tín chỉ",
        r"\btchi\b": "tín chỉ",
        r"\btl\b": "tích lũy",
    }

    def __init__(self, custom_acronyms: Dict[str, str] = None):
        self.acronyms = self.ACRONYMS.copy()
        if custom_acronyms:
            self.acronyms.update(custom_acronyms)

    def normalize(self, query: str) -> str:
        """Thực hiện làm sạch và mở rộng từ viết tắt."""
        if not query:
            return ""

        # Chuẩn hóa Unicode NFC
        query = unicodedata.normalize("NFC", query)
        query = query.strip()

        # Thay thế từ viết tắt
        lower_query = query.lower()
        for pattern, full_text in self.acronyms.items():
            lower_query = re.sub(pattern, full_text, lower_query, flags=re.IGNORECASE)

        # Xóa các ký tự thừa liên tiếp
        lower_query = re.sub(r"[ \t]+", " ", lower_query)
        return lower_query.strip()

    @staticmethod
    def extract_cohort_and_campus(query: str) -> Tuple[Optional[str], Optional[str]]:
        """Bóc tách thực thể khóa học (K17-K22) và cơ sở (Campus) từ câu hỏi."""
        q = query.lower()
        cohort = None
        campus = None

        # Bắt khóa: k17, k18, k19, k20, k21, k22, khóa 17, v.v.
        cohort_match = re.search(r"\b(k1[7-9]|k2[0-2]|khóa\s*1[7-9]|khóa\s*2[0-2])\b", q)
        if cohort_match:
            c_raw = cohort_match.group(1).replace("khóa", "").strip()
            if not c_raw.startswith("k"):
                c_raw = "k" + c_raw
            cohort = c_raw.upper()

        # Bắt cơ sở
        if any(w in q for w in ["hòa lạc", "hoa lac", "fuhl"]):
            campus = "FUHL"
        elif any(w in q for w in ["hà nội", "ha noi", "hn"]):
            campus = "HN"
        elif any(w in q for w in ["hồ chí minh", "ho chi minh", "hcm", "sài gòn", "tp.hcm", "tphcm"]):
            campus = "HCM"
        elif any(w in q for w in ["cần thơ", "can tho", "ct"]):
            campus = "CT"
        elif any(w in q for w in ["đà nẵng", "da nang", "dn"]):
            campus = "DN"
        elif any(w in q for w in ["quy nhơn", "quy nhon", "qn"]):
            campus = "QN"

        return cohort, campus
