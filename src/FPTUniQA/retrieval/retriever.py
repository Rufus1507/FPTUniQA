"""Lớp bọc hợp nhất Hybrid Retriever (BM25 + FAISS + RRF). Phụ trách: TV2."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from FPTUniQA.retrieval.bm25 import BM25Retriever
from FPTUniQA.retrieval.dense import DenseRetriever
from FPTUniQA.retrieval.rrf import reciprocal_rank_fusion
from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.retrieval.retriever")


class HybridRetriever:
    """Bộ tìm kiếm kết hợp cả từ khóa (BM25) và ngữ nghĩa sâu (Dense Vector)."""

    def __init__(
        self,
        bm25_retriever: Optional[BM25Retriever] = None,
        dense_retriever: Optional[DenseRetriever] = None,
        rrf_k: int = 60,
        weights: Optional[List[float]] = None,
        auto_load: bool = True,
    ):
        self.rrf_k = rrf_k
        self.weights = weights

        if self.weights is None:
            try:
                from FPTUniQA.utils.config import load_config
                cfg = load_config()
                rrf_cfg = cfg.get("retrieval", {}).get("rrf", {})
                self.weights = rrf_cfg.get("weights", [0.4, 0.6])
                if rrf_k == 60:
                    self.rrf_k = rrf_cfg.get("k", 60)
            except Exception:
                self.weights = [0.4, 0.6]

        # Khởi tạo hoặc auto-load BM25
        if bm25_retriever is not None:
            self.bm25_retriever = bm25_retriever
        else:
            self.bm25_retriever = BM25Retriever()
            bm25_dir = Path("data/processed/bm25_index")
            if not (bm25_dir / "bm25_index.pkl").exists():
                bm25_dir = Path(__file__).resolve().parent.parent.parent.parent / "data/processed/bm25_index"
            if auto_load and (bm25_dir / "bm25_index.pkl").exists():
                try:
                    self.bm25_retriever.load(bm25_dir)
                    logger.info(f"Nạp thành công chỉ mục BM25 ({len(self.bm25_retriever.documents)} documents) từ {bm25_dir}")
                except Exception as e:
                    logger.warning(f"Không thể nạp chỉ mục BM25 từ {bm25_dir}: {e}")

        # Khởi tạo hoặc auto-load FAISS Dense
        if dense_retriever is not None:
            self.dense_retriever = dense_retriever
        else:
            self.dense_retriever = DenseRetriever()
            faiss_dir = Path("data/processed/faiss_index")
            if not (faiss_dir / "dense.index").exists():
                faiss_dir = Path(__file__).resolve().parent.parent.parent.parent / "data/processed/faiss_index"
            if auto_load and (faiss_dir / "dense.index").exists():
                try:
                    self.dense_retriever.load(faiss_dir)
                    logger.info(f"Nạp thành công chỉ mục FAISS ({len(self.dense_retriever.documents)} documents) từ {faiss_dir}")
                except Exception as e:
                    logger.warning(f"Không thể nạp chỉ mục FAISS từ {faiss_dir}: {e}")

    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """Lập chỉ mục đồng thời cho cả BM25 và FAISS."""
        logger.info(f"Lập chỉ mục đồng thời {len(documents)} tài liệu cho BM25 và FAISS...")
        self.bm25_retriever.index(documents)
        self.dense_retriever.build_index(documents)
        logger.info("Hoàn tất lập chỉ mục cho cả hai nhánh BM25 và FAISS.")

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int = 20,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Truy xuất song song từ BM25 và Dense, sau đó hợp nhất bằng weighted RRF."""
        if not query or not str(query).strip():
            return []

        # Tăng candidate_k nếu có metadata_filter để đảm bảo sau filter vẫn đủ top_k
        cand_k = max(candidate_k, top_k * 3) if metadata_filter else candidate_k

        bm25_results = self.bm25_retriever.retrieve(
            query, top_k=cand_k, metadata_filter=metadata_filter
        )

        if self.dense_retriever._faiss_index is None:
            fused_results = bm25_results
        else:
            dense_results = self.dense_retriever.retrieve(
                query, top_k=cand_k, metadata_filter=metadata_filter
            )
            fused_results = reciprocal_rank_fusion(
                ranked_runs=[bm25_results, dense_results],
                k=self.rrf_k,
                top_n=cand_k * 2,
                weights=self.weights,
            )

        if metadata_filter:
            from FPTUniQA.retrieval.filter import matches_metadata_filter
            fused_results = [
                (doc, score) for doc, score in fused_results
                if matches_metadata_filter(doc, metadata_filter)
            ]

        return fused_results[:top_k]

    def retrieve_contract2(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int = 20,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Truy xuất tài liệu theo chuẩn Contract 2 với các trường định danh đầy đủ."""
        if not query or not str(query).strip():
            return []

        results = self.retrieve(query, top_k, candidate_k, metadata_filter)
        output = []
        max_rrf = sum(self.weights) / (self.rrf_k + 1.0) if self.weights and self.rrf_k > 0 else 1.0

        for doc, score in results:
            raw_meta = doc.get("metadata", {})
            meta = dict(raw_meta) if isinstance(raw_meta, dict) else {}
            if "effective_date" not in meta:
                meta["effective_date"] = raw_meta.get("effective_date", doc.get("effective_date", ""))
            if "applies_to_cohort" not in meta:
                meta["applies_to_cohort"] = raw_meta.get("cohort", doc.get("applies_to_cohort", ""))
            if "doc_type" not in meta:
                meta["doc_type"] = raw_meta.get("category", doc.get("doc_type", "quy_che"))

            norm_score = round(min(1.0, max(0.0, float(score / max_rrf))), 4)
            strategy = "hybrid" if self.dense_retriever._faiss_index is not None else "bm25"

            output.append({
                "doc_id": doc.get("id") or doc.get("doc_id") or meta.get("doc_id", ""),
                "title": doc.get("title") or meta.get("title", "Tài liệu học vụ"),
                "text": doc.get("text", ""),
                "content": doc.get("text", ""),
                "score": norm_score,
                "source": doc.get("source") or meta.get("url") or doc.get("title", ""),
                "category": doc.get("doc_type") or meta.get("doc_type", meta.get("category", "quy_che")),
                "retrieval_strategy": strategy,
                "metadata": meta,
            })
        return output
