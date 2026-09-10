"""Kiểm thử đơn vị cho bộ tìm kiếm BM25."""

from university_qa.retrieval.bm25 import BM25Retriever


def test_bm25_retriever():
    docs = [
        {"id": "1", "title": "Học phí", "text": "Học phí ngành công nghệ thông tin là 650000 VNĐ."},
        {"id": "2", "title": "Kỷ luật", "text": "Sinh viên bị cảnh báo học tập 3 lần liên tiếp sẽ bị thôi học."},
    ]
    retriever = BM25Retriever()
    retriever.index(docs)

    results = retriever.retrieve("học phí công nghệ thông tin", top_k=2)
    assert len(results) >= 1
    best_doc, score = results[0]
    assert best_doc["id"] == "1"
    assert score > 0
