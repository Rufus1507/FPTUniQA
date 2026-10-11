"""Tìm kiếm vector tương đồng trên FAISS. Phụ trách: TV2."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import faiss
import numpy as np
from FPTUniQA.retrieval.embedding import EmbeddingModel


from FPTUniQA.retrieval.filter import matches_metadata_filter


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
        self._faiss_index: Optional[faiss.Index] = None
        self.documents: List[Dict[str, Any]] = []

    def _init_index(self):
        if self.metric == "inner_product":
            self._faiss_index = faiss.IndexFlatIP(self.dimension)
        else:
            self._faiss_index = faiss.IndexFlatL2(self.dimension)

    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """Sinh vector và thêm vào chỉ mục FAISS."""
        self.documents = documents
        texts = [f"{d.get('title', '')}: {d.get('text', '')}" for d in documents]
        embeddings = self.embedding_model.embed_documents(texts)
        
        if self.metric == "inner_product":
            faiss.normalize_L2(embeddings)

        self.dimension = embeddings.shape[1]
        self._init_index()
        self._faiss_index.add(embeddings)

    def retrieve(self, query: str, top_k: int = 10, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Truy vấn top-k văn bản tương đồng vector."""
        if not query or not str(query).strip():
            return []
        if self._faiss_index is None or not self.documents:
            return []

        query_emb = self.embedding_model.embed_query(query).reshape(1, -1)
        if self.metric == "inner_product":
            faiss.normalize_L2(query_emb)
            
        search_k = min(max(top_k * 20, 200) if metadata_filter else top_k, len(self.documents))
        distances, indices = self._faiss_index.search(query_emb, search_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.documents):
                doc = self.documents[idx]
                if metadata_filter and not matches_metadata_filter(doc, metadata_filter):
                    continue
                results.append((doc, float(dist)))
                if len(results) >= top_k:
                    break
        
        results = sorted(results, key=lambda x: x[1], reverse=True)[:top_k]
        return results

    def retrieve_contract2(self, query: str, top_k: int = 10, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Truy xuất tài liệu theo format Contract 2."""
        if not query or not str(query).strip():
            return []
        results = self.retrieve(query, top_k, metadata_filter)
        output = []
        for doc, score in results:
            raw_meta = doc.get("metadata", {})
            meta = dict(raw_meta) if isinstance(raw_meta, dict) else {}
            if "effective_date" not in meta:
                meta["effective_date"] = raw_meta.get("effective_date", doc.get("effective_date", ""))
            if "applies_to_cohort" not in meta:
                meta["applies_to_cohort"] = raw_meta.get("cohort", doc.get("applies_to_cohort", ""))
            if "doc_type" not in meta:
                meta["doc_type"] = raw_meta.get("category", doc.get("doc_type", "quy_che"))

            # Chuẩn hóa cosine similarity về khoảng [0.0, 1.0]
            norm_score = round(min(1.0, max(0.0, float(score))), 4)

            output.append({
                "doc_id": doc.get("id") or doc.get("doc_id") or meta.get("doc_id", ""),
                "title": doc.get("title") or meta.get("title", "Tài liệu học vụ"),
                "text": doc.get("text", ""),
                "content": doc.get("text", ""),
                "score": norm_score,
                "source": doc.get("source") or meta.get("url") or doc.get("title", ""),
                "category": doc.get("doc_type") or meta.get("doc_type", meta.get("category", "quy_che")),
                "retrieval_strategy": "dense",
                "metadata": meta,
            })
        return output

    def save(self, dir_path: Union[str, Path]) -> None:
        """Lưu file index FAISS và metadata documents."""
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        if self._faiss_index is not None:
            faiss.write_index(self._faiss_index, str(path / "dense.index"))
        with open(path / "documents.json", "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        with open(path / "meta.json", "w", encoding="utf-8") as f:
            json.dump({
                "dimension": self.dimension,
                "metric": self.metric,
                "model_name": self.embedding_model.model_name
            }, f, ensure_ascii=False, indent=2)

    def load(self, dir_path: Union[str, Path]) -> None:
        """Nạp lại FAISS index và danh sách documents."""
        path = Path(dir_path)
        index_file = path / "dense.index"
        doc_file = path / "documents.json"
        meta_file = path / "meta.json"
        if not index_file.exists() or not doc_file.exists():
            raise FileNotFoundError(f"Không tìm thấy index FAISS tại {path}")

        self._faiss_index = faiss.read_index(str(index_file))
        with open(doc_file, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    self.dimension = meta.get("dimension", self.dimension)
                    self.metric = meta.get("metric", self.metric)
            except Exception:
                pass

    load_index = load
    save_index = save
