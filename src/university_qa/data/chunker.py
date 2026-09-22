"""Phân đoạn văn bản quy chế theo ngữ nghĩa (Điều, Khoản) hoặc theo token/ký tự có overlap. Phụ trách: TV1."""

import re
from typing import Dict, List


class TextChunker:
    """Bộ chia nhỏ văn bản cho hệ thống RAG với hỗ trợ bảng biểu và heading."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_by_characters(self, text: str) -> List[str]:
        """Cắt đoạn văn bản theo số ký tự với bước trượt overlap."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        step = self.chunk_size - self.chunk_overlap

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start += step

        return chunks

    def chunk_by_legal_sections(self, text: str) -> List[Dict[str, str]]:
        """Phân đoạn thông minh theo cấu trúc Điều/Khoản của văn bản quy chế đại học."""
        pattern = r"(Điều\s+\d+[\.\:]\s*[^\n]+)"
        parts = re.split(pattern, text)

        chunks = []
        if len(parts) <= 1:
            # Không tìm thấy cấu trúc Điều khoản, fallback về chunking thông thường
            for c in self.chunk_by_characters(text):
                chunks.append({"title": "Quy chế chung", "text": c})
            return chunks

        # parts[0] thường là phần mở đầu/căn cứ
        if parts[0].strip():
            chunks.append({"title": "Phần mở đầu", "text": parts[0].strip()})

        for i in range(1, len(parts), 2):
            title = parts[i].strip()
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            full_text = f"{title}\n{content}".strip()

            # Nếu nội dung 1 điều quá dài, tiếp tục chia nhỏ
            if len(full_text) > self.chunk_size:
                sub_chunks = self.chunk_by_characters(full_text)
                for idx, sc in enumerate(sub_chunks):
                    chunks.append({"title": f"{title} (Phần {idx + 1})", "text": sc})
            else:
                chunks.append({"title": title, "text": full_text})

        return chunks

    def chunk_by_headings(self, text: str, base_title: str = "") -> List[Dict[str, str]]:
        """
        Phân đoạn theo các thẻ Heading trong văn bản Markdown/plain text
        (ký hiệu # hoặc ## hoặc ###, hoặc các dòng all-caps ngắn).

        Được sử dụng cho văn bản HTML đã bóc tách (bài tuyển sinh, mô tả ngành).
        """
        # Pattern tìm Markdown heading hoặc ALL-CAPS section header
        heading_pattern = re.compile(
            r"^(#{1,4}\s+.+|[A-ZĐÀÁẢÃẠĂẮẶẰẲẴÂẤẬẦẨẪÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỘỒỔỖƠỚỢỜỞỠÙÚỦŨỤƯỨỰỪỬỮ].{0,60})$",
            re.MULTILINE,
        )

        parts = heading_pattern.split(text)
        if len(parts) <= 1:
            # Không tìm thấy heading → fallback chunking
            for c in self.chunk_by_characters(text):
                yield_title = base_title or "Nội dung"
                return [{"title": yield_title, "text": c}]

        chunks = []
        # parts[0] = nội dung trước heading đầu tiên
        if parts[0].strip():
            chunks.append({"title": base_title or "Giới thiệu", "text": parts[0].strip()})

        i = 1
        while i < len(parts):
            section_title = parts[i].strip().lstrip("#").strip()
            section_body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            full_section = f"{section_title}\n{section_body}".strip()
            display_title = f"{base_title} — {section_title}" if base_title else section_title

            if len(full_section) > self.chunk_size:
                sub_chunks = self.chunk_by_characters(full_section)
                for idx, sc in enumerate(sub_chunks):
                    chunks.append({"title": f"{display_title} (Phần {idx + 1})", "text": sc})
            else:
                if full_section:
                    chunks.append({"title": display_title, "text": full_section})
            i += 2

        return chunks if chunks else [{"title": base_title or "Nội dung", "text": text}]

    def chunk_document(
        self,
        text: str,
        tables_md: List[str] = None,
        title: str = "",
        has_legal_structure: bool = False,
    ) -> List[Dict[str, str]]:
        """
        Phân đoạn thông minh dựa trên loại nội dung:
        - Văn bản quy chế có cấu trúc Điều/Khoản → chunk_by_legal_sections
        - Bảng biểu (học phí) → giữ nguyên thành 1 chunk, không cắt ngang
        - Bài viết thông thường → chunk_by_headings → fallback chunk_by_characters

        Args:
            text: Nội dung văn bản chính.
            tables_md: Danh sách bảng Markdown (từ html_extractor).
            title: Tiêu đề tài liệu (làm ngữ cảnh cho chunk title).
            has_legal_structure: True nếu biết trước là văn bản quy chế.
        """
        chunks = []

        # 1. Phân đoạn bảng biểu riêng (mỗi bảng là 1 chunk độc lập)
        if tables_md:
            for idx, table in enumerate(tables_md):
                if not table.strip():
                    continue
                table_title = f"{title} — Bảng {idx + 1}" if title else f"Bảng biểu {idx + 1}"
                # Nếu bảng quá dài, cắt theo ký tự
                if len(table) > self.chunk_size * 2:
                    for cidx, c in enumerate(self.chunk_by_characters(table)):
                        chunks.append({
                            "title": f"{table_title} (Phần {cidx + 1})",
                            "text": c
                        })
                else:
                    chunks.append({"title": table_title, "text": table.strip()})

        # 2. Phân đoạn phần text chính
        if not text or not text.strip():
            return chunks

        if has_legal_structure or bool(re.search(r"Điều\s+\d+[\.\:]", text)):
            text_chunks = self.chunk_by_legal_sections(text)
        else:
            text_chunks = self.chunk_by_headings(text, base_title=title)

        # Bổ sung context title vào từng chunk text
        for chunk in text_chunks:
            if chunk.get("text"):
                chunks.append(chunk)

        return chunks if chunks else [{"title": title or "Nội dung", "text": text}]
