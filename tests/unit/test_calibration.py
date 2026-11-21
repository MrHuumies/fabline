from __future__ import annotations

import numpy as np
import pytest

from fabline.harness.baselines import evaluate_calibration_baselines
from fabline.harness.metrics import calibration_metrics


def test_calibration_metrics_well_calibrated() -> None:
    truth = np.array([0, 0, 1, 1], dtype=np.float64)
    probs = np.array([0.01, 0.02, 0.98, 0.99], dtype=np.float64)
    metrics = calibration_metrics(truth, probs, n_bins=10)
    assert 0.0 <= metrics["brier"] < 0.01
    assert 0.0 <= metrics["nll"] < 0.05
    assert 0.0 <= metrics["ece"] < 0.02
    assert metrics["accuracy"] == 1.0


def test_calibration_metrics_overconfident_wrong() -> None:
    truth = np.array([0, 1], dtype=np.float64)
    probs = np.array([0.9, 0.9], dtype=np.float64)
    metrics = calibration_metrics(truth, probs, n_bins=10)
    assert metrics["brier"] == pytest.approx(0.41)
    assert metrics["ece"] == pytest.approx(0.4)
    assert metrics["accuracy"] == 0.5


def test_calibration_metrics_validation() -> None:
    with pytest.raises(ValueError):
        calibration_metrics(np.array([0, 2]), np.array([0.1, 0.2]))
    with pytest.raises(ValueError):
        calibration_metrics(np.array([0, 1]), np.array([-0.1, 1.1]))
    with pytest.raises(ValueError):
        calibration_metrics(np.array([0, 1]), np.array([0.1, 0.2]), n_bins=0)


def test_evaluate_calibration_baselines() -> None:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(120, 4))
    truth = (X[:, 0] + 0.5 * X[:, 1] > 0).astype(np.float64)
    results = evaluate_calibration_baselines(
        X[:90],
        truth[:90],
        X[90:],
        truth[90:],
        with_ci=True,
    )
    assert set(results) == {"gbdt", "mlp"}
    for payload in results.values():
        metrics = payload["test"]
        assert 0.0 <= metrics["brier"] <= 1.0
        assert 0.0 <= metrics["ece"] <= 1.0
        assert metrics["nll"] >= 0.0
        assert set(payload["ci"]) == {"brier", "nll", "ece"}
