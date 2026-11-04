"""Unit tests cho Confidence-Aware Soft Boosting và Evaluator Wrong-Cohort chuẩn hóa."""

import pytest
from FPTUniQA.evaluation.retrieval_metrics import (
    compute_wrong_cohort_rate,
    compute_recall_at_k_equivalent,
)
from FPTUniQA.retrieval.filter import classify_metadata_match


def test_classify_metadata_match_shared_policy():
    """Tài liệu quy chế toàn trường (scope ALL / không ghi cohort) phải trả về 'neutral'."""
    doc_shared = {
        "id": "doc_shared_001",
        "metadata": {"cohort": "ALL", "campus": "ALL"}
    }
    meta_filter = {"cohort": "K18", "confidence": 0.9}
    assert classify_metadata_match(doc_shared, meta_filter) == "neutral"


def test_classify_metadata_match_exact():
    """Khớp trực tiếp khóa K18 -> 'match'."""
    doc_k18 = {
        "id": "doc_k18_001",
        "metadata": {"cohort": "K18", "campus": "Hòa Lạc"}
    }
    meta_filter = {"cohort": "K18", "confidence": 0.9}
    assert classify_metadata_match(doc_k18, meta_filter) == "match"


def test_classify_metadata_match_conflict():
    """Xung đột khóa K17 khi hỏi K18 -> 'mismatch'."""
    doc_k17 = {
        "id": "doc_k17_001",
        "metadata": {"cohort": "K17", "campus": "Hòa Lạc"}
    }
    meta_filter = {"cohort": "K18", "confidence": 0.9}
    assert classify_metadata_match(doc_k17, meta_filter) == "mismatch"


def test_wrong_cohort_rate_neutral():
    """Câu hỏi quy chế chung không có expected_cohorts -> trả về None (bỏ khỏi denominator)."""
    top5 = ["doc_fpt_k17_001", "doc_fpt_k20_002"]
    res = compute_wrong_cohort_rate(top5, expected_cohorts=set())
    assert res is None


def test_wrong_cohort_rate_equiv_exempt():
    """Tài liệu khác khóa nhưng nằm trong equiv_group -> miễn trừ, trả về 0.0."""
    top5 = ["doc_fpt_k17_0588"]  # Quy chế phúc khảo K17
    expected = {"K20"}
    equiv_groups = [["doc_fpt_k20_0127", "doc_fpt_k17_0588"]]
    res = compute_wrong_cohort_rate(top5, expected_cohorts=expected, equiv_groups=equiv_groups)
    assert res == 0.0


def test_wrong_cohort_rate_true_mismatch():
    """Tài liệu khác khóa và KHÔNG thuộc equiv_group -> trả về 1.0."""
    top5 = ["doc_fpt_k17_0582"]  # Biểu phí K17
    expected = {"K20"}
    equiv_groups = []
    res = compute_wrong_cohort_rate(top5, expected_cohorts=expected, equiv_groups=equiv_groups)
    assert res == 1.0


def test_recall_at_k_equivalent():
    """Kiểm tra Equivalent Recall: hit nếu doc nằm trong equiv_group của gold."""
    top5 = ["doc_fpt_k17_0588"]
    gold = {"doc_fpt_k20_0127"}
    equiv = [["doc_fpt_k20_0127", "doc_fpt_k17_0588"]]
    # Doc ID thông thường: trượt (0.0)
    # Equivalent: trúng (1.0)
    assert compute_recall_at_k_equivalent(top5, gold, equiv_groups=equiv, k=5) == 1.0
