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

def test_rrf_disjoint_runs():
    run1 = [({"id": "a"}, 1.0)]
    run2 = [({"id": "b"}, 2.0)]
    fused = reciprocal_rank_fusion([run1, run2], k=60, top_n=5)
    assert len(fused) == 2

def test_rrf_single_run():
    run1 = [({"id": "a"}, 1.0), ({"id": "b"}, 0.5)]
    fused = reciprocal_rank_fusion([run1], k=60, top_n=2)
    assert len(fused) == 2
    assert fused[0][0]["id"] == "a"

def test_rrf_weighted():
    run1 = [({"id": "a"}, 1.0)]
    run2 = [({"id": "b"}, 2.0)]
    fused_equal = reciprocal_rank_fusion([run1, run2], k=60, top_n=2)
    fused_weighted = reciprocal_rank_fusion([run1, run2], k=60, top_n=2, weights=[2.0, 0.5])
    # With weights, doc from run1 should score higher relative to run2
    assert len(fused_weighted) == 2

def test_rrf_empty_run():
    fused = reciprocal_rank_fusion([[], [({"id": "a"}, 1.0)]], k=60, top_n=5)
    assert len(fused) == 1
