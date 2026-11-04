import pytest
from FPTUniQA.evaluation.statistical_testing import paired_bootstrap_test, BootstrapTestResult


def test_paired_bootstrap_identical():
    """Hai tập điểm giống hệt nhau -> delta_mean = 0, p_value = 1.0, không có ý nghĩa thống kê."""
    a = [0.8, 0.6, 0.9, 0.7, 0.5]
    b = [0.8, 0.6, 0.9, 0.7, 0.5]
    res = paired_bootstrap_test(a, b, n_bootstraps=500, random_state=42)
    assert res.delta_mean == 0.0
    assert res.ci_low == 0.0
    assert res.ci_high == 0.0
    assert res.p_value == 1.0
    assert not res.significant_at_0_05
    assert res.n_pairs == 5


def test_paired_bootstrap_significant_improvement():
    """A vượt trội rõ rệt so với B -> delta_mean > 0, ci_low > 0, p_value < 0.05."""
    a = [1.0, 1.0, 0.9, 1.0, 0.8, 0.9, 1.0, 0.9, 1.0, 0.9] * 5  # 50 samples
    b = [0.4, 0.5, 0.3, 0.4, 0.5, 0.4, 0.3, 0.5, 0.4, 0.3] * 5
    res = paired_bootstrap_test(a, b, n_bootstraps=1000, random_state=42)
    assert res.delta_mean > 0.4
    assert res.ci_low > 0.0
    assert res.p_value < 0.01
    assert res.significant_at_0_05 is True


def test_paired_bootstrap_unpack():
    """Kiểm tra unpack tuple (delta, ci_l, ci_h, p)."""
    a = [0.7, 0.8, 0.9]
    b = [0.6, 0.7, 0.8]
    delta, ci_l, ci_h, p = paired_bootstrap_test(a, b, n_bootstraps=100, random_state=42)
    assert delta > 0


def test_paired_bootstrap_length_mismatch():
    """Báo lỗi khi độ dài hai danh sách không khớp."""
    with pytest.raises(ValueError):
        paired_bootstrap_test([1.0, 0.5], [1.0])
