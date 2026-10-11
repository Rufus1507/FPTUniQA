"""Kiểm thử đơn vị cho bộ tìm kiếm BM25."""

from FPTUniQA.retrieval.bm25 import BM25Retriever


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
    from FPTUniQA.retrieval.bm25 import tokenize_vietnamese
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

def test_bm25_contract2_strict_pydantic_validation():
    """Kiểm tra Contract 2 xuất ra score chuẩn hóa trong [0.0, 1.0] và hợp lệ với Pydantic DocumentChunk."""
    from contracts import DocumentChunk
    docs = [
        {"id": "doc_test", "title": "Tiêu đề mẫu", "text": "Quy chế cảnh báo học vụ",
         "metadata": {"doc_id": "doc_test", "effective_date": "2024-01-01", "cohort": "K2024", "category": "quy_che"}},
    ]
    r = BM25Retriever()
    r.index(docs)
    res = r.retrieve_contract2("quy chế cảnh báo học vụ", top_k=1)
    assert len(res) == 1
    chunk = DocumentChunk(**res[0])
    assert 0.0 <= chunk.score <= 1.0
    assert chunk.retrieval_strategy == "bm25"
    assert chunk.doc_id == "doc_test"

def test_bm25_empty_and_whitespace_query():
    """Kiểm tra query rỗng hoặc whitespace trả về [] ngay lập tức."""
    docs = [{"id": "1", "title": "A", "text": "Nội dung quy chế"}]
    r = BM25Retriever()
    r.index(docs)
    assert r.retrieve("") == []
    assert r.retrieve("   ") == []
    assert r.retrieve(None) == []
    assert r.retrieve_contract2("") == []

def test_bm25_punctuation_cleaning():
    """Kiểm tra tokenize loại bỏ dấu câu không đưa vào vocabulary terms."""
    from FPTUniQA.retrieval.bm25 import tokenize_vietnamese
    tokens = tokenize_vietnamese("Điều kiện cảnh báo học vụ (2024)? *học phí*!")
    assert "?" not in tokens
    assert "!" not in tokens
    assert "(" not in tokens
    assert ")" not in tokens
    assert "*" not in tokens

def test_bm25_metadata_filter_wildcard():
    """Kiểm tra metadata filter với wildcard 'all'/'All' và alias trường."""
    docs = [
        {"id": "d1", "title": "A", "text": "Học phí", "campus": "all", "metadata": {"campus": "all"}},
        {"id": "d2", "title": "B", "text": "Học phí", "campus": "ha_noi", "metadata": {"campus": "ha_noi"}},
        {"id": "d3", "title": "C", "text": "Học phí", "campus": "da_nang", "metadata": {"campus": "da_nang"}},
    ]
    r = BM25Retriever()
    r.index(docs)
    res = r.retrieve("học phí", top_k=5, metadata_filter={"campus": "ha_noi"})
    matched_ids = [d["id"] for d, _ in res]
    assert "d1" in matched_ids  # 'all' matches 'ha_noi'
    assert "d2" in matched_ids  # exact match
    assert "d3" not in matched_ids  # da_nang should be excluded

def test_bm25_corpus_property():
    """Kiểm tra getter và setter cho property corpus."""
    r = BM25Retriever()
    r.corpus = [{"id": "1", "text": "hello"}]
    assert len(r.documents) == 1
    assert r.corpus[0]["id"] == "1"

