"""Thuật toán tìm kiếm từ khóa BM25 cho tiếng Việt. Phụ trách: TV2."""

import math
import os
import pickle
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from rank_bm25 import BM25Plus
from FPTUniQA.retrieval.filter import matches_metadata_filter

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
    """Tách từ tiếng Việt có hỗ trợ pyvi, làm sạch dấu câu và loại bỏ stopwords."""
    if not text:
        return []
    # Loại bỏ dấu câu / ký tự đặc biệt, thay bằng khoảng trắng để tránh đưa dấu câu vào từ vựng BM25
    clean_text = re.sub(r"[^\w\s_]", " ", text)
    if tokenizer_type == "pyvi" and HAS_PYVI:
        tokens = ViTokenizer.tokenize(clean_text).lower().split()
    else:
        clean_text = clean_text.lower()
        tokens = re.findall(r"\b[\w_]+\b", clean_text)
        
    return [t for t in tokens if t and t not in VIETNAMESE_STOPWORDS and not re.match(r"^[^\w_]+$", t)]

class BM25Retriever:
    """Bộ truy xuất văn bản sử dụng BM25 Okapi."""

    def __init__(self, k1: float = 1.5, b: float = 0.75, tokenizer_type: str = "pyvi"):
        self.k1 = k1
        self.b = b
        self.tokenizer_type = tokenizer_type
        self.bm25: Optional[BM25Plus] = None
        self.documents: List[Dict[str, Any]] = []

    @property
    def corpus(self) -> List[Dict[str, Any]]:
        """Thuộc tính tương thích ngược cho danh sách documents."""
        return self.documents

    @corpus.setter
    def corpus(self, val: List[Dict[str, Any]]) -> None:
        self.documents = val

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

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Truy xuất top-k tài liệu liên quan nhất kèm điểm BM25."""
        if not query or not str(query).strip():
            return []
        if self.bm25 is None or not self.documents:
            return []

        tokenized_query = tokenize_vietnamese(query, self.tokenizer_type)
        if not tokenized_query:
            return []
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                break
            doc = self.documents[idx]
            if metadata_filter and not matches_metadata_filter(doc, metadata_filter):
                continue
            results.append((doc, float(scores[idx])))
            if len(results) >= top_k:
                break
        return results

    def retrieve_contract2(
        self,
        query: str,
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Truy xuất tài liệu theo format Contract 2 với điểm số chuẩn hóa [0.0, 1.0]."""
        if not query or not str(query).strip():
            return []
        raw_results = self.retrieve(query, top_k=top_k, metadata_filter=metadata_filter)
        formatted_results = []
        for doc, raw_score in raw_results:
            raw_meta = doc.get("metadata", {})
            meta = dict(raw_meta) if isinstance(raw_meta, dict) else {}
            if "effective_date" not in meta:
                meta["effective_date"] = raw_meta.get("effective_date", doc.get("effective_date", ""))
            if "applies_to_cohort" not in meta:
                meta["applies_to_cohort"] = raw_meta.get("cohort", doc.get("applies_to_cohort", ""))
            if "doc_type" not in meta:
                meta["doc_type"] = raw_meta.get("category", doc.get("doc_type", "quy_che"))

            # Chuẩn hóa điểm BM25 về đoạn [0.0, 1.0] bằng hàm hyperbolic tangent
            # math.tanh(s / 10.0) ánh xạ đơn điệu [0, inf) -> [0, 1)
            norm_score = round(min(1.0, max(0.0, float(math.tanh(max(0.0, raw_score) / 10.0)))), 4)

            formatted_results.append({
                "doc_id": doc.get("id") or doc.get("doc_id") or meta.get("doc_id", ""),
                "title": doc.get("title") or meta.get("title", "Tài liệu học vụ"),
                "text": doc.get("text", ""),
                "content": doc.get("text", ""),
                "score": norm_score,
                "source": doc.get("source") or meta.get("url") or meta.get("doc_id", doc.get("title", "")),
                "category": doc.get("doc_type") or meta.get("doc_type", meta.get("category", "quy_che")),
                "retrieval_strategy": "bm25",
                "metadata": meta,
            })
        return formatted_results

    def save(self, dir_path: Union[str, Path]) -> None:
        """Lưu chỉ mục và dữ liệu văn bản ra đĩa."""
        path = Path(dir_path)
        if path.suffix == ".pkl":
            file_path = path
            file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)
            file_path = path / "bm25_index.pkl"
        with open(file_path, "wb") as f:
            pickle.dump({"bm25": self.bm25, "documents": self.documents}, f)

    def load(self, dir_path: Union[str, Path]) -> None:
        """Nạp chỉ mục BM25 từ đĩa."""
        p = Path(dir_path)
        if p.is_file() or (p.suffix == ".pkl" and p.exists()):
            file_path = p
        else:
            file_path = p / "bm25_index.pkl"

        if not file_path.exists():
            raise FileNotFoundError(f"Không tìm thấy index tại {file_path}")
        with open(file_path, "rb") as f:
            data = pickle.load(f)
            self.bm25 = data["bm25"]
            self.documents = data["documents"]
