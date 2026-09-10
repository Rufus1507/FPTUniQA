"""Kiểm thử đơn vị cho module chunker."""

from university_qa.data.chunker import TextChunker


def test_chunk_by_characters():
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    text = "Đây là một đoạn văn bản dài nhằm mục đích kiểm thử khả năng chia nhỏ theo ký tự của bộ chunker."
    chunks = chunker.chunk_by_characters(text)
    assert len(chunks) > 1
    assert all(len(c) <= 50 for c in chunks)


def test_chunk_by_legal_sections():
    chunker = TextChunker(chunk_size=200, chunk_overlap=20)
    text = (
        "Điều 1. Phạm vi áp dụng\nQuy chế này áp dụng cho toàn thể sinh viên.\n\n"
        "Điều 2. Đăng ký học tập\nSinh viên phải đăng ký học phần đúng hạn quy định."
    )
    sections = chunker.chunk_by_legal_sections(text)
    assert len(sections) == 2
    assert "Điều 1" in sections[0]["title"]
    assert "Điều 2" in sections[1]["title"]
