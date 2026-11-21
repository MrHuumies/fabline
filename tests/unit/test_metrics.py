from __future__ import annotations

import math

import numpy as np
import pytest

from fabline.harness.metrics import regression_metrics


def test_perfect_prediction() -> None:
    metrics = regression_metrics(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0]))
    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0
    assert metrics["r2"] == 1.0


def test_known_error() -> None:
    metrics = regression_metrics(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 4.0]))
    assert metrics["mae"] == pytest.approx(1.0 / 3.0)
    assert metrics["rmse"] == pytest.approx(math.sqrt(1.0 / 3.0))
    assert metrics["r2"] == pytest.approx(0.5)


def test_constant_truth_has_zero_r2() -> None:
    metrics = regression_metrics(np.array([2.0, 2.0]), np.array([1.0, 3.0]))
    assert metrics["r2"] == 0.0


def test_shape_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        regression_metrics(np.array([1.0]), np.array([1.0, 2.0]))
