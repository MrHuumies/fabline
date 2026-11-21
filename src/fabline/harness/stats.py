"""Bootstrap confidence intervals for small benchmark suites."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def bootstrap_metric_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    *,
    n_boot: int = 200,
    seed: int = 0,
) -> tuple[float, float]:
    truth = np.asarray(y_true)
    pred = np.asarray(y_pred)
    if len(truth) != len(pred):
        raise ValueError("y_true and y_pred must have the same length")
    if len(truth) == 0:
        return (float("nan"), float("nan"))

    rng = np.random.default_rng(seed)
    values = np.empty(n_boot, dtype=np.float64)
    for index in range(n_boot):
        sample = rng.integers(0, len(truth), size=len(truth))
        values[index] = metric(truth[sample], pred[sample])
    low, high = np.percentile(values, [2.5, 97.5])
    return (float(low), float(high))


def bootstrap_mean_ci(
    values: list[float] | np.ndarray,
    *,
    n_boot: int = 500,
    seed: int = 0,
) -> tuple[float, float]:
    data = np.asarray(values, dtype=np.float64)
    if data.size == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot, dtype=np.float64)
    for index in range(n_boot):
        sample = rng.integers(0, len(data), size=len(data))
        means[index] = float(np.mean(data[sample]))
    low, high = np.percentile(means, [2.5, 97.5])
    return (float(low), float(high))
