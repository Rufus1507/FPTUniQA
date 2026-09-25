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

    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """Truy xuất top-k tài liệu liên quan nhất kèm điểm BM25."""
        if self.bm25 is None or not self.documents:
            return []

        tokenized_query = tokenize_vietnamese(query)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.documents[idx], float(scores[idx])))
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
