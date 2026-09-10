"""Kiểm thử thuật toán Reciprocal Rank Fusion (RRF)."""

from university_qa.retrieval.rrf import reciprocal_rank_fusion


def test_reciprocal_rank_fusion():
    run1 = [
        ({"id": "doc_a", "title": "A"}, 0.9),
        ({"id": "doc_b", "title": "B"}, 0.8),
    ]
    run2 = [
        ({"id": "doc_b", "title": "B"}, 12.5),
        ({"id": "doc_a", "title": "A"}, 9.1),
    ]

    fused = reciprocal_rank_fusion([run1, run2], k=60, top_n=2)
    assert len(fused) == 2
    # Cả hai tài liệu đều xuất hiện
    fused_ids = [d["id"] for d, _ in fused]
    assert "doc_a" in fused_ids
    assert "doc_b" in fused_ids
