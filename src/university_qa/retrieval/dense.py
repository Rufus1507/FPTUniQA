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
        self.faiss_index: Optional[faiss.Index] = None
        self.documents: List[Dict[str, Any]] = []

    def _init_index(self):
        if self.metric == "inner_product":
            self.faiss_index = faiss.IndexFlatIP(self.dimension)
        else:
            self.faiss_index = faiss.IndexFlatL2(self.dimension)

    def index(self, documents: List[Dict[str, Any]]) -> None:
        """Sinh vector và thêm vào chỉ mục FAISS."""
        self.documents = documents
        texts = [f"{d.get('title', '')}: {d.get('text', '')}" for d in documents]
        embeddings = self.embedding_model.embed_documents(texts)

        self.dimension = embeddings.shape[1]
        self._init_index()
        self.faiss_index.add(embeddings)

    @staticmethod
    def _matches_filter(
        doc: Dict[str, Any],
        filter_cohort: Optional[str] = None,
        filter_campus: Optional[str] = None,
    ) -> bool:
        """Kiểm tra tài liệu có khớp với bộ lọc khóa và cơ sở hay không."""
        if filter_cohort:
            target_cohort = filter_cohort.upper().strip()
            doc_cohorts = doc.get("applies_to_cohort")
            if not doc_cohorts:
                c = doc.get("metadata", {}).get("cohort")
                doc_cohorts = [c] if c else ["ALL"]
            cohorts_upper = [str(c).upper().strip() for c in doc_cohorts]
            if "ALL" not in cohorts_upper and target_cohort not in cohorts_upper:
                return False

        if filter_campus:
            target_campus = filter_campus.upper().strip()
            doc_campus = str(doc.get("campus") or doc.get("metadata", {}).get("campus", "ALL")).upper().strip()
            campus_match = (
                doc_campus == "ALL"
                or doc_campus == target_campus
                or (doc_campus in ["HN", "FUHL"] and target_campus in ["HN", "FUHL"])
            )
            if not campus_match:
                return False

        return True

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filter_cohort: Optional[str] = None,
        filter_campus: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Truy vấn top-k văn bản tương đồng vector có hỗ trợ lọc siêu dữ liệu cứng."""
        if self.faiss_index is None or not self.documents:
            return []

        query_emb = self.embedding_model.embed_query(query).reshape(1, -1)

        # Nếu có lọc metadata, quét rộng hơn để không bị sót tài liệu sau khi lọc
        has_filter = filter_cohort is not None or filter_campus is not None
        search_k = len(self.documents) if has_filter else min(top_k, len(self.documents))

        distances, indices = self.faiss_index.search(query_emb, search_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.documents):
                doc = self.documents[idx]
                if has_filter and not self._matches_filter(doc, filter_cohort, filter_campus):
                    continue
                results.append((doc, float(dist)))
                if len(results) >= top_k:
                    break

        return results

    def save(self, dir_path: Union[str, Path]) -> None:
        """Lưu file index FAISS và metadata documents."""
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        if self.faiss_index is not None:
            faiss.write_index(self.faiss_index, str(path / "dense.index"))
        with open(path / "documents.json", "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

    def load(self, dir_path: Union[str, Path]) -> None:
        """Nạp lại FAISS index và danh sách documents."""
        path = Path(dir_path)
        index_file = path / "dense.index"
        doc_file = path / "documents.json"
        if not index_file.exists() or not doc_file.exists():
            raise FileNotFoundError(f"Không tìm thấy index FAISS tại {path}")

        self.faiss_index = faiss.read_index(str(index_file))
        with open(doc_file, "r", encoding="utf-8") as f:
            self.documents = json.load(f)
