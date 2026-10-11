"""Kiểm thử tích hợp cho toàn bộ luồng RAGPipeline kết nối HybridRetriever thực tế."""

from FPTUniQA.pipeline.rag_pipeline import RAGPipeline


def test_rag_pipeline_flow():
    pipeline = RAGPipeline()
    pipeline.load_corpus("tests/fixtures/sample_corpus.jsonl")

    # Test câu hỏi quy chế
    res = pipeline.run("Được đăng ký tối đa bao nhiêu tín chỉ một học kỳ?", top_k=2)
    assert res["intent"] == "factoid"
    assert "answer" in res
    assert len(res["retrieved_documents"]) > 0

    # Test câu hỏi ngoài miền (OOD)
    ood_res = pipeline.run("Cách nấu món phở bò?", top_k=2)
    assert ood_res["intent"] == "ood"
    assert "nằm ngoài phạm vi" in ood_res["answer"]


def test_rag_pipeline_empty_retrieval_no_mock_injection():
    """Kiểm tra khi retriever không tìm thấy tài liệu, hệ thống thông báo lịch sự mà KHÔNG inject mock docs."""
    class EmptyRetriever:
        def retrieve_contract2(self, *args, **kwargs):
            return []

    pipeline = RAGPipeline(retriever=EmptyRetriever(), use_mock_fallback=False)
    res = pipeline.run("Quy định về cảnh báo học vụ XYZ12345 như thế nào?", top_k=2)

    assert "không tìm thấy tài liệu phù hợp" in res["answer"].lower()
    assert len(res["retrieved_documents"]) == 0
    assert len(res["citations"]) == 0


def test_rag_pipeline_mock_fallback_explicit():
    """Kiểm tra cờ use_mock_fallback=True chỉ kích hoạt khi được bật tường minh."""
    class EmptyRetriever:
        def retrieve_contract2(self, *args, **kwargs):
            return []

    pipeline = RAGPipeline(retriever=EmptyRetriever(), use_mock_fallback=True)
    res = pipeline.run("Quy chế cảnh báo học vụ", top_k=2)

    assert len(res["retrieved_documents"]) > 0
    assert res["retrieved_documents"][0]["retrieval_strategy"] == "mock"
