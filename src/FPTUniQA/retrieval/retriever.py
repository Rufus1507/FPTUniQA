"""Lớp bọc hợp nhất Hybrid Retriever (BM25 + FAISS + RRF + Cross-Encoder Reranker). Phụ trách: TV2."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from FPTUniQA.reranking.reranker import BaseReranker
from FPTUniQA.retrieval.bm25 import BM25Retriever
from FPTUniQA.retrieval.cache import RetrievalCache
from FPTUniQA.retrieval.dense import DenseRetriever
from FPTUniQA.retrieval.rrf import reciprocal_rank_fusion
from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.retrieval.retriever")


class HybridRetriever:
    """Bộ tìm kiếm kết hợp cả từ khóa (BM25), ngữ nghĩa sâu (Dense Vector) và Cross-Encoder Reranker."""

    def __init__(
        self,
        bm25_retriever: Optional[BM25Retriever] = None,
        dense_retriever: Optional[DenseRetriever] = None,
        reranker: Optional[BaseReranker] = None,
        rrf_k: int = 60,
        weights: Optional[List[float]] = None,
        auto_load: bool = True,
        cache: Optional[RetrievalCache] = None,
    ):
        self.rrf_k = rrf_k
        self.weights = weights
        self._auto_load = auto_load
        self._is_loaded = False

        try:
            from FPTUniQA.utils.config import load_config
            cfg = load_config()
        except Exception:
            cfg = {}

        if self.weights is None:
            rrf_cfg = cfg.get("retrieval", {}).get("rrf", {})
            self.weights = rrf_cfg.get("weights", [0.4, 0.6])
            if rrf_k == 60:
                self.rrf_k = rrf_cfg.get("k", 60)

        # Lưu retriever hoặc khởi tạo instance rỗng
        self._bm25_retriever = bm25_retriever
        self._dense_retriever = dense_retriever

        # Khởi tạo Reranker (Two-stage retrieval)
        rerank_cfg = cfg.get("reranking", {})
        self.default_candidate_k = int(rerank_cfg.get("candidate_k", 20))
        self._reranker = reranker
        self._rerank_cfg = rerank_cfg

        # Khởi tạo Caching Layer
        cache_cfg = cfg.get("retrieval", {}).get("cache", {})
        if cache is not None:
            self.cache = cache
        elif cache_cfg.get("enabled", True):
            self.cache = RetrievalCache(
                ttl_seconds=int(cache_cfg.get("ttl_seconds", 3600)),
                max_entries=int(cache_cfg.get("max_entries", 1000)),
                redis_url=cache_cfg.get("redis_url", None),
            )
        else:
            self.cache = None

        # Nếu auto_load=True, thực hiện nạp ngay; nếu False sẽ nạp lazy khi gọi ensure_loaded()
        if auto_load:
            self.ensure_loaded()

    @property
    def is_loaded(self) -> bool:
        """Trạng thái đã nạp chỉ mục hay chưa."""
        return self._is_loaded

    @property
    def bm25_retriever(self) -> BM25Retriever:
        if self._bm25_retriever is None:
            self._bm25_retriever = BM25Retriever()
        return self._bm25_retriever

    @bm25_retriever.setter
    def bm25_retriever(self, val: BM25Retriever) -> None:
        self._bm25_retriever = val

    @property
    def dense_retriever(self) -> DenseRetriever:
        if self._dense_retriever is None:
            self._dense_retriever = DenseRetriever()
        return self._dense_retriever

    @dense_retriever.setter
    def dense_retriever(self, val: DenseRetriever) -> None:
        self._dense_retriever = val

    @property
    def reranker(self) -> Optional[BaseReranker]:
        if self._reranker is None and self._rerank_cfg.get("enabled", True):
            try:
                from FPTUniQA.reranking.cross_encoder import CrossEncoderReranker
                self._reranker = CrossEncoderReranker(
                    model_name=self._rerank_cfg.get("model_name", "BAAI/bge-reranker-base"),
                    device=self._rerank_cfg.get("device", "cpu"),
                    batch_size=self._rerank_cfg.get("batch_size", 16),
                    score_threshold=self._rerank_cfg.get("score_threshold", 0.0),
                )
            except Exception as e:
                logger.warning(f"Không thể khởi tạo CrossEncoderReranker: {e}")
                self._reranker = None
        return self._reranker

    @reranker.setter
    def reranker(self, val: Optional[BaseReranker]) -> None:
        self._reranker = val

    def ensure_loaded(self) -> None:
        """Nạp chỉ mục BM25 và FAISS từ đĩa nếu chưa nạp (Lazy Loading)."""
        if self._is_loaded:
            return

        # Nạp BM25 nếu chưa có dữ liệu
        bm25 = self.bm25_retriever
        if not bm25.documents:
            bm25_dir = Path("data/processed/bm25_index")
            if not (bm25_dir / "bm25_index.pkl").exists():
                bm25_dir = Path(__file__).resolve().parent.parent.parent.parent / "data/processed/bm25_index"
            if (bm25_dir / "bm25_index.pkl").exists():
                try:
                    bm25.load(bm25_dir)
                    logger.info(f"Nạp thành công chỉ mục BM25 ({len(bm25.documents)} documents) từ {bm25_dir}")
                except Exception as e:
                    logger.warning(f"Không thể nạp chỉ mục BM25 từ {bm25_dir}: {e}")

        # Nạp FAISS Dense nếu chưa có index
        dense = self.dense_retriever
        if dense._faiss_index is None:
            faiss_dir = Path("data/processed/faiss_index")
            if not (faiss_dir / "dense.index").exists():
                faiss_dir = Path(__file__).resolve().parent.parent.parent.parent / "data/processed/faiss_index"
            if (faiss_dir / "dense.index").exists():
                try:
                    dense.load(faiss_dir)
                    logger.info(f"Nạp thành công chỉ mục FAISS ({len(dense.documents)} documents) từ {faiss_dir}")
                except Exception as e:
                    logger.warning(f"Không thể nạp chỉ mục FAISS từ {faiss_dir}: {e}")

        self._is_loaded = True

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
        candidate_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        rerank: bool = True,
        score_threshold: Optional[float] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Quy trình truy xuất 2 giai đoạn: Candidate Retrieval (BM25+Dense+RRF) -> Reranking (Cross-Encoder)."""
        if not query or not str(query).strip():
            return []

        cache_key = None
        if self.cache is not None:
            cache_key = self.cache.make_cache_key(
                query=query,
                top_k=top_k,
                candidate_k=candidate_k,
                metadata_filter=metadata_filter,
                rerank=rerank,
                score_threshold=score_threshold,
            )
            cached_res = self.cache.get(cache_key)
            if cached_res is not None:
                return [(item[0], float(item[1])) for item in cached_res]

        self.ensure_loaded()

        if candidate_k is None:
            candidate_k = self.default_candidate_k

        # Tăng candidate_k nếu có metadata_filter để đảm bảo sau filter vẫn đủ ứng viên
        cand_k = max(candidate_k, top_k * 3) if metadata_filter else candidate_k

        # Giai đoạn 1: Truy xuất ứng viên từ BM25 và Dense
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

        # Lọc metadata nếu có
        if metadata_filter:
            from FPTUniQA.retrieval.filter import matches_metadata_filter
            fused_results = [
                (doc, score) for doc, score in fused_results
                if matches_metadata_filter(doc, metadata_filter)
            ]

        # Giai đoạn 2: Tái xếp hạng bằng CrossEncoderReranker (nếu rerank=True và reranker khả dụng)
        if rerank and self.reranker is not None:
            candidate_docs = [doc for doc, _ in fused_results[:candidate_k]]
            if candidate_docs:
                reranked = self.reranker.rerank(
                    query=query,
                    documents=candidate_docs,
                    top_n=top_k,
                    score_threshold=score_threshold,
                )
                if self.cache is not None and cache_key:
                    self.cache.set(cache_key, reranked)
                return reranked
            return []

        max_rrf = sum(self.weights) / (self.rrf_k + 1.0) if self.weights and self.rrf_k > 0 else 1.0
        if score_threshold is not None and score_threshold > 0.0:
            fused_results = [
                (doc, score) for doc, score in fused_results
                if (score / max_rrf) >= score_threshold
            ]

        final_res = fused_results[:top_k]
        if self.cache is not None and cache_key:
            self.cache.set(cache_key, final_res)
        return final_res

    def retrieve_contract2(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        rerank: bool = True,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Truy xuất tài liệu theo chuẩn Contract 2 với các trường định danh và điểm số bounded [0.0, 1.0]."""
        if not query or not str(query).strip():
            return []

        results = self.retrieve(
            query=query,
            top_k=top_k,
            candidate_k=candidate_k,
            metadata_filter=metadata_filter,
            rerank=rerank,
            score_threshold=score_threshold,
        )
        output = []
        is_reranked = rerank and self.reranker is not None
        max_rrf = sum(self.weights) / (self.rrf_k + 1.0) if self.weights and self.rrf_k > 0 else 1.0

        has_dense = (
            self.dense_retriever._faiss_index is not None
            and getattr(self.dense_retriever._faiss_index, "ntotal", 0) > 0
        )
        has_bm25 = (
            self.bm25_retriever.bm25 is not None
            and len(getattr(self.bm25_retriever, "documents", [])) > 0
        )
        if has_dense and has_bm25:
            strategy = "hybrid"
        elif has_dense:
            strategy = "dense"
        else:
            strategy = "bm25"

        for doc, score in results:
            raw_meta = doc.get("metadata", {})
            meta = dict(raw_meta) if isinstance(raw_meta, dict) else {}
            if "effective_date" not in meta:
                meta["effective_date"] = raw_meta.get("effective_date", doc.get("effective_date", "2024-01-01"))
            if "applies_to_cohort" not in meta:
                meta["applies_to_cohort"] = raw_meta.get("cohort", doc.get("applies_to_cohort", "ALL"))
            if "doc_type" not in meta:
                meta["doc_type"] = raw_meta.get("category", doc.get("doc_type", "quy_che"))

            if is_reranked:
                # Điểm số từ CrossEncoderReranker đã được chuẩn hóa về [0.0, 1.0]
                norm_score = round(min(1.0, max(0.0, float(score))), 4)
            else:
                norm_score = round(min(1.0, max(0.0, float(score / max_rrf))), 4)

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
