"""Tính toán các chỉ số đánh giá tầng tìm kiếm: Recall@K, MRR, NDCG, Hit@K."""

import math
from typing import List, Set


def compute_hit_rate_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """Hit Rate @ K: 1.0 nếu có ít nhất 1 tài liệu đúng nằm trong top K, ngược lại 0.0."""
    top_k_ids = set(retrieved_ids[:k])
    return 1.0 if len(top_k_ids.intersection(ground_truth_ids)) > 0 else 0.0


def compute_recall_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """Recall @ K: Tỷ lệ tài liệu đúng được tìm thấy trong top K trên tổng số tài liệu đúng."""
    if not ground_truth_ids:
        return 0.0
    top_k_ids = set(retrieved_ids[:k])
    hits = len(top_k_ids.intersection(ground_truth_ids))
    return hits / len(ground_truth_ids)


def compute_mrr(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int = 20) -> float:
    """Mean Reciprocal Rank (MRR): Nghịch đảo của thứ hạng đầu tiên tìm thấy tài liệu đúng."""
    for rank, doc_id in enumerate(retrieved_ids[:k], start=1):
        if doc_id in ground_truth_ids:
            return 1.0 / rank
    return 0.0


def compute_ndcg_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int = 10) -> float:
    """Normalized Discounted Cumulative Gain (NDCG@K) cho độ liên quan nhị phân (0 hoặc 1)."""
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        rel = 1.0 if doc_id in ground_truth_ids else 0.0
        dcg += rel / math.log2(i + 2)

    # Tính IDCG lý tưởng
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(k, len(ground_truth_ids))))
    if idcg == 0:
        return 0.0
    return dcg / idcg
