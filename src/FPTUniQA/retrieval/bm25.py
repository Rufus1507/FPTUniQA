"""Thuật toán tìm kiếm từ khóa BM25 cho tiếng Việt. Phụ trách: TV2."""

import os
import pickle
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from rank_bm25 import BM25Plus

try:
    from pyvi import ViTokenizer
    HAS_PYVI = True
except ImportError:
    HAS_PYVI = False

VIETNAMESE_STOPWORDS = {
    "là", "của", "và", "có", "được", "trong", "cho", "này", "đó", "một", "những",
    "các", "để", "với", "từ", "theo", "về", "tại", "khi", "do", "nếu", "hoặc",
    "nhưng", "vì", "hay", "cũng", "đã", "sẽ", "đang", "rất", "không", "chưa"
}

def tokenize_vietnamese(text: str, tokenizer_type: str = "pyvi") -> List[str]:
    """Tách từ tiếng Việt có hỗ trợ pyvi và loại bỏ stopwords."""
    if tokenizer_type == "pyvi" and HAS_PYVI:
        tokens = ViTokenizer.tokenize(text).lower().split()
    else:
        text = text.lower()
        tokens = re.findall(r"\b[\w_]+\b", text)
        
    return [t for t in tokens if t not in VIETNAMESE_STOPWORDS]

class BM25Retriever:
    """Bộ truy xuất văn bản sử dụng BM25 Okapi."""

    def __init__(self, k1: float = 1.5, b: float = 0.75, tokenizer_type: str = "pyvi"):
        self.k1 = k1
        self.b = b
        self.tokenizer_type = tokenizer_type
        self.bm25: Optional[BM25Plus] = None
        self.documents: List[Dict[str, Any]] = []

    def index(self, documents: List[Dict[str, Any]]) -> None:
        """Lập chỉ mục BM25 từ danh sách documents có trường 'text'."""
        self.documents = documents
        if not documents:
            self.bm25 = None
            return
        tokenized_corpus = [
            tokenize_vietnamese(f"{doc.get('title', '')} {doc.get('text', '')}", self.tokenizer_type)
            for doc in documents
        ]
        self.bm25 = BM25Plus(tokenized_corpus, k1=self.k1, b=self.b)

    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """Truy xuất top-k tài liệu liên quan nhất kèm điểm BM25."""
        if self.bm25 is None or not self.documents:
            return []

        tokenized_query = tokenize_vietnamese(query, self.tokenizer_type)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.documents[idx], float(scores[idx])))
        return results

    def retrieve_contract2(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Truy xuất tài liệu theo format Contract 2."""
        raw_results = self.retrieve(query, top_k=top_k)
        formatted_results = []
        for doc, score in raw_results:
            metadata = doc.get("metadata", {})
            formatted_results.append({
                "doc_id": doc.get("id", ""),
                "text": doc.get("text", ""),
                "score": score,
                "source": metadata.get("doc_id", ""),
                "retrieval_strategy": "bm25",
                "metadata": {
                    "effective_date": metadata.get("effective_date", ""),
                    "applies_to_cohort": metadata.get("cohort", ""),
                    "doc_type": metadata.get("category", "")
                }
            })
        return formatted_results

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
