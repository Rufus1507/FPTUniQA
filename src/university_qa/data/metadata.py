"""Bổ sung thông tin siêu dữ liệu (cohort, ngày ban hành, danh mục). Phụ trách: TV1."""

from typing import Any, Dict, Optional


class MetadataEnricher:
    """Gán và chuẩn hóa siêu dữ liệu cho các văn bản chunk."""

    def __init__(self, default_metadata: Optional[Dict[str, Any]] = None):
        self.default_metadata = default_metadata or {
            "cohort": "All",
            "effective_date": "2023-09-01",
            "category": "dao_tao",
        }

    def enrich_chunk(
        self,
        chunk_id: str,
        title: str,
        text: str,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Tạo đối tượng corpus chunk hoàn chỉnh với đầy đủ metadata."""
        meta = self.default_metadata.copy()
        if custom_metadata:
            meta.update(custom_metadata)

        return {
            "id": chunk_id,
            "title": title,
            "text": text,
            "metadata": meta,
        }
