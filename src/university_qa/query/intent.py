"""Phân loại ý định người dùng: Factoid / Bảng biểu (Structured) / Ngoài miền (OOD). Phụ trách: TV3."""

import re
from enum import Enum
from typing import Dict, Tuple


class QueryIntent(str, Enum):
    FACTOID = "factoid"          # Câu hỏi quy chế, thủ tục, văn bản
    STRUCTURED = "structured"    # Câu hỏi liên quan bảng biểu học phí, số tín chỉ
    OOD = "ood"                  # Câu hỏi ngoài miền (chính trị, thời tiết, giải trí...)


class IntentClassifier:
    """Bộ phân loại ý định dựa trên từ khóa và mẫu biểu thức chính quy."""

    # Từ khóa nhận diện ngoài miền
    OOD_KEYWORDS = [
        "thời tiết", "nấu ăn", "món phở", "bóng đá", "world cup",
        "tổng thống", "thủ đô", "giá vàng", "chứng khoán",
        "phim", "bài hát", "ca sĩ", "diễn viên", "windows 11"
    ]

    # Từ khóa nhận diện bảng học phí / số học
    STRUCTURED_KEYWORDS = [
        "học phí", "bao nhiêu tiền", "giá tín chỉ", "chi phí",
        "tiền học", "mức thu", "bao nhiêu vnd", "bảng học phí"
    ]

    def classify(self, query: str) -> Tuple[QueryIntent, float]:
        """Phân loại ý định câu truy vấn và trả về độ tin cậy."""
        q_lower = query.lower()

        # Kiểm tra OOD
        for kw in self.OOD_KEYWORDS:
            if kw in q_lower:
                return QueryIntent.OOD, 0.95

        # Kiểm tra Structured (Học phí / bảng tính)
        for kw in self.STRUCTURED_KEYWORDS:
            if kw in q_lower:
                return QueryIntent.STRUCTURED, 0.90

        # Mặc định là câu hỏi tra cứu quy chế (Factoid)
        return QueryIntent.FACTOID, 0.85
