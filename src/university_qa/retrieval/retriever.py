"""Lớp bọc hợp nhất Hybrid Retriever (BM25 + FAISS + RRF). Phụ trách: TV2."""

from pathlib import Path
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
        auto_load: bool = True,
    ):
        self.rrf_k = rrf_k

        if bm25_retriever is not None:
            self.bm25_retriever = bm25_retriever
        else:
            self.bm25_retriever = BM25Retriever()
            bm25_dir = Path("data/processed/bm25_index")
            if auto_load and (bm25_dir / "bm25_index.pkl").exists():
                try:
                    self.bm25_retriever.load(bm25_dir)
                except Exception:
                    pass

        if dense_retriever is not None:
            self.dense_retriever = dense_retriever
        else:
            self.dense_retriever = DenseRetriever()
            faiss_dir = Path("data/processed/faiss_index")
            if auto_load and (faiss_dir / "dense.index").exists():
                try:
                    self.dense_retriever.load(faiss_dir)
                except Exception:
                    pass


    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """Lập chỉ mục đồng thời cho cả BM25 và FAISS."""
        self.bm25_retriever.index(documents)
        self.dense_retriever.build_index(documents)

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int = 20,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Truy xuất song song từ BM25 và Dense, sau đó hợp nhất bằng RRF, áp dụng filter sau khi fuse."""
        bm25_results = self.bm25_retriever.retrieve(query, top_k=candidate_k)
        
        if self.dense_retriever._faiss_index is None:
            # Fallback nếu dense chưa được index
            fused_results = bm25_results
        else:
            dense_results = self.dense_retriever.retrieve(query, top_k=candidate_k)
            fused_results = reciprocal_rank_fusion(
                ranked_runs=[bm25_results, dense_results],
                k=self.rrf_k,
                top_n=candidate_k * 2,
            )

        if metadata_filter:
            filtered_results = []
            for doc, score in fused_results:
                doc_meta = doc.get("metadata", {})
                match = all(doc_meta.get(k) == v for k, v in metadata_filter.items())
                if match:
                    filtered_results.append((doc, score))
            fused_results = filtered_results

        return fused_results[:top_k]

    def retrieve_contract2(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int = 20,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        results = self.retrieve(query, top_k, candidate_k, metadata_filter)
        output = []
        for doc, score in results:
            output.append({
                "doc_id": doc.get("id", doc.get("doc_id")),
                "text": doc.get("text", ""),
                "score": score,
                "source": doc.get("title", ""),
                "retrieval_strategy": "hybrid_rrf",
                "metadata": doc.get("metadata", {})
            })
        return output
