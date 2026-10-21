"""Kiểm thử đơn vị cho DocumentLoader và Hybrid Gateway."""

from pathlib import Path
from university_qa.data.loader import DocumentLoader


def test_loader_text_file(tmp_path):
    test_file = tmp_path / "test_doc.md"
    test_file.write_text("# Tiêu đề quy chế\n\nNội dung điều khoản đào tạo.", encoding="utf-8")

    loader = DocumentLoader()
    doc = loader.load_file(test_file)

    assert doc["source"] == "test_doc.md"
    assert "Nội dung điều khoản đào tạo." in doc["content"]
    assert doc["engine"] == "native_text"


def test_loader_markitdown_converter(tmp_path):
    test_file = tmp_path / "rules.md"
    test_file.write_text("| Khóa | Học phí |\n|---|---|\n| K19 | 28.7M |", encoding="utf-8")

    loader = DocumentLoader()
    doc = loader.load_with_markitdown(test_file)

    assert doc["engine"] == "markitdown"
    assert "K19" in doc["content"]
