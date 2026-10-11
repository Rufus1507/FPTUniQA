from FPTUniQA.retrieval.dense import DenseRetriever
from FPTUniQA.retrieval.embedding import EmbeddingModel

def test_dense_build_and_retrieve():
    docs = [
        {"id": "1", "title": "Học phí", "text": "Học phí ngành CNTT"},
        {"id": "2", "title": "Kỷ luật", "text": "Sinh viên bị cảnh báo học tập"},
    ]
    emb = EmbeddingModel()  # Will use dummy mode
    r = DenseRetriever(embedding_model=emb)
    r.build_index(docs)
    results = r.retrieve("học phí", top_k=2)
    assert len(results) >= 1

def test_dense_metadata_filter():
    docs = [
        {"id": "1", "title": "A", "text": "Text A", "metadata": {"cohort": "K2023"}},
        {"id": "2", "title": "B", "text": "Text B", "metadata": {"cohort": "K2024"}},
    ]
    emb = EmbeddingModel()
    r = DenseRetriever(embedding_model=emb)
    r.build_index(docs)
    results = r.retrieve("text", top_k=5, metadata_filter={"cohort": "K2023"})
    for doc, _ in results:
        assert doc.get("metadata", {}).get("cohort") == "K2023"

def test_dense_save_and_load(tmp_path):
    docs = [{"id": "1", "title": "T", "text": "Test document"}]
    emb = EmbeddingModel()
    r = DenseRetriever(embedding_model=emb)
    r.build_index(docs)
    r.save(tmp_path)
    
    r2 = DenseRetriever(embedding_model=emb)
    r2.load(tmp_path)
    results = r2.retrieve("test", top_k=1)
    assert len(results) >= 1

def test_dense_contract2_pydantic_validation():
    """Kiểm tra Contract 2 xuất ra score chuẩn hóa trong [0.0, 1.0] và hợp lệ với Pydantic DocumentChunk."""
    from contracts import DocumentChunk
    docs = [{"id": "d1", "title": "A", "text": "Quy chế"}]
    emb = EmbeddingModel()
    r = DenseRetriever(embedding_model=emb)
    r.build_index(docs)
    res = r.retrieve_contract2("quy chế", top_k=1)
    assert len(res) == 1
    chunk = DocumentChunk(**res[0])
    assert 0.0 <= chunk.score <= 1.0
    assert chunk.retrieval_strategy == "dense"

def test_dense_empty_and_whitespace_query():
    """Kiểm tra DenseRetriever với query rỗng/whitespace trả về [] thay vì embed query giả."""
    docs = [{"id": "1", "title": "A", "text": "Text"}]
    emb = EmbeddingModel()
    r = DenseRetriever(embedding_model=emb)
    r.build_index(docs)
    assert r.retrieve("") == []
    assert r.retrieve("   ") == []
    assert r.retrieve(None) == []
    assert r.retrieve_contract2("") == []

def test_dense_metadata_filter_wildcard():
    """Kiểm tra lọc wildcard 'all' trong DenseRetriever."""
    docs = [
        {"id": "d1", "title": "A", "text": "Học phí", "campus": "all", "metadata": {"campus": "all"}},
        {"id": "d2", "title": "B", "text": "Học phí", "campus": "ha_noi", "metadata": {"campus": "ha_noi"}},
        {"id": "d3", "title": "C", "text": "Học phí", "campus": "da_nang", "metadata": {"campus": "da_nang"}},
    ]
    emb = EmbeddingModel()
    r = DenseRetriever(embedding_model=emb)
    r.build_index(docs)
    res = r.retrieve("học phí", top_k=5, metadata_filter={"campus": "ha_noi"})
    matched_ids = [d["id"] for d, _ in res]
    assert "d1" in matched_ids
    assert "d2" in matched_ids
    assert "d3" not in matched_ids

