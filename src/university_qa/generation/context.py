"""Ghép nối ngữ cảnh tài liệu và bảng có cấu trúc vào prompt. Phụ trách: TV3."""

from typing import Any, Dict, List, Optional


class ContextBuilder:
    """Xây dựng chuỗi văn bản context từ tài liệu text và dữ liệu bảng."""

    def __init__(self, max_context_length: int = 3000):
        self.max_context_length = max_context_length

    def build_context(
        self,
        documents: List[Dict[str, Any]],
        structured_info: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Ghép nối các đoạn tài liệu thành chuỗi hoàn chỉnh cho Prompt."""
        context_parts = []

        # Thêm thông tin bảng dữ liệu có cấu trúc nếu có
        if structured_info:
            context_parts.append("[DỮ LIỆU BẢNG TRA CỨU BIỂU PHÍ & ĐÀO TẠO]")
            for item in structured_info:
                if "faculty" in item and "credit_price_vnd" in item:
                    line = (
                        f"- Ngành: {item.get('major_name')} (Khoa {item.get('faculty')}): "
                        f"Giá tín chỉ: {item.get('credit_price_vnd'):,} VNĐ/tín chỉ, "
                        f"Học phí dự kiến/kỳ: {item.get('estimated_term_tuition_vnd'):,} VNĐ"
                    )
                    context_parts.append(line)
            context_parts.append("")

        # Thêm các đoạn trích dẫn văn bản
        for idx, doc in enumerate(documents, start=1):
            doc_id = doc.get("id", f"doc_{idx}")
            title = doc.get("title", "Tài liệu quy chế")
            text = doc.get("text", "")
            meta = doc.get("metadata", {})
            section = meta.get("section", "")
            cohort = meta.get("cohort", "Tất cả")

            part = f"[{doc_id}] {title} (Phạm vi: {cohort}, Mục: {section}):\n{text}\n"
            context_parts.append(part)

        full_context = "\n".join(context_parts)
        if len(full_context) > self.max_context_length:
            full_context = full_context[: self.max_context_length] + "\n[... đã cắt bớt ngữ cảnh ...]"

        return full_context
