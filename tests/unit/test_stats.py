from __future__ import annotations

import numpy as np

from fabline.harness.stats import (
    bootstrap_cluster_mean_ci,
    bootstrap_mean_ci,
)


def test_cluster_bootstrap_resamples_whole_clusters() -> None:
    rng = np.random.default_rng(7)
    groups = np.repeat(np.arange(12), 5)
    values = rng.normal(loc=groups * 0.1, scale=1.0, size=groups.size)
    low, high = bootstrap_cluster_mean_ci(values, groups)
    assert np.isfinite(low)
    assert np.isfinite(high)
    assert low <= float(np.mean(values)) <= high
    assert low < high


def test_cluster_bootstrap_single_cluster_is_degenerate() -> None:
    values = [1.0, 2.0, 3.0]
    groups = [5, 5, 5]
    assert bootstrap_cluster_mean_ci(values, groups) == (2.0, 2.0)


def test_mean_bootstrap_brackets_mean() -> None:
    values = [0.0, 1.0, 2.0, 3.0, 4.0]
    low, high = bootstrap_mean_ci(values)
    assert low <= float(np.mean(values)) <= high
    assert low < high
