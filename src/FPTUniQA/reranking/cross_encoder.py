"""Mô hình Cross-Encoder (bge-reranker-large/v2-m3) để tái xếp hạng chính xác. Phụ trách: TV2."""

import math
from typing import Any, Dict, List, Optional, Tuple
from FPTUniQA.reranking.reranker import BaseReranker
from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.reranking.cross_encoder")


class CrossEncoderReranker(BaseReranker):
    """Bộ tái xếp hạng sử dụng mô hình Cross-Encoder chuẩn hóa Contract 2."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ):
        try:
            from FPTUniQA.utils.config import load_config
            cfg = load_config().get("reranking", {})
        except Exception:
            cfg = {}

        self.model_name = model_name or cfg.get("model_name", "BAAI/bge-reranker-large")
        self.device = device or cfg.get("device", "cpu")
        self.batch_size = batch_size or cfg.get("batch_size", 16)
        self.score_threshold = (
            score_threshold if score_threshold is not None else float(cfg.get("score_threshold", 0.0))
        )
        self._model = None

    def _load_model(self):
        """Khởi tạo nạp mô hình CrossEncoder từ sentence_transformers hoặc kích hoạt fallback."""
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder
            import torch.nn as nn

            logger.info(f"Đang nạp mô hình CrossEncoder '{self.model_name}' trên thiết bị: {self.device}")
            try:
                self._model = CrossEncoder(self.model_name, device=self.device, activation_fn=nn.Sigmoid())
            except TypeError:
                try:
                    self._model = CrossEncoder(
                        self.model_name, device=self.device, default_activation_function=nn.Sigmoid()
                    )
                except Exception:
                    self._model = CrossEncoder(self.model_name, device=self.device)
            logger.info(f"Nạp thành công mô hình CrossEncoder '{self.model_name}'")
        except Exception as e:
            logger.warning(
                f"Không thể nạp mô hình CrossEncoder '{self.model_name}': {e}. Kích hoạt chế độ fallback dummy reranker."
            )
            self._model = "dummy"

    @staticmethod
    def _sigmoid(score: float) -> float:
        """Tính hàm Sigmoid ổn định số học (numerically stable sigmoid)."""
        if score >= 0:
            z = math.exp(-min(score, 700.0))
            return 1.0 / (1.0 + z)
        else:
            z = math.exp(max(score, -700.0))
            return z / (1.0 + z)

    @classmethod
    def _normalize_scores(cls, scores: List[float]) -> List[float]:
        """Chuẩn hóa danh sách điểm số về đoạn [0.0, 1.0] bảo toàn thứ tự đơn điệu (monotonicity).

        Nếu bất kỳ điểm nào nằm ngoài [0.0, 1.0] (chứng tỏ đây là raw logits chưa qua sigmoid),
        toàn bộ danh sách sẽ được ánh xạ qua hàm sigmoid đồng bộ.
        """
        if not scores:
            return []
        is_raw_logits = any(s < 0.0 or s > 1.0 for s in scores)
        if is_raw_logits:
            return [round(min(1.0, max(0.0, cls._sigmoid(s))), 4) for s in scores]
        return [round(min(1.0, max(0.0, float(s))), 4) for s in scores]

    @classmethod
    def _normalize_score(cls, score: float, is_logit: bool = False) -> float:
        """Chuẩn hóa một giá trị điểm đơn lẻ về [0.0, 1.0]."""
        if is_logit or score < 0.0 or score > 1.0:
            return round(min(1.0, max(0.0, cls._sigmoid(score))), 4)
        return round(min(1.0, max(0.0, float(score))), 4)

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Chấm điểm cặp (query, doc_text), chuẩn hóa điểm và sắp xếp lại danh sách ứng viên."""
        if not query or not str(query).strip() or not documents:
            return []

        # Lọc bỏ phần tử không hợp lệ (None, không phải dict, hoặc rỗng hoàn toàn)
        def is_valid_doc(d: Any) -> bool:
            if not isinstance(d, dict):
                return False
            raw = d.get("text") or d.get("content") or d.get("title") or ""
            return bool(str(raw).strip())

        valid_documents = [d for d in documents if is_valid_doc(d)]
        if not valid_documents:
            return []

        self._load_model()

        # Hỗ trợ cả hai trường 'text' và 'content'
        def get_doc_text(d: Dict[str, Any]) -> str:
            text = d.get("text") or d.get("content") or ""
            title = d.get("title") or ""
            if title and text:
                return f"{title}: {text}"
            return text or title

        pairs = [[query, get_doc_text(d)] for d in valid_documents]

        if self._model == "dummy":
            # Chấm điểm giả lập dựa trên độ dài trùng lặp từ khóa cho test / fallback
            q_words = set(query.lower().split())
            scores = []
            for d in valid_documents:
                doc_text = get_doc_text(d)
                text_words = set(doc_text.lower().split())
                overlap = len(q_words.intersection(text_words))
                norm_score = overlap / max(1, len(q_words))
                scores.append(round(min(1.0, max(0.0, float(norm_score))), 4))
        else:
            try:
                preds = self._model.predict(pairs, batch_size=self.batch_size)
                if hasattr(preds, "tolist"):
                    raw_list = preds.tolist()
                else:
                    raw_list = list(preds)
                scores = self._normalize_scores([float(s) for s in raw_list])
            except Exception as e:
                logger.warning(f"Lỗi khi dự đoán bằng CrossEncoder: {e}. Sử dụng fallback scoring.")
                q_words = set(query.lower().split())
                scores = []
                for d in valid_documents:
                    doc_text = get_doc_text(d)
                    text_words = set(doc_text.lower().split())
                    overlap = len(q_words.intersection(text_words))
                    norm_score = overlap / max(1, len(q_words))
                    scores.append(round(min(1.0, max(0.0, float(norm_score))), 4))

        scored_docs = list(zip(valid_documents, scores))

        # Áp dụng ngưỡng điểm loại bỏ nhiễu (score thresholding)
        effective_thresh = score_threshold if score_threshold is not None else self.score_threshold
        if effective_thresh > 0.0:
            scored_docs = [(d, s) for d, s in scored_docs if s >= effective_thresh]

        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:top_n]
