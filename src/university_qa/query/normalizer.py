"""Chuẩn hóa từ viết tắt, thuật ngữ quy chế và chính tả tiếng Việt. Phụ trách: TV3."""

import re
import unicodedata
from typing import Dict


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
