"""Kiểm thử tích hợp cho bộ tìm kiếm lai (Hybrid Retriever: BM25 + FAISS)."""

from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.utils.io import read_jsonl


def test_hybrid_retrieval_pipeline():
    docs = read_jsonl("tests/fixtures/sample_corpus.jsonl")
    retriever = HybridRetriever()
    retriever.build_index(docs)

    results = retriever.retrieve("tối đa bao nhiêu tín chỉ", top_k=2)
    assert len(results) > 0
    top_doc, score = results[0]
    assert "tín chỉ" in top_doc["text"].lower()

def test_hybrid_contract2_validation():
    from contracts import DocumentChunk
    docs = read_jsonl("tests/fixtures/sample_corpus.jsonl")
    retriever = HybridRetriever()
    retriever.build_index(docs)

    results = retriever.retrieve_contract2("tín chỉ", top_k=2)
    assert len(results) > 0
    for r in results:
        chunk = DocumentChunk(**r)
        assert 0.0 <= chunk.score <= 1.0
        assert chunk.retrieval_strategy in ("bm25", "hybrid")

def test_hybrid_empty_query():
    retriever = HybridRetriever()
    assert retriever.retrieve("") == []
    assert retriever.retrieve("   ") == []
    assert retriever.retrieve(None) == []
    assert retriever.retrieve_contract2("") == []

