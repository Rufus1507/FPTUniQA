"""Unit tests cho HybridRetriever với các chế độ metadata_mode (none, hard, soft) và soft boost ranking."""

import pytest
from unittest.mock import MagicMock
from FPTUniQA.retrieval.retriever import HybridRetriever


def test_hybrid_retriever_param_validation():
    # beta >= 1.0 -> ValueError
    with pytest.raises(ValueError):
        HybridRetriever(auto_load=False, beta=1.0)
    # beta < 0.0 -> ValueError
    with pytest.raises(ValueError):
        HybridRetriever(auto_load=False, beta=-0.1)
    # alpha < 0.0 -> ValueError
    with pytest.raises(ValueError):
        HybridRetriever(auto_load=False, alpha=-0.5)


def test_hybrid_retriever_soft_mode_boost():
    mock_bm25 = MagicMock()
    mock_dense = MagicMock()

    doc_match = {"id": "doc_match", "metadata": {"cohort": "K18"}}
    doc_neutral = {"id": "doc_neutral", "metadata": {}}
    doc_mismatch = {"id": "doc_mismatch", "metadata": {"cohort": "K21"}}

    # Cả hai retriever trả về 3 doc với điểm số ngang nhau
    mock_bm25.retrieve.return_value = [
        (doc_mismatch, 1.0),
        (doc_neutral, 1.0),
        (doc_match, 1.0),
    ]
    mock_dense.retrieve.return_value = [
        (doc_mismatch, 1.0),
        (doc_neutral, 1.0),
        (doc_match, 1.0),
    ]

    retriever = HybridRetriever(
        bm25_retriever=mock_bm25,
        dense_retriever=mock_dense,
        reranker=None,
        auto_load=False,
        cache=None,
        metadata_mode="soft",
        alpha=0.3,
        beta=0.3,
    )

    results = retriever.retrieve(
        query="quy định học vụ",
        top_k=3,
        metadata_filter={"cohort": "K18"},
        rerank=False,
    )

    # Kiểm tra: BM25/Dense con KHÔNG nhận metadata_filter trong soft mode
    assert mock_bm25.retrieve.call_args[1].get("metadata_filter") is None
    assert mock_dense.retrieve.call_args[1].get("metadata_filter") is None

    # Sau Soft Boosting: doc_match phải vươn lên top 1, doc_neutral ở top 2, doc_mismatch ở top 3
    result_ids = [d["id"] for d, _ in results]
    assert result_ids[0] == "doc_match"
    assert result_ids[1] == "doc_neutral"
    assert result_ids[2] == "doc_mismatch"
