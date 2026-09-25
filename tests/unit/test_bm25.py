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

def test_bm25_vietnamese_tokenization():
    """Kiểm tra tách từ tiếng Việt hoạt động (pyvi hoặc fallback)."""
    from university_qa.retrieval.bm25 import tokenize_vietnamese
    tokens = tokenize_vietnamese("Sinh viên đăng ký học phần")
    assert len(tokens) > 0
    # Should not have stopwords if filtering is on
    assert all(t != "" for t in tokens)

def test_bm25_contract2_output():
    """Kiểm tra output đúng format Contract 2."""
    docs = [
        {"id": "d1", "title": "Test", "text": "Học phí ngành CNTT",
         "metadata": {"doc_id": "QC-01", "effective_date": "2023-01-01",
                      "cohort": "K2023", "category": "hoc_phi"}},
    ]
    r = BM25Retriever()
    r.index(docs)
    results = r.retrieve_contract2("học phí", top_k=1)
    assert len(results) >= 1
    item = results[0]
    assert "doc_id" in item
    assert "score" in item
    assert "retrieval_strategy" in item
    assert item["retrieval_strategy"] == "bm25"
    assert "metadata" in item

def test_bm25_save_and_load(tmp_path):
    """Kiểm tra save/load index trên đĩa."""
    docs = [
        {"id": "1", "title": "A", "text": "Quy chế đào tạo tín chỉ"},
        {"id": "2", "title": "B", "text": "Học bổng khuyến khích học tập"},
    ]
    r = BM25Retriever()
    r.index(docs)
    r.save(tmp_path)

    r2 = BM25Retriever()
    r2.load(tmp_path)
    results = r2.retrieve("học bổng", top_k=1)
    assert len(results) >= 1
    assert results[0][0]["id"] == "2"

def test_bm25_empty_corpus():
    """Kiểm tra xử lý edge case corpus rỗng."""
    r = BM25Retriever()
    r.index([])
    results = r.retrieve("bất kỳ câu hỏi nào")
    assert results == []

def test_bm25_no_match_returns_empty():
    """Kiểm tra query không liên quan trả về danh sách rỗng."""
    docs = [{"id": "1", "title": "X", "text": "Quy chế đào tạo"}]
    r = BM25Retriever()
    r.index(docs)
    results = r.retrieve("xyzabc12345notexist", top_k=5)
    assert results == []
