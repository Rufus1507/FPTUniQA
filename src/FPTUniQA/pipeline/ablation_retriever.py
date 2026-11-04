"""Adapter Retrieval cho Khung Ablation Study Matrix (BM25, Dense, C3, C3p, C4-hard, C4-soft, Reranker)."""

from typing import Any, Dict, List, Optional, Tuple
import re
from FPTUniQA.query.campus_matcher import CAMPUS_DISPLAY_NAMES, match_campus_code
from FPTUniQA.retrieval.filter import matches_metadata_filter
from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.pipeline.ablation_retriever")


class AblationRetriever:
    """Retriever linh hoạt cho phép kích hoạt / ngắt từng thành phần:
    - bm25: Chỉ dùng BM25 lexical search
    - dense: Chỉ dùng FAISS dense vector search
    - c3_hybrid / c3_hybrid_sequential: Hybrid (BM25 + FAISS) tuần tự, không metadata
    - c3p_hybrid_parallel: Hybrid (BM25 + FAISS) song song hóa, không metadata
    - c4_hybrid_rrf_filter / c4_hard: Hybrid RRF song song + Lọc cứng Metadata (Hard Pre-filtering)
    - c4_hybrid_rrf_soft / c4_soft: Hybrid RRF song song + Xếp hạng mềm Metadata (Soft Boost Ranking)
    """

    def __init__(
        self,
        hybrid_retriever: Optional[HybridRetriever] = None,
        default_mode: str = "hybrid",
        auto_load: bool = True,
    ):
        self._hybrid = hybrid_retriever or HybridRetriever(auto_load=auto_load)
        if auto_load:
            self._hybrid.ensure_loaded()
        self.default_mode = default_mode

    @property
    def bm25_retriever(self):
        return self._hybrid.bm25_retriever

    @property
    def dense_retriever(self):
        return self._hybrid.dense_retriever

    @property
    def reranker(self):
        return self._hybrid.reranker

    def _extract_heuristic_filter(self, query: str) -> Optional[Dict[str, Any]]:
        """Trích xuất metadata filter cơ bản từ query (cohort, campus) khi caller không cung cấp."""
        filt: Dict[str, Any] = {}
        # Cohort regex
        m_cohort = re.search(r"\b(k1[5-9]|k2[0-5])\b", query, re.IGNORECASE)
        if m_cohort:
            filt["cohort"] = m_cohort.group(1).upper()

        # Campus check qua SSOT campus_matcher
        code = match_campus_code(query)
        if code and code in CAMPUS_DISPLAY_NAMES:
            filt["campus"] = CAMPUS_DISPLAY_NAMES[code]

        return filt if filt else None

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        mode: Optional[str] = None,
        candidate_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        rerank: bool = False,
        score_threshold: Optional[float] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Truy xuất thô dạng [(doc, score)]."""
        self._hybrid.ensure_loaded()
        active_mode = (mode or self.default_mode).lower()

        if active_mode == "bm25":
            return self._hybrid.bm25_retriever.retrieve(
                query, top_k=top_k, metadata_filter=metadata_filter
            )

        elif active_mode == "dense":
            if self._hybrid.dense_retriever._faiss_index is None:
                return self._hybrid.bm25_retriever.retrieve(query, top_k=top_k)
            return self._hybrid.dense_retriever.retrieve(
                query, top_k=top_k, metadata_filter=metadata_filter
            )

        elif active_mode in ("hybrid", "c3_hybrid", "c3_hybrid_sequential"):
            # C3: Hybrid tuần tự, không lọc metadata, không rerank
            return self._hybrid.retrieve(
                query=query,
                top_k=top_k,
                candidate_k=candidate_k,
                metadata_filter=None,
                metadata_mode="none",
                parallel=False,
                rerank=rerank,
                score_threshold=score_threshold,
            )

        elif active_mode in ("c3p_hybrid", "c3p_hybrid_parallel"):
            # C3p: Hybrid song song hóa, không lọc metadata, không rerank
            return self._hybrid.retrieve(
                query=query,
                top_k=top_k,
                candidate_k=candidate_k,
                metadata_filter=None,
                metadata_mode="none",
                parallel=True,
                rerank=rerank,
                score_threshold=score_threshold,
            )

        elif active_mode in ("hybrid_filter", "hybrid_rrf_filter", "c4_hybrid_rrf_filter", "c4_hard"):
            # C4-hard: Hybrid RRF song song + Lọc cứng metadata
            effective_filter = metadata_filter or self._extract_heuristic_filter(query)
            return self._hybrid.retrieve(
                query=query,
                top_k=top_k,
                candidate_k=candidate_k,
                metadata_filter=effective_filter,
                metadata_mode="hard",
                parallel=True,
                rerank=rerank,
                score_threshold=score_threshold,
            )

        elif active_mode in ("hybrid_soft", "hybrid_rrf_soft", "c4_hybrid_rrf_soft", "c4_soft"):
            # C4-soft: Hybrid RRF song song + Xếp hạng mềm metadata (Soft Boost)
            effective_filter = metadata_filter or self._extract_heuristic_filter(query)
            return self._hybrid.retrieve(
                query=query,
                top_k=top_k,
                candidate_k=candidate_k,
                metadata_filter=effective_filter,
                metadata_mode="soft",
                alpha=0.25,
                beta=0.25,
                parallel=True,
                rerank=rerank,
                score_threshold=score_threshold,
            )

        else:
            # Mặc định gọi qua HybridRetriever đầy đủ
            return self._hybrid.retrieve(
                query=query,
                top_k=top_k,
                candidate_k=candidate_k,
                metadata_filter=metadata_filter,
                rerank=rerank,
                score_threshold=score_threshold,
            )

    def retrieve_contract2(
        self,
        query: str,
        top_k: int = 10,
        mode: Optional[str] = None,
        candidate_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        rerank: bool = False,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Truy xuất và chuẩn hóa theo Contract 2."""
        if not query or not str(query).strip():
            return []

        active_mode = (mode or self.default_mode).lower()
        results = self.retrieve(
            query=query,
            top_k=top_k,
            mode=active_mode,
            candidate_k=candidate_k,
            metadata_filter=metadata_filter,
            rerank=rerank,
            score_threshold=score_threshold,
        )

        max_rrf = (
            sum(self._hybrid.weights) / (self._hybrid.rrf_k + 1.0)
            if self._hybrid.weights and self._hybrid.rrf_k > 0
            else 1.0
        )

        if active_mode in ("bm25",):
            strategy = "bm25"
        elif active_mode in ("dense",):
            strategy = "dense"
        else:
            strategy = "hybrid"

        output = []
        for doc, score in results:
            raw_meta = doc.get("metadata", {})
            meta = dict(raw_meta) if isinstance(raw_meta, dict) else {}
            if "effective_date" not in meta:
                meta["effective_date"] = raw_meta.get("effective_date", doc.get("effective_date", "2024-01-01"))
            if "applies_to_cohort" not in meta:
                meta["applies_to_cohort"] = raw_meta.get("cohort", doc.get("applies_to_cohort", "ALL"))
            if "doc_type" not in meta:
                meta["doc_type"] = raw_meta.get("category", doc.get("doc_type", "quy_che"))

            norm_score = round(min(1.0, max(0.0, float(score / max_rrf))), 4) if max_rrf > 0 else 0.5
            text_val = doc.get("text") or doc.get("content") or ""
            doc_id_val = str(doc.get("id") or doc.get("doc_id") or meta.get("doc_id") or "doc_unknown")

            output.append({
                "doc_id": doc_id_val,
                "title": doc.get("title") or meta.get("title", "Tài liệu học vụ"),
                "text": text_val,
                "content": text_val,
                "score": norm_score,
                "source": doc.get("source") or meta.get("url") or doc.get("title", ""),
                "category": doc.get("doc_type") or meta.get("doc_type", meta.get("category", "quy_che")),
                "retrieval_strategy": strategy,
                "metadata": meta,
            })
        return output
