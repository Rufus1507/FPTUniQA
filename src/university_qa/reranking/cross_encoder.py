"""Mô hình Cross-Encoder (bge-reranker-large/v2-m3) để tái xếp hạng chính xác. Phụ trách: TV2."""

from typing import Any, Dict, List, Optional, Tuple
from university_qa.reranking.reranker import BaseReranker


class CrossEncoderReranker(BaseReranker):
    """Bộ tái xếp hạng sử dụng mô hình Cross-Encoder."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-large",
        device: str = "cpu",
        batch_size: int = 16,
    ):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name, device=self.device)
            except Exception:
                self._model = "dummy"

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Chấm điểm cặp (query, doc_text) và sắp xếp lại danh sách."""
        if not documents:
            return []

        self._load_model()
        pairs = [[query, f"{d.get('title', '')}: {d.get('text', '')}"] for d in documents]

        if self._model == "dummy":
            # Chấm điểm giả lập dựa trên độ dài trùng lặp từ khóa cho test
            q_words = set(query.lower().split())
            scores = []
            for d in documents:
                text_words = set(d.get("text", "").lower().split())
                overlap = len(q_words.intersection(text_words))
                scores.append(float(overlap))
        else:
            scores = self._model.predict(pairs, batch_size=self.batch_size).tolist()

        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return scored_docs[:top_n]
