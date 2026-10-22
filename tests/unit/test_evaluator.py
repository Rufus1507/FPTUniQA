"""Unit tests cho module RAGEvaluator và các metrics đánh giá hệ thống."""

from unittest.mock import MagicMock
import pytest

from FPTUniQA.evaluation.evaluator import RAGEvaluator


@pytest.fixture
def mock_pipeline():
    pipeline = MagicMock()
    pipeline.retriever = MagicMock()
    cache_mock = MagicMock()
    cache_mock.get_stats.return_value = {
        "hits": 15,
        "misses": 5,
        "total_lookups": 20,
        "hit_rate": 0.75,
        "cached_entries": 10,
    }
    pipeline.retriever.cache = cache_mock
    return pipeline


def test_evaluate_latency_distribution(mock_pipeline):
    evaluator = RAGEvaluator(mock_pipeline)

    # Dãy độ trễ giả lập
    latencies = [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0]
    metrics = evaluator.evaluate_latency(latencies)

    assert metrics["mean_ms"] == 550.0
    assert metrics["min_ms"] == 100.0
    assert metrics["max_ms"] == 1000.0
    assert metrics["p50_ms"] == 600.0
    assert metrics["p95_ms"] == 1000.0


def test_evaluate_latency_empty(mock_pipeline):
    evaluator = RAGEvaluator(mock_pipeline)
    metrics = evaluator.evaluate_latency([])
    assert metrics["mean_ms"] == 0.0
    assert metrics["p50_ms"] == 0.0


def test_evaluate_routing_accuracy(mock_pipeline):
    evaluator = RAGEvaluator(mock_pipeline)

    questions = [
        {"query": "Học phí KTPM?", "expected_route": "structured_lookup"},
        {"query": "Cảnh báo học vụ?", "expected_route": "rag_pipeline"},
        {"query": "Thời tiết hôm nay?", "expected_route": "ood"},
    ]

    run_results = [
        {"route": "structured_lookup"},
        {"route": "rag_pipeline"},
        {"route": "rag_pipeline"},  # 1 case sai
    ]

    res = evaluator.evaluate_routing(questions, run_results)
    assert res["total_evaluated"] == 3
    assert res["correct_routes"] == 2
    assert res["routing_accuracy"] == pytest.approx(0.6667, rel=1e-3)


def test_evaluate_cache_performance(mock_pipeline):
    evaluator = RAGEvaluator(mock_pipeline)
    stats = evaluator.evaluate_cache_performance()
    assert stats["hits"] == 15
    assert stats["misses"] == 5
    assert stats["hit_rate"] == 0.75


def test_evaluate_answer_quality(mock_pipeline):
    evaluator = RAGEvaluator(mock_pipeline)

    questions = [
        {
            "query": "Điều kiện tốt nghiệp?",
            "golden_answer": "Sinh viên phải hoàn thành tất cả tín chỉ và có chứng chỉ tiếng Anh.",
        }
    ]

    run_results = [
        {
            "answer": "Sinh viên cần hoàn thành tất cả các tín chỉ và nộp chứng chỉ tiếng Anh.",
            "retrieved_chunks": [
                {"text": "Quy chế quy định sinh viên phải hoàn thành tất cả tín chỉ và có chứng chỉ tiếng Anh để xét tốt nghiệp."}
            ],
        }
    ]

    res = evaluator.evaluate_answer_quality(questions, run_results)
    assert res["mean_faithfulness"] > 0.5
    assert res["mean_relevance"] > 0.4
    assert res["hallucination_rate"] == 0.0


def test_evaluate_ood_rejection(mock_pipeline):
    evaluator = RAGEvaluator(mock_pipeline)
    mock_pipeline.run.side_effect = [
        {"intent": "ood", "answer": "Câu hỏi nằm ngoài phạm vi."},
        {"intent": "factoid", "answer": "Học phí là 28 triệu."},
    ]

    ood_questions = [
        {"query": "Nấu món phở bò như thế nào?"},
        {"query": "Thủ đô của Úc là gì?"},
    ]

    res = evaluator.evaluate_ood(ood_questions)
    assert res["ood_rejection_accuracy"] == 0.5
