"""Thuật toán tìm kiếm từ khóa BM25 cho tiếng Việt. Phụ trách: TV2."""

import os
import pickle
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from rank_bm25 import BM25Okapi


def tokenize_vietnamese(text: str) -> List[str]:
    """Tách từ cơ bản cho tiếng Việt (chuyển chữ thường, xóa dấu câu)."""
    text = text.lower()
    tokens = re.findall(r"\b[\w_]+\b", text)
    return tokens


class BM25Retriever:
    """Bộ truy xuất văn bản sử dụng BM25 Okapi."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Dict[str, Any]] = []

    def index(self, documents: List[Dict[str, Any]]) -> None:
        """Lập chỉ mục BM25 từ danh sách documents có trường 'text'."""
        self.documents = documents
        tokenized_corpus = [
            tokenize_vietnamese(f"{doc.get('title', '')} {doc.get('text', '')}")
            for doc in documents
        ]
        self.bm25 = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)

    @staticmethod
    def _matches_filter(
        doc: Dict[str, Any],
        filter_cohort: Optional[str] = None,
        filter_campus: Optional[str] = None,
    ) -> bool:
        """Kiểm tra tài liệu có khớp với bộ lọc khóa và cơ sở hay không."""
        if filter_cohort:
            target_cohort = filter_cohort.upper().strip()
            doc_cohorts = doc.get("applies_to_cohort")
            if not doc_cohorts:
                c = doc.get("metadata", {}).get("cohort")
                doc_cohorts = [c] if c else ["ALL"]
            cohorts_upper = [str(c).upper().strip() for c in doc_cohorts]
            if "ALL" not in cohorts_upper and target_cohort not in cohorts_upper:
                return False

        if filter_campus:
            target_campus = filter_campus.upper().strip()
            doc_campus = str(doc.get("campus") or doc.get("metadata", {}).get("campus", "ALL")).upper().strip()
            campus_match = (
                doc_campus == "ALL"
                or doc_campus == target_campus
                or (doc_campus in ["HN", "FUHL"] and target_campus in ["HN", "FUHL"])
            )
            if not campus_match:
                return False

        return True

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filter_cohort: Optional[str] = None,
        filter_campus: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Truy xuất top-k tài liệu liên quan nhất kèm điểm BM25 và lọc siêu dữ liệu cứng."""
        if self.bm25 is None or not self.documents:
            return []

        tokenized_query = tokenize_vietnamese(query)
        scores = self.bm25.get_scores(tokenized_query)
        # Khử hiện tượng điểm âm (negative IDF) khi corpus quá nhỏ
        safe_scores = [max(float(s), 0.0) for s in scores]

        # Lọc trước danh sách chỉ mục hợp lệ theo Metadata Pre-filtering
        valid_indices = [
            i
            for i in range(len(self.documents))
            if self._matches_filter(self.documents[i], filter_cohort, filter_campus)
        ]

        if not valid_indices:
            return []

        def get_sort_key(i: int):
            doc_tokens = set(tokenize_vietnamese(f"{self.documents[i].get('title', '')} {self.documents[i].get('text', '')}"))
            overlap_count = sum(1 for t in tokenized_query if t in doc_tokens)
            return (safe_scores[i], overlap_count)

        top_indices = sorted(valid_indices, key=get_sort_key, reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            doc_tokens = set(tokenize_vietnamese(f"{self.documents[idx].get('title', '')} {self.documents[idx].get('text', '')}"))
            overlap_count = sum(1 for t in tokenized_query if t in doc_tokens)
            if safe_scores[idx] > 0 or overlap_count > 0:
                effective_score = float(max(safe_scores[idx], 0.1 * overlap_count))
                results.append((self.documents[idx], effective_score))
        return results

    def save(self, dir_path: Union[str, Path]) -> None:
        """Lưu chỉ mục và dữ liệu văn bản ra đĩa."""
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "bm25_index.pkl", "wb") as f:
            pickle.dump({"bm25": self.bm25, "documents": self.documents}, f)

    def load(self, dir_path: Union[str, Path]) -> None:
        """Nạp chỉ mục BM25 từ đĩa."""
        path = Path(dir_path) / "bm25_index.pkl"
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy index tại {path}")
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.bm25 = data["bm25"]
            self.documents = data["documents"]
