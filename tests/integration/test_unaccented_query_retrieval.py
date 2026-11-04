"""Integration tests cho Hybrid Retrieval với cả query tiếng Việt không dấu và có dấu (Bước 7)."""

import pytest
from FPTUniQA.retrieval.retriever import HybridRetriever


@pytest.fixture(scope="module")
def hybrid_retriever():
    retriever = HybridRetriever(auto_load=True)
    return retriever


def test_graduation_query_unaccented_vs_accented(hybrid_retriever):
    """Kiểm tra câu hỏi tốt nghiệp không dấu và có dấu đều lấy được chunk 1.5.2 Điều kiện tốt nghiệp."""
    q_unacc = "dieu kien de sinh vien duoc xet tot nghiep la gi"
    res_unacc = hybrid_retriever.retrieve_contract2(q_unacc, top_k=3)
    assert len(res_unacc) > 0

    titles_unacc = [c.get("title", "") for c in res_unacc]
    # Khẳng định top-1 hoặc top-3 chứa điều kiện xét tốt nghiệp
    assert any("tốt nghiệp" in t.lower() for t in titles_unacc)
    # Khẳng định không bị chunk bài hát truyền thống chiếm top
    assert "Bài hát truyền thống" not in titles_unacc[0]

    q_acc = "Điều kiện để sinh viên được xét tốt nghiệp là gì?"
    res_acc = hybrid_retriever.retrieve_contract2(q_acc, top_k=3)
    titles_acc = [c.get("title", "") for c in res_acc]
    assert any("tốt nghiệp" in t.lower() for t in titles_acc)


def test_ojt_query_unaccented(hybrid_retriever):
    """Kiểm tra câu hỏi OJT không dấu truy xuất đúng chunk thực tập tốt nghiệp."""
    q_ojt_unacc = "sinh vien can bao nhieu tin chi de di ojt thuc tap doanh nghiep"
    res = hybrid_retriever.retrieve_contract2(q_ojt_unacc, top_k=5)
    assert len(res) > 0
    contents = " ".join([c.get("content", "") + " " + c.get("title", "") for c in res]).lower()
    assert "thực tập" in contents or "ojt" in contents or "tín chỉ" in contents
