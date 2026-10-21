"""Bổ sung thông tin siêu dữ liệu (cohort, ngày ban hành, danh mục). Phụ trách: TV1."""

from typing import Any, Dict, Optional


class MetadataEnricher:
    """Gán và chuẩn hóa siêu dữ liệu cho các văn bản chunk theo chuẩn Contract 1 Hybrid."""

    def __init__(self, default_metadata: Optional[Dict[str, Any]] = None):
        self.default_metadata = default_metadata or {
            "cohort": "ALL",
            "campus": "ALL",
            "effective_date": "2023-09-01",
            "category": "dao_tao",
            "doc_type": "handbook",
        }

    def enrich_chunk(
        self,
        chunk_id: str,
        title: str,
        text: str,
        custom_metadata: Optional[Dict[str, Any]] = None,
        structured_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Tạo đối tượng corpus chunk hoàn chỉnh với đầy đủ metadata Contract 1."""
        meta = self.default_metadata.copy()
        if custom_metadata:
            meta.update(custom_metadata)

        cohort_val = meta.get("cohort", "ALL")
        if isinstance(cohort_val, list):
            applies_to_cohort = cohort_val
        elif cohort_val and cohort_val != "ALL":
            applies_to_cohort = [cohort_val]
        else:
            applies_to_cohort = ["K17", "K18", "K19", "K20", "K21", "K22"]

        campus_val = meta.get("campus", "ALL")
        effective_date = meta.get("effective_date", "2023-09-01")
        doc_type = meta.get("doc_type", "handbook")
        source = meta.get("source_file", meta.get("source", "Sổ tay sinh viên FPT"))

        # Đối tượng hợp nhất Contract 1 Hybrid
        return {
            "id": chunk_id,
            "doc_id": chunk_id,
            "title": title,
            "text": text,
            "source": source,
            "effective_date": effective_date,
            "applies_to_cohort": applies_to_cohort,
            "campus": campus_val,
            "doc_type": doc_type,
            "structured_payload": structured_payload,
            "metadata": {
                "doc_id": chunk_id,
                "section": title,
                "cohort": cohort_val if isinstance(cohort_val, str) else "-".join(cohort_val),
                "campus": campus_val,
                "effective_date": effective_date,
                "category": meta.get("category", "dao_tao"),
                "source_file": source,
            },
        }
