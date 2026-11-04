"""Unit tests cho các chỉ số đánh giá retrieval mở rộng (Equivalent Recall, Wrong Cohort Rate)."""

import pytest
from FPTUniQA.evaluation.retrieval_metrics import (
    compute_recall_at_k,
    compute_recall_at_k_doc_id,
    compute_recall_at_k_equivalent,
    compute_wrong_cohort_rate,
    extract_doc_cohort,
)


def test_standard_vs_equivalent_recall():
    gold = {"doc_k19_001"}
    equiv = [["doc_k19_001", "doc_k18_001", "doc_k20_001"]]

    # Trường hợp 1: Trúng đích danh doc ID
    retrieved_exact = ["doc_k19_001", "doc_other"]
    assert compute_recall_at_k(retrieved_exact, gold, k=5) == 1.0
    assert compute_recall_at_k_equivalent(retrieved_exact, gold, equiv, k=5) == 1.0

    # Trường hợp 2: Trượt doc ID nhưng trúng tài liệu tương đương (Trượt giả)
    retrieved_equiv = ["doc_k18_001", "doc_other"]
    assert compute_recall_at_k(retrieved_equiv, gold, k=5) == 0.0
    assert compute_recall_at_k_equivalent(retrieved_equiv, gold, equiv, k=5) == 1.0

    # Trường hợp 3: Trượt cả hai
    retrieved_miss = ["doc_random_1", "doc_random_2"]
    assert compute_recall_at_k(retrieved_miss, gold, k=5) == 0.0
    assert compute_recall_at_k_equivalent(retrieved_miss, gold, equiv, k=5) == 0.0

    # Trường hợp 4: equiv_group rỗng fallback về standard recall
    assert compute_recall_at_k_equivalent(retrieved_exact, gold, equiv_groups=None, k=5) == 1.0
    assert compute_recall_at_k_equivalent(retrieved_equiv, gold, equiv_groups=None, k=5) == 0.0


def test_wrong_cohort_rate():
    expected_cohorts = {"K18", "K19"}

    # Có doc sai khóa (K21) nằm trong top-5
    retrieved_with_wrong = ["doc_fpt_k18_0100", "doc_fpt_k21_0200", "doc_general"]
    assert compute_wrong_cohort_rate(retrieved_with_wrong, expected_cohorts, k=5) == 1.0

    # Chỉ gồm doc đúng khóa hoặc doc chung (không khóa)
    retrieved_correct = ["doc_fpt_k18_0100", "doc_fpt_k19_0200", "doc_general_policy"]
    assert compute_wrong_cohort_rate(retrieved_correct, expected_cohorts, k=5) == 0.0

    # expected_cohorts rỗng / None -> không tính wrong cohort
    assert compute_wrong_cohort_rate(retrieved_with_wrong, expected_cohorts=None, k=5) == 0.0
