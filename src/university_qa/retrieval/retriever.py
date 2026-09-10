"""Lớp bọc hợp nhất Hybrid Retriever (BM25 + FAISS + RRF). Phụ trách: TV2."""

from typing import Any, Dict, List, Optional, Tuple
from university_qa.retrieval.bm25 import BM25Retriever
from university_qa.retrieval.dense import DenseRetriever
from university_qa.retrieval.rrf import reciprocal_rank_fusion


class HybridRetriever:
    """Bộ tìm kiếm kết hợp cả từ khóa (BM25) và ngữ nghĩa sâu (Dense Vector)."""

    def __init__(
        self,
        bm25_retriever: Optional[BM25Retriever] = None,
        dense_retriever: Optional[DenseRetriever] = None,
        rrf_k: int = 60,
    ):
        self.bm25_retriever = bm25_retriever or BM25Retriever()
        self.dense_retriever = dense_retriever or DenseRetriever()
        self.rrf_k = rrf_k

    def index(self, documents: List[Dict[str, Any]]) -> None:
        """Lập chỉ mục đồng thời cho cả BM25 và FAISS."""
        self.bm25_retriever.index(documents)
        self.dense_retriever.index(documents)

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int = 20,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Truy xuất song song từ BM25 và Dense, sau đó hợp nhất bằng RRF."""
        bm25_results = self.bm25_retriever.retrieve(query, top_k=candidate_k)
        dense_results = self.dense_retriever.retrieve(query, top_k=candidate_k)

        hybrid_results = reciprocal_rank_fusion(
            ranked_runs=[bm25_results, dense_results],
            k=self.rrf_k,
            top_n=top_k,
        )
        return hybrid_results
