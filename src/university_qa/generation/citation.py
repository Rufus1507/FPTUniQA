"""Trích xuất nguồn tham chiếu (Citations) và đoạn căn cứ chứng minh. Phụ trách: TV3."""

import re
from typing import Any, Dict, List


class CitationExtractor:
    """Trích xuất danh sách trích dẫn nguồn từ tài liệu và câu trả lời."""

    @staticmethod
    def extract_from_answer_and_docs(
        answer: str,
        retrieved_docs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Tìm các mã tài liệu [doc_xxx] xuất hiện trong câu trả lời hoặc trích xuất từ top docs."""
        citations = []
        found_ids = set(re.findall(r"\[(doc_\d+|QC-[\w\-]+|HB-[\w\-]+)\]", answer))

        # Nếu mô hình nhắc đến các mã cụ thể trong câu trả lời
        doc_map = {doc.get("id"): doc for doc in retrieved_docs}
        for doc_id in found_ids:
            if doc_id in doc_map:
                doc = doc_map[doc_id]
                citations.append({
                    "doc_id": doc_id,
                    "title": doc.get("title", ""),
                    "section": doc.get("metadata", {}).get("section", ""),
                    "snippet": doc.get("text", "")[:150] + "...",
                })

        # Nếu trong câu trả lời không ghi rõ thẻ ID, mặc định lấy top 2 tài liệu xếp hạng cao nhất
        if not citations and retrieved_docs:
            for doc in retrieved_docs[:2]:
                citations.append({
                    "doc_id": doc.get("id", ""),
                    "title": doc.get("title", ""),
                    "section": doc.get("metadata", {}).get("section", ""),
                    "snippet": doc.get("text", "")[:150] + "...",
                })

        return citations
