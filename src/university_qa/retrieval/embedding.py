"""Khởi tạo và tạo vector embedding (multilingual-e5 / bge-m3). Phụ trách: TV2."""

from typing import List, Optional
import numpy as np


class EmbeddingModel:
    """Lớp sinh vector embedding cho văn bản và câu hỏi."""

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-base",
        device: str = "cpu",
        normalize: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.normalize = normalize
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
            except Exception as e:
                # Fallback dự phòng cho môi trường offline hoặc testing
                self._model = "dummy"

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Tạo embeddings cho danh sách tài liệu/đoạn văn bản."""
        self._load_model()
        if self._model == "dummy":
            # Tạo vector ngẫu nhiên cố định phục vụ kiểm thử nhanh
            np.random.seed(42)
            return np.random.randn(len(texts), 768).astype(np.float32)

        # Với E5, quy ước thêm prefix 'passage: ' cho văn bản
        formatted_texts = (
            [f"passage: {t}" for t in texts]
            if "e5" in self.model_name.lower()
            else texts
        )
        embeddings = self._model.encode(
            formatted_texts,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
        )
        return np.array(embeddings, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Tạo embedding cho một câu truy vấn."""
        self._load_model()
        if self._model == "dummy":
            np.random.seed(len(query))
            return np.random.randn(768).astype(np.float32)

        # Với E5, quy ước thêm prefix 'query: ' cho câu hỏi
        formatted_query = (
            f"query: {query}" if "e5" in self.model_name.lower() else query
        )
        embedding = self._model.encode(
            formatted_query,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
        )
        return np.array(embedding, dtype=np.float32)
