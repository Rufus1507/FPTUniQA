"""Kiểm thử tích hợp cho bộ tìm kiếm lai 2 giai đoạn (Hybrid Retriever: BM25 + FAISS + Reranker)."""

from contracts import DocumentChunk
from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.utils.io import read_jsonl


def test_hybrid_retrieval_pipeline():
    docs = read_jsonl("tests/fixtures/sample_corpus.jsonl")
    retriever = HybridRetriever()
    retriever.build_index(docs)

    results = retriever.retrieve("tối đa bao nhiêu tín chỉ", top_k=2, rerank=False)
    assert len(results) > 0
    top_doc, score = results[0]
    assert "tín chỉ" in top_doc["text"].lower()


def test_two_stage_retrieval_pipeline():
    docs = read_jsonl("tests/fixtures/sample_corpus.jsonl")
    retriever = HybridRetriever()
    retriever.build_index(docs)

    # Thử nghiệm 2 giai đoạn: candidate_k -> CrossEncoder Rerank -> top_k
    results = retriever.retrieve("tối đa bao nhiêu tín chỉ", top_k=2, candidate_k=5, rerank=True)
    assert len(results) > 0
    top_doc, score = results[0]
    assert "tín chỉ" in top_doc["text"].lower()
    assert 0.0 <= score <= 1.0


def test_hybrid_contract2_validation():
    docs = read_jsonl("tests/fixtures/sample_corpus.jsonl")
    retriever = HybridRetriever()
    retriever.build_index(docs)

    # Kiểm tra cả 2 chế độ: rerank=False và rerank=True
    for rerank_flag in [False, True]:
        results = retriever.retrieve_contract2("tín chỉ", top_k=2, rerank=rerank_flag)
        assert len(results) > 0
        for r in results:
            chunk = DocumentChunk(**r)
            assert 0.0 <= chunk.score <= 1.0
            assert chunk.retrieval_strategy in ("bm25", "hybrid")
            assert chunk.metadata.get("effective_date") is not None
            assert chunk.metadata.get("applies_to_cohort") is not None
            assert chunk.metadata.get("doc_type") is not None


def test_metadata_prefiltering_with_rerank():
    docs = read_jsonl("tests/fixtures/sample_corpus.jsonl")
    retriever = HybridRetriever()
    retriever.build_index(docs)

    results = retriever.retrieve_contract2(
        "học phí và quy chế",
        top_k=2,
        metadata_filter={"doc_type": "quy_che"},
        rerank=True,
    )
    for r in results:
        chunk = DocumentChunk(**r)
        assert chunk.category == "quy_che" or chunk.metadata.get("doc_type") == "quy_che"


def test_hybrid_empty_query():
    retriever = HybridRetriever()
    assert retriever.retrieve("") == []
    assert retriever.retrieve("   ") == []
    assert retriever.retrieve(None) == []
    assert retriever.retrieve_contract2("") == []


def test_hybrid_retriever_score_thresholding():
    """Kiểm tra cắt ngưỡng nhiễu score_threshold trong retrieve và retrieve_contract2."""
    docs = read_jsonl("tests/fixtures/sample_corpus.jsonl")
    retriever = HybridRetriever()
    retriever.build_index(docs)

    # Chạy không threshold
    all_chunks = retriever.retrieve_contract2("tín chỉ", top_k=5, score_threshold=0.0)
    assert len(all_chunks) > 0

    # Chạy với threshold cao
    filtered_chunks = retriever.retrieve_contract2("tín chỉ", top_k=5, score_threshold=0.999)
    for c in filtered_chunks:
        assert c["score"] >= 0.999


def test_hybrid_retriever_content_field_preservation():
    """Kiểm tra tài liệu chỉ có 'content' (Contract 2) không bị mất nội dung khi qua retrieve_contract2."""
    retriever = HybridRetriever(auto_load=False)
    custom_doc = {
        "id": "doc_content_only",
        "title": "Quy chế bảo lưu",
        "content": "Sinh viên được bảo lưu kết quả học tập tối đa 2 học kỳ liên tiếp.",
        "category": "quy_che",
    }
    retriever.build_index([custom_doc])

    results = retriever.retrieve_contract2("bảo lưu học tập", top_k=1, rerank=False)
    assert len(results) == 1
    assert results[0]["text"] == custom_doc["content"]
    assert results[0]["content"] == custom_doc["content"]
    assert results[0]["doc_id"] == "doc_content_only"


def test_retrieval_strategy_dense_and_bm25_modes():
    """Kiểm tra trường retrieval_strategy phản ánh chính xác trạng thái index (hybrid / dense / bm25)."""
    retriever = HybridRetriever(auto_load=False)
    retriever.retrieve = lambda *args, **kwargs: [({"id": "d1", "text": "test"}, 0.8)]

    # 1. Cả 2 đều None -> bm25
    assert retriever.retrieve_contract2("q")[0]["retrieval_strategy"] == "bm25"

    # 2. Chỉ có dense index
    class DummyFAISS:
        ntotal = 10
    retriever.dense_retriever._faiss_index = DummyFAISS()
    assert retriever.retrieve_contract2("q")[0]["retrieval_strategy"] == "dense"

    # 3. Cả 2 đều có index -> hybrid
    class DummyBM25:
        pass
    retriever.bm25_retriever.bm25 = DummyBM25()
    retriever.bm25_retriever.documents = [{"id": "d1"}]
    assert retriever.retrieve_contract2("q")[0]["retrieval_strategy"] == "hybrid"
