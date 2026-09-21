"""Định dạng và ghép nối các đoạn tài liệu thành ngữ cảnh có cấu trúc cho Prompt."""

from typing import List, Dict


def format_context(chunks: List[Dict]) -> str:
    """Chuyển đổi danh sách các chunk từ retriever thành văn bản có cấu trúc.

    Mỗi chunk được đánh số thứ tự dạng [Nguồn N] kèm tiêu đề và phân loại.
    """
    if not chunks:
        return "Không có tài liệu nào được trích xuất."

    formatted_sections = []
    for idx, chunk in enumerate(chunks, start=1):
        title = chunk.get("title", "Tài liệu học vụ")
        category = chunk.get("category", "quy_che")
        content = chunk.get("content", "").strip()
        source = chunk.get("source", "")

        header = f"[Nguồn {idx}] - Tiêu đề: {title} | Danh mục: {category}"
        if source:
            header += f" | Căn cứ: {source}"

        section = f"{header}\nNội dung: {content}\n"
        formatted_sections.append(section)

    return "\n".join(formatted_sections)
