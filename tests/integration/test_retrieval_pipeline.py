"""Kiểm thử tích hợp cho bộ tìm kiếm lai (Hybrid Retriever: BM25 + FAISS)."""

from university_qa.retrieval.retriever import HybridRetriever
from university_qa.utils.io import read_jsonl


def test_hybrid_retrieval_pipeline():
    docs = read_jsonl("tests/fixtures/sample_corpus.jsonl")
    retriever = HybridRetriever()
    retriever.index(docs)

    results = retriever.retrieve("tối đa bao nhiêu tín chỉ", top_k=2)
    assert len(results) > 0
    top_doc, score = results[0]
    assert "tín chỉ" in top_doc["text"].lower()
