"""Phân đoạn văn bản quy chế theo ngữ nghĩa (Điều, Khoản) hoặc theo token/ký tự có overlap. Phụ trách: TV1."""

import re
from typing import Dict, List


class TextChunker:
    """Bộ chia nhỏ văn bản cho hệ thống RAG."""

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
        # Tách theo biểu thức quy chế: "Điều 1.", "Điều 2:", v.v.
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
