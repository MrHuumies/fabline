"""Baselines for the M1 throughput task."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

import numpy as np

from .metrics import (
    calibration_metrics,
    classification_metrics,
    multi_output_metrics,
    regression_metrics,
)
from .stats import bootstrap_metric_ci


class Baseline(Protocol):
    name: str

    def fit(self, X: np.ndarray, y: np.ndarray) -> None: ...

    def predict(self, X: np.ndarray) -> np.ndarray: ...


class ProbabilisticBaseline(Protocol):
    name: str

    def fit(self, X: np.ndarray, y: np.ndarray) -> None: ...

    def predict_proba(self, X: np.ndarray) -> np.ndarray: ...


class MeanBaseline:
    name = "mean"

    def __init__(self) -> None:
        self.value = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.value = float(np.mean(y))

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(len(X), self.value, dtype=np.float64)


class PersistenceBaseline:
    """Predict the next window from the last observed window.

    Uses the ``score_last_window_norm`` feature from the vector observation. It
    is a scripted baseline, not a learned model.
    """

    name = "persistence"

    def __init__(self, feature_names: tuple[str, ...] | None) -> None:
        if feature_names is None:
            raise ValueError("persistence baseline requires feature names")
        names = list(feature_names)
        if "score_last_window_norm" not in names:
            raise ValueError("persistence baseline requires score_last_window_norm")
        self.index = names.index("score_last_window_norm")
        self.scale = 1000.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        return None

    def predict(self, X: np.ndarray) -> np.ndarray:
        values = X[:, self.index].astype(np.float64) * self.scale
        return np.asarray(np.maximum(0.0, values), dtype=np.float64)


class GradientBoostingBaseline:
    name = "gbdt"

    def __init__(self) -> None:
        from sklearn.ensemble import HistGradientBoostingRegressor

        self.model = HistGradientBoostingRegressor(max_iter=200, random_state=0)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.asarray(self.model.predict(X), dtype=np.float64)


class MLPBaseline:
    name = "mlp"

    def __init__(self) -> None:
        from sklearn.neural_network import MLPRegressor

        self.model = MLPRegressor(
            hidden_layer_sizes=(64,),
            max_iter=500,
            random_state=0,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.asarray(self.model.predict(X), dtype=np.float64)


class MajorityBaseline:
    name = "majority"

    def __init__(self) -> None:
        self.label = 0

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        values, counts = np.unique(y, return_counts=True)
        self.label = values[int(np.argmax(counts))]

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(len(X), self.label)


class GradientBoostingClassifierBaseline:
    name = "gbdt"

    def __init__(self) -> None:
        from sklearn.ensemble import HistGradientBoostingClassifier

        self.model = HistGradientBoostingClassifier(max_iter=200, random_state=0)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.asarray(self.model.predict(X))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return np.asarray(self.model.predict_proba(X)[:, 1], dtype=np.float64)


class MLPClassifierBaseline:
    name = "mlp"

    def __init__(self) -> None:
        from sklearn.neural_network import MLPClassifier

        self.model = MLPClassifier(
            hidden_layer_sizes=(64,),
            max_iter=500,
            random_state=0,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.asarray(self.model.predict(X))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return np.asarray(self.model.predict_proba(X)[:, 1], dtype=np.float64)


class CopyBaseline:
    """Predict the current observation as the next observation."""

    name = "copy"

    def __init__(self) -> None:
        self.dim: int | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.dim = y.shape[1] if y.ndim > 1 else 1

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.dim is None:
            raise RuntimeError("baseline is not fitted")
        return np.asarray(X[:, : self.dim], dtype=np.float64)


class LinearBaseline:
    name = "linear"

    def __init__(self) -> None:
        self.coef: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        design = np.column_stack([np.ones(len(X)), X]).astype(np.float64)
        solution, *_ = np.linalg.lstsq(design, y.astype(np.float64), rcond=None)
        self.coef = solution

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.coef is None:
            raise RuntimeError("baseline is not fitted")
        design = np.column_stack([np.ones(len(X)), X]).astype(np.float64)
        return np.asarray(np.maximum(0.0, design @ self.coef), dtype=np.float64)


def _flatten_observations(X: np.ndarray) -> np.ndarray:
    return np.asarray(X).reshape(len(X), -1)


def evaluate_baselines(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: tuple[str, ...] | None,
    *,
    include_models: bool = False,
    with_ci: bool = False,
    X_extra: np.ndarray | None = None,
    y_extra: np.ndarray | None = None,
) -> dict[str, dict[str, object]]:
    X_train = _flatten_observations(X_train)
    X_val = _flatten_observations(X_val)
    X_test = _flatten_observations(X_test)
    if X_extra is not None:
        X_extra = _flatten_observations(X_extra)

    candidates: list[Baseline] = [MeanBaseline(), LinearBaseline()]
    if include_models:
        candidates.extend([GradientBoostingBaseline(), MLPBaseline()])
    skipped: dict[str, object] | None = None
    try:
        candidates.insert(1, PersistenceBaseline(feature_names))
    except ValueError as exc:
        skipped = {"skipped": str(exc)}

    results: dict[str, dict[str, object]] = {}
    for baseline in candidates:
        baseline.fit(X_train, y_train)
        val_pred = baseline.predict(X_val)
        test_pred = baseline.predict(X_test)
        result: dict[str, object] = {
            "val": regression_metrics(y_val, val_pred),
            "test": regression_metrics(y_test, test_pred),
        }
        cis: dict[str, object] = {}
        if with_ci:
            cis["val"] = _regression_ci(y_val, val_pred)
            cis["test"] = _regression_ci(y_test, test_pred)
        if X_extra is not None and y_extra is not None:
            extra_pred = baseline.predict(X_extra)
            result["shift"] = regression_metrics(y_extra, extra_pred)
            if with_ci:
                cis["shift"] = _regression_ci(y_extra, extra_pred)
        if cis:
            result["ci"] = cis
        results[baseline.name] = result
    if skipped is not None:
        results["persistence"] = skipped
    return results


def _regression_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, tuple[float, float]]:
    return {
        "mae": bootstrap_metric_ci(
            y_true,
            y_pred,
            lambda a, b: regression_metrics(a, b)["mae"],
        ),
        "r2": bootstrap_metric_ci(
            y_true,
            y_pred,
            lambda a, b: regression_metrics(a, b)["r2"],
        ),
    }


def _classification_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, tuple[float, float]]:
    return {
        "accuracy": bootstrap_metric_ci(
            y_true,
            y_pred,
            lambda a, b: classification_metrics(a, b)["accuracy"],
        ),
        "balanced_accuracy": bootstrap_metric_ci(
            y_true,
            y_pred,
            lambda a, b: classification_metrics(a, b)["balanced_accuracy"],
        ),
    }


def _multi_output_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, tuple[float, float]]:
    return {
        "mse": bootstrap_metric_ci(
            y_true,
            y_pred,
            lambda a, b: multi_output_metrics(a, b)["mse"],
        ),
        "cosine": bootstrap_metric_ci(
            y_true,
            y_pred,
            lambda a, b: multi_output_metrics(a, b)["cosine"],
        ),
    }


def evaluate_classification_baselines(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    *,
    with_ci: bool = False,
    X_extra: np.ndarray | None = None,
    y_extra: np.ndarray | None = None,
) -> dict[str, dict[str, object]]:
    X_train = _flatten_observations(X_train)
    X_val = _flatten_observations(X_val)
    X_test = _flatten_observations(X_test)
    if X_extra is not None:
        X_extra = _flatten_observations(X_extra)

    candidates: list[Baseline] = [
        MajorityBaseline(),
        GradientBoostingClassifierBaseline(),
        MLPClassifierBaseline(),
    ]
    results: dict[str, dict[str, object]] = {}
    for baseline in candidates:
        baseline.fit(X_train, y_train)
        val_pred = baseline.predict(X_val)
        test_pred = baseline.predict(X_test)
        result: dict[str, object] = {
            "val": classification_metrics(y_val, val_pred),
            "test": classification_metrics(y_test, test_pred),
        }
        cis: dict[str, object] = {}
        if with_ci:
            cis["val"] = _classification_ci(y_val, val_pred)
            cis["test"] = _classification_ci(y_test, test_pred)
        if X_extra is not None and y_extra is not None:
            extra_pred = baseline.predict(X_extra)
            result["shift"] = classification_metrics(y_extra, extra_pred)
            if with_ci:
                cis["shift"] = _classification_ci(y_extra, extra_pred)
        if cis:
            result["ci"] = cis
        results[baseline.name] = result
    return results


def _calibration_metric(
    name: str,
    n_bins: int,
) -> Callable[[np.ndarray, np.ndarray], float]:
    def score(truth: np.ndarray, probabilities: np.ndarray) -> float:
        return calibration_metrics(truth, probabilities, n_bins=n_bins)[name]

    return score


def evaluate_calibration_baselines(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    *,
    with_ci: bool = False,
    n_bins: int = 10,
) -> dict[str, dict[str, object]]:
    """Fit probabilistic classifiers and report calibration on the test split."""

    X_train = _flatten_observations(X_train)
    X_test = _flatten_observations(X_test)
    candidates: list[ProbabilisticBaseline] = [
        GradientBoostingClassifierBaseline(),
        MLPClassifierBaseline(),
    ]
    results: dict[str, dict[str, object]] = {}
    for baseline in candidates:
        baseline.fit(X_train, y_train)
        probabilities = baseline.predict_proba(X_test)
        result: dict[str, object] = {
            "test": calibration_metrics(y_test, probabilities, n_bins=n_bins)
        }
        if with_ci:
            result["ci"] = {
                key: list(
                    bootstrap_metric_ci(
                        y_test,
                        probabilities,
                        _calibration_metric(key, n_bins),
                    )
                )
                for key in ("brier", "nll", "ece")
            }
        results[baseline.name] = result
    return results


def evaluate_next_state_baselines(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    *,
    with_ci: bool = False,
    X_extra: np.ndarray | None = None,
    y_extra: np.ndarray | None = None,
) -> dict[str, dict[str, object]]:
    X_train = _flatten_observations(X_train)
    X_val = _flatten_observations(X_val)
    X_test = _flatten_observations(X_test)
    if X_extra is not None:
        X_extra = _flatten_observations(X_extra)

    candidates: list[Baseline] = [CopyBaseline(), LinearBaseline(), MLPBaseline()]
    results: dict[str, dict[str, object]] = {}
    for baseline in candidates:
        baseline.fit(X_train, y_train)
        val_pred = baseline.predict(X_val)
        test_pred = baseline.predict(X_test)
        result: dict[str, object] = {
            "val": multi_output_metrics(y_val, val_pred),
            "test": multi_output_metrics(y_test, test_pred),
        }
        cis: dict[str, object] = {}
        if with_ci:
            cis["val"] = _multi_output_ci(y_val, val_pred)
            cis["test"] = _multi_output_ci(y_test, test_pred)
        if X_extra is not None and y_extra is not None:
            extra_pred = baseline.predict(X_extra)
            result["shift"] = multi_output_metrics(y_extra, extra_pred)
            if with_ci:
                cis["shift"] = _multi_output_ci(y_extra, extra_pred)
        if cis:
            result["ci"] = cis
        results[baseline.name] = result
    return results
