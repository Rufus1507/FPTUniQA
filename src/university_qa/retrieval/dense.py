"""Tìm kiếm vector tương đồng trên FAISS. Phụ trách: TV2."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import faiss
import numpy as np
from university_qa.retrieval.embedding import EmbeddingModel


class DenseRetriever:
    """Bộ truy xuất ngữ nghĩa dense vector dựa trên FAISS."""

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        dimension: int = 768,
        metric: str = "inner_product",
    ):
        self.embedding_model = embedding_model or EmbeddingModel()
        self.dimension = dimension
        self.metric = metric
        self.index: Optional[faiss.Index] = None
        self.documents: List[Dict[str, Any]] = []

    def _init_index(self):
        if self.metric == "inner_product":
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)

    def index(self, documents: List[Dict[str, Any]]) -> None:
        """Sinh vector và thêm vào chỉ mục FAISS."""
        self.documents = documents
        texts = [f"{d.get('title', '')}: {d.get('text', '')}" for d in documents]
        embeddings = self.embedding_model.embed_documents(texts)

        self.dimension = embeddings.shape[1]
        self._init_index()
        self.index.add(embeddings)

    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """Truy vấn top-k văn bản tương đồng vector."""
        if self.index is None or not self.documents:
            return []

        query_emb = self.embedding_model.embed_query(query).reshape(1, -1)
        distances, indices = self.index.search(query_emb, min(top_k, len(self.documents)))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.documents):
                results.append((self.documents[idx], float(dist)))
        return results

    def save(self, dir_path: Union[str, Path]) -> None:
        """Lưu file index FAISS và metadata documents."""
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, str(path / "dense.index"))
        with open(path / "documents.json", "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

    def load(self, dir_path: Union[str, Path]) -> None:
        """Nạp lại FAISS index và danh sách documents."""
        path = Path(dir_path)
        index_file = path / "dense.index"
        doc_file = path / "documents.json"
        if not index_file.exists() or not doc_file.exists():
            raise FileNotFoundError(f"Không tìm thấy index FAISS tại {path}")

        self.index = faiss.read_index(str(index_file))
        with open(doc_file, "r", encoding="utf-8") as f:
            self.documents = json.load(f)
