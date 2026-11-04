"""Tính toán các chỉ số đánh giá tầng tìm kiếm: Recall@K, MRR, NDCG, Hit@K, Equivalent Recall, Wrong Cohort Rate."""

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union


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


def compute_recall_at_k_doc_id(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """Alias cho Recall @ K theo mã Doc ID chính xác."""
    return compute_recall_at_k(retrieved_ids, ground_truth_ids, k=k)


def compute_recall_at_k_equivalent(
    retrieved_ids: List[str],
    ground_truth_ids: Set[str],
    equiv_groups: Optional[List[List[str]]] = None,
    k: int = 5,
) -> float:
    """Recall @ K theo nhóm nội dung tương đương (Equivalent Group).

    - Nếu equiv_groups rỗng: tính theo Recall doc ID truyền thống.
    - Nếu có equiv_groups: một tài liệu trong top K được tính là Hit nếu nó thuộc nhóm tương đương
      với bất kỳ tài liệu gold nào.
    """
    if not ground_truth_ids:
        return 0.0

    if not equiv_groups:
        return compute_recall_at_k(retrieved_ids, ground_truth_ids, k=k)

    # Mở rộng tập gold sang các doc ID tương đương nội dung
    expanded_gold: Set[str] = set(ground_truth_ids)
    for grp in equiv_groups:
        grp_set = set(grp)
        if grp_set & set(ground_truth_ids):
            expanded_gold.update(grp_set)

    top_k_ids = set(retrieved_ids[:k])
    hits = len(top_k_ids.intersection(expanded_gold))
    # Bounded bởi tỷ lệ tài liệu tìm thấy / số tài liệu gold tối thiểu
    return min(1.0, hits / max(1, len(ground_truth_ids)))


def extract_doc_cohort(doc_or_id: Union[str, Dict[str, Any]]) -> Optional[str]:
    """Trích xuất mã khóa Kxx từ doc dict hoặc doc_id string (VD: 'doc_fpt_k17_0605' -> 'K17')."""
    if isinstance(doc_or_id, dict):
        meta = doc_or_id.get("metadata", {})
        cohort_val = meta.get("cohort", doc_or_id.get("cohort", meta.get("applies_to_cohort")))
        if cohort_val and str(cohort_val).strip().lower() not in ("all", "chung", "none", ""):
            m = re.search(r"k(\d{1,2})", str(cohort_val), re.IGNORECASE)
            if m:
                return f"K{m.group(1)}"
        doc_id = str(doc_or_id.get("id") or doc_or_id.get("doc_id") or "")
    else:
        doc_id = str(doc_or_id)

    m = re.search(r"k(\d{1,2})", doc_id, re.IGNORECASE)
    if m:
        return f"K{m.group(1)}"
    return None


def compute_wrong_cohort_rate(
    retrieved_docs_or_ids: List[Any],
    expected_cohorts: Optional[Set[str]],
    k: int = 5,
) -> float:
    """Wrong-Cohort Rate cho 1 truy vấn:
    Trả về 1.0 nếu trong top K có ít nhất một tài liệu có khóa xác định rõ nhưng KHÔNG thuộc expected_cohorts.
    Tài liệu chung / không có khóa không bị tính là sai khóa.
    Nếu expected_cohorts rỗng / None: trả về 0.0 (không đánh giá).
    """
    if not expected_cohorts:
        return 0.0

    top_k_items = retrieved_docs_or_ids[:k]
    for item in top_k_items:
        c = extract_doc_cohort(item)
        if c is not None and c not in expected_cohorts:
            return 1.0

    return 0.0


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
