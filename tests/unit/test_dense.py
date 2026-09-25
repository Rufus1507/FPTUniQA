"""Kiểm thử đơn vị cho bộ tìm kiếm Dense FAISS."""
from university_qa.retrieval.dense import DenseRetriever
from university_qa.retrieval.embedding import EmbeddingModel

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
