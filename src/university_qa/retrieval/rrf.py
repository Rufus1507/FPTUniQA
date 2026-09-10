"""Thuật toán hợp nhất kết quả Reciprocal Rank Fusion (RRF). Phụ trách: TV2."""

from typing import Any, Dict, List, Tuple


def reciprocal_rank_fusion(
    ranked_runs: List[List[Tuple[Dict[str, Any], float]]],
    k: int = 60,
    top_n: int = 10,
) -> List[Tuple[Dict[str, Any], float]]:
    """Hợp nhất các danh sách tài liệu từ nhiều bộ tìm kiếm bằng công thức RRF:

    RRF_score(d) = sum_{run} (1 / (k + rank_run(d)))
    """
    scores: Dict[str, float] = {}
    doc_lookup: Dict[str, Dict[str, Any]] = {}

    for run in ranked_runs:
        for rank, (doc, _) in enumerate(run, start=1):
            doc_id = str(doc.get("id", id(doc)))
            doc_lookup[doc_id] = doc
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # Sắp xếp theo điểm RRF giảm dần
    sorted_doc_ids = sorted(scores.keys(), key=lambda did: scores[did], reverse=True)

    results = []
    for doc_id in sorted_doc_ids[:top_n]:
        results.append((doc_lookup[doc_id], scores[doc_id]))

    return results
