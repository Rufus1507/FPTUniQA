"""Unit tests cho BM25 Retriever hỗ trợ query không dấu và có dấu."""

import pytest
from FPTUniQA.retrieval.bm25 import BM25Retriever


@pytest.fixture(scope="module")
def bm25_retriever():
    retriever = BM25Retriever()
    retriever.load("data/processed/bm25_index")
    return retriever


def test_bm25_unaccented_graduation_query(bm25_retriever):
    """Kiểm tra BM25 truy xuất với query không dấu khớp đúng chunk tốt nghiệp."""
    q_unacc = "dieu kien de sinh vien duoc xet tot nghiep la gi"
    results = bm25_retriever.retrieve(q_unacc, top_k=5)
    assert len(results) > 0

    top_doc_ids = [doc.get("id") or doc.get("doc_id") for doc, _ in results]
    top_titles = [doc.get("title", "") for doc, _ in results]

    # Khẳng định chunk điều kiện tốt nghiệp nằm trong top-5
    assert any("tốt nghiệp" in t.lower() for t in top_titles)
    # Khẳng định chunk bài hát truyền thống không nằm ở Top 1
    assert "Bài hát truyền thống" not in top_titles[0]


def test_bm25_accented_query_consistency(bm25_retriever):
    """Kiểm tra BM25 truy xuất với query có dấu giữ nguyên chất lượng."""
    q_acc = "Điều kiện để sinh viên được xét tốt nghiệp là gì?"
    results = bm25_retriever.retrieve(q_acc, top_k=5)
    top_titles = [doc.get("title", "") for doc, _ in results]
    assert any("tốt nghiệp" in t.lower() for t in top_titles)
