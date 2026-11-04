import pytest
from FPTUniQA.evaluation.retrieval_metrics import (
    compute_recall_at_k,
    compute_recall_at_k_equivalent,
    compute_wrong_cohort_rate,
)


def test_equivalent_recall():
    gold = {"doc_fpt_k20_0001"}
    equiv = [["doc_fpt_k20_0001", "doc_fpt_k18_0001", "doc_fpt_k17_0001"]]

    # Trường hợp 1: Hit đúng doc ID gốc
    retrieved_exact = ["doc_fpt_k20_0001", "other_1", "other_2"]
    assert compute_recall_at_k(retrieved_exact, gold, k=5) == 1.0
    assert compute_recall_at_k_equivalent(retrieved_exact, gold, equiv, k=5) == 1.0

    # Trường hợp 2: Hit doc tương đương (K18 thay vì K20)
    retrieved_equiv = ["doc_fpt_k18_0001", "other_1", "other_2"]
    # Theo doc ID truyền thống: trượt (0.0)
    assert compute_recall_at_k(retrieved_equiv, gold, k=5) == 0.0
    # Theo nhóm tương đương: trúng (1.0)
    assert compute_recall_at_k_equivalent(retrieved_equiv, gold, equiv, k=5) == 1.0

    # Trường hợp 3: Trượt cả doc gốc lẫn doc tương đương
    retrieved_miss = ["doc_other_9999", "other_1", "other_2"]
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

    # expected_cohorts rỗng / None -> trả về None để loại khỏi mẫu số (chuẩn hóa học thuật)
    assert compute_wrong_cohort_rate(retrieved_with_wrong, expected_cohorts=None, k=5) is None
