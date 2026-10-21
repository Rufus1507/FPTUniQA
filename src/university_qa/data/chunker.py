"""Phân đoạn văn bản quy chế theo ngữ nghĩa (Điều, Khoản) hoặc theo token/ký tự có overlap. Phụ trách: TV1."""

import re
from typing import Dict, List


# Cấu hình phân đoạn chuẩn cho văn bản quy chế tiếng Việt
CHUNK_CONFIG = {
    "chunk_size_chars": 1500,       # Tương đương ~500 tokens tiếng Việt có dấu
    "chunk_overlap_chars": 200,     # Tương đương ~65 tokens
    "min_chunk_size_chars": 150,    # Tương đương ~50 tokens
    "approx_tokens_per_chunk": 500,
    "approx_tokens_overlap": 50,
}


class TextChunker:
    """Bộ chia nhỏ văn bản cho hệ thống RAG Sổ tay đại học."""

    def __init__(
        self,
        chunk_size: int = CHUNK_CONFIG["chunk_size_chars"],
        chunk_overlap: int = CHUNK_CONFIG["chunk_overlap_chars"],
        min_chunk_size: int = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = (
            min_chunk_size
            if min_chunk_size is not None
            else min(chunk_size // 4, CHUNK_CONFIG["min_chunk_size_chars"])
        )

    def chunk_by_characters(self, text: str) -> List[str]:
        """Cắt đoạn văn bản theo số ký tự với bước trượt overlap."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        step = max(self.chunk_size - self.chunk_overlap, 1)

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start += step

        return chunks

    def chunk_by_legal_sections(self, text: str) -> List[Dict[str, str]]:
        """Phân đoạn thông minh theo cấu trúc Chương/Điều/Khoản và Mục của Sổ tay sinh viên ĐH FPT."""
        # Biểu thức chính quy bắt: Chương X, Điều Y, Mục Z, Số La Mã (I., II.), Tiểu mục (1.1, 6.3.2)
        pattern = r"(?m)^(?=(?:(?:Chương|Điều|Mục)\s+[IVXLCDM\d]+|[IVXLCDM]+\.\s+|\d+\.\d+(?:\.\d+)?\s+)[^\n]+)"
        raw_parts = [p.strip() for p in re.split(pattern, text) if p.strip()]

        if len(raw_parts) <= 1:
            # Fallback nếu không phát hiện các mục tiêu đề
            legacy_pattern = r"(Điều\s+\d+[\.\:]\s*[^\n]+)"
            legacy_parts = re.split(legacy_pattern, text)
            if len(legacy_parts) > 1:
                chunks = []
                if legacy_parts[0].strip():
                    chunks.append({"title": "Phần mở đầu", "text": legacy_parts[0].strip()})
                for i in range(1, len(legacy_parts), 2):
                    title = legacy_parts[i].strip()
                    content = legacy_parts[i + 1].strip() if i + 1 < len(legacy_parts) else ""
                    full = f"{title}\n{content}".strip()
                    if len(full) > self.chunk_size:
                        for idx, sc in enumerate(self.chunk_by_characters(full)):
                            chunks.append({"title": f"{title} (Phần {idx + 1})", "text": sc})
                    else:
                        chunks.append({"title": title, "text": full})
                return chunks

            # Nếu văn bản hoàn toàn không có heading
            chunks = []
            for c in self.chunk_by_characters(text):
                chunks.append({"title": "Quy chế chung", "text": c})
            return chunks

        chunks: List[Dict[str, str]] = []
        for p in raw_parts:
            lines = [l.strip() for l in p.split("\n") if l.strip()]
            header = lines[0] if lines else "Quy chế học vụ"

            # Nếu đoạn quá dài, chia nhỏ kèm overlap
            if len(p) > self.chunk_size:
                sub_chunks = self.chunk_by_characters(p)
                for idx, sc in enumerate(sub_chunks):
                    chunks.append({
                        "title": f"{header} (Phần {idx + 1})",
                        "text": sc
                    })
            elif len(p) < self.min_chunk_size and chunks:
                # Gộp đoạn quá ngắn vào chunk liền kề để không mất ngữ cảnh
                chunks[-1]["text"] += "\n\n" + p
            else:
                chunks.append({
                    "title": header,
                    "text": p
                })

        return chunks
