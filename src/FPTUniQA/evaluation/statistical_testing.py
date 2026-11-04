"""Module kiểm định thống kê học thuật (Statistical Hypothesis Testing) cho Ablation Study.
Cung cấp phương pháp Paired Bootstrap Test & Confidence Interval (95% CI) theo chuẩn thực nghiệm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union
import numpy as np


@dataclass
class BootstrapTestResult:
    """Kết quả kiểm định Paired Bootstrap Test."""
    delta_mean: float
    ci_low: float
    ci_high: float
    p_value: float
    significant_at_0_05: bool
    n_pairs: int
    bootstrap_resamples: int
    random_seed: int

    def __iter__(self) -> Iterator[Union[float, bool, int]]:
        """Hỗ trợ unpack tuple: (delta_mean, ci_low, ci_high, p_value)."""
        yield self.delta_mean
        yield self.ci_low
        yield self.ci_high
        yield self.p_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delta_mean": round(self.delta_mean, 4),
            "ci_low": round(self.ci_low, 4),
            "ci_high": round(self.ci_high, 4),
            "p_value": round(self.p_value, 4),
            "significant_at_0_05": self.significant_at_0_05,
            "n_pairs": self.n_pairs,
            "bootstrap_resamples": self.bootstrap_resamples,
            "random_seed": self.random_seed,
        }


def paired_bootstrap_test(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    n_bootstraps: int = 1000,
    ci: float = 0.95,
    random_state: int = 42,
) -> BootstrapTestResult:
    """Thực hiện kiểm định Paired Bootstrap Test giữa hai cấu hình trên cùng một tập truy vấn.

    Args:
        scores_a: Điểm số của cấu hình thử nghiệm A (VD: C4-soft).
        scores_b: Điểm số của cấu hình đối sánh B (VD: C4-hard).
        n_bootstraps: Số lần lấy mẫu bootstrap (mặc định 1000).
        ci: Độ tin cậy (mặc định 0.95 cho CI 95%).
        random_state: Seed ngẫu nhiên để tái lập tuyệt đối kết quả.

    Returns:
        BootstrapTestResult chứa delta_mean, ci_low, ci_high, p_value, significant_at_0_05.
    """
    if len(scores_a) != len(scores_b):
        raise ValueError(
            f"Độ dài scores_a ({len(scores_a)}) và scores_b ({len(scores_b)}) phải bằng nhau để paired test."
        )

    n = len(scores_a)
    if n == 0:
        raise ValueError("Tập dữ liệu điểm số không được rỗng.")

    arr_a = np.asarray(scores_a, dtype=np.float64)
    arr_b = np.asarray(scores_b, dtype=np.float64)

    # Hiệu số thực tế theo cặp: delta_i = a_i - b_i
    diffs = arr_a - arr_b
    delta_mean = float(np.mean(diffs))

    # Nếu tất cả các cặp hoàn toàn giống hệt nhau (delta_i == 0 với mọi i)
    if np.all(diffs == 0.0):
        return BootstrapTestResult(
            delta_mean=0.0,
            ci_low=0.0,
            ci_high=0.0,
            p_value=1.0,
            significant_at_0_05=False,
            n_pairs=n,
            bootstrap_resamples=n_bootstraps,
            random_seed=random_state,
        )

    rng = np.random.RandomState(random_state)
    boot_diff_means = np.empty(n_bootstraps, dtype=np.float64)

    # Lấy mẫu có hoàn lại theo chỉ số câu hỏi (resample pairs)
    for i in range(n_bootstraps):
        indices = rng.randint(0, n, size=n)
        boot_diff_means[i] = np.mean(diffs[indices])

    # Tính khoảng tin cậy hai phía Percentile Bootstrap CI
    alpha_half = (1.0 - ci) / 2.0
    ci_low = float(np.percentile(boot_diff_means, alpha_half * 100.0))
    ci_high = float(np.percentile(boot_diff_means, (1.0 - alpha_half) * 100.0))

    # Kiểm định giả thuyết hai phía H0: delta = 0
    # Phân phối bootstrap dịch chuyển tâm về H0: centered_boot = boot_diff_means - delta_mean
    centered_boot = boot_diff_means - delta_mean
    abs_delta = abs(delta_mean)
    # Tỷ lệ các mẫu bootstrap có độ lệch lớn hơn hoặc bằng độ lệch quan sát
    p_val = float(np.mean(np.abs(centered_boot) >= abs_delta))
    p_val = min(1.0, max(0.0, p_val))

    significant = bool(p_val < (1.0 - ci))

    return BootstrapTestResult(
        delta_mean=delta_mean,
        ci_low=ci_low,
        ci_high=ci_high,
        p_value=p_val,
        significant_at_0_05=significant,
        n_pairs=n,
        bootstrap_resamples=n_bootstraps,
        random_seed=random_state,
    )
