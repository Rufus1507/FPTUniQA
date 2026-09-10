"""Kiểm thử tích hợp cho toàn bộ luồng RAGPipeline."""

from university_qa.pipeline.rag_pipeline import RAGPipeline


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
