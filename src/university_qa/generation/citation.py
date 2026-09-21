"""Trích xuất và ánh xạ các marker [Nguồn N] trong câu trả lời thành danh sách Citations có cấu trúc."""

import re
from typing import List, Dict


def extract_citations(answer: str, context_chunks: List[Dict]) -> List[Dict]:
    """Phân tích các thẻ [Nguồn N] trong câu trả lời và ánh xạ về tài liệu tương ứng.

    Trả về danh sách các dict có dạng:
    [
        {
            "doc_id": "FPTU-QC-001",
            "title": "Quy chế cảnh báo học vụ...",
            "source": "Sổ tay sinh viên...",
            "category": "quy_che",
            "source_index": 1
        }
    ]
    """
    if not answer or not context_chunks:
        return []

    # Tìm tất cả các marker dạng [Nguồn 1], [Nguồn 2], [nguồn 3]...
    pattern = r"\[[Nn]guồn\s+(\d+)\]"
    matched_indices = re.findall(pattern, answer)

    # Chuyển đổi thành tập các số nguyên duy nhất theo thứ tự xuất hiện
    seen = set()
    unique_indices = []
    for idx_str in matched_indices:
        idx = int(idx_str)
        if idx not in seen:
            seen.add(idx)
            unique_indices.append(idx)

    citations: List[Dict] = []
    for idx in unique_indices:
        # Danh sách 1-indexed nên vị trí tương ứng trong list là idx - 1
        if 1 <= idx <= len(context_chunks):
            chunk = context_chunks[idx - 1]
            citation_item = {
                "doc_id": chunk.get("doc_id", f"DOC-{idx}"),
                "title": chunk.get("title", "Tài liệu học vụ"),
                "source": chunk.get("source", "Tài liệu quy chế"),
                "category": chunk.get("category", "quy_che"),
                "source_index": idx,
            }
            citations.append(citation_item)

    # Nếu mô hình không trích dẫn rõ marker nhưng có context_chunks, lấy chunk hàng đầu làm căn cứ
    if not citations and context_chunks:
        top_chunk = context_chunks[0]
        citations.append({
            "doc_id": top_chunk.get("doc_id", "DOC-1"),
            "title": top_chunk.get("title", "Tài liệu học vụ"),
            "source": top_chunk.get("source", "Tài liệu quy chế"),
            "category": top_chunk.get("category", "quy_che"),
            "source_index": 1,
        })

    return citations
