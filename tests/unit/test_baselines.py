from __future__ import annotations

import numpy as np

from fabline.harness.baselines import (
    LinearBaseline,
    MeanBaseline,
    PersistenceBaseline,
    evaluate_baselines,
)
from fabline.obs.vector import FEATURES


def test_mean_baseline() -> None:
    baseline = MeanBaseline()
    baseline.fit(np.zeros((3, 2)), np.array([1.0, 2.0, 3.0]))
    assert np.allclose(baseline.predict(np.zeros((2, 2))), 2.0)


def test_persistence_baseline() -> None:
    index = FEATURES.index("score_last_window_norm")
    X = np.zeros((2, len(FEATURES)))
    X[0, index] = 1.5
    X[1, index] = 0.25
    baseline = PersistenceBaseline(FEATURES)
    baseline.fit(X, np.zeros(2))
    assert np.allclose(baseline.predict(X), [1500.0, 250.0])


def test_linear_baseline() -> None:
    X = np.array([[0.0], [1.0], [2.0], [3.0]])
    y = 2.0 * X[:, 0] + 1.0
    baseline = LinearBaseline()
    baseline.fit(X, y)
    predictions = baseline.predict(np.array([[4.0], [5.0]]))
    assert np.allclose(predictions, [9.0, 11.0], atol=1e-8)


def test_evaluate_baselines() -> None:
    index = FEATURES.index("score_last_window_norm")
    X = np.zeros((6, len(FEATURES)))
    y = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0])
    X[:, index] = y / 1000.0
    results = evaluate_baselines(
        X[:3],
        y[:3],
        X[3:5],
        y[3:5],
        X[5:],
        y[5:],
        FEATURES,
    )
    assert set(results) == {"mean", "persistence", "linear"}
    assert "val" in results["mean"]
    assert "test" in results["linear"]
