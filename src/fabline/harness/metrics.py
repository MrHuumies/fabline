"""Regression metrics used by the M1 benchmark."""

from __future__ import annotations

import numpy as np


def _flatten(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=np.float64).reshape(-1)


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    truth = _flatten(y_true)
    pred = _flatten(y_pred)
    if truth.shape != pred.shape:
        raise ValueError(f"shape mismatch: {truth.shape} vs {pred.shape}")
    if truth.size == 0:
        raise ValueError("empty metric input")

    errors = pred - truth
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors * errors)))
    ss_res = float(np.sum(errors * errors))
    centered = truth - float(np.mean(truth))
    ss_tot = float(np.sum(centered * centered))
    r2 = 0.0 if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    return {"mae": mae, "rmse": rmse, "r2": r2}


def classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    truth = np.asarray(y_true).reshape(-1)
    pred = np.asarray(y_pred).reshape(-1)
    if truth.shape != pred.shape:
        raise ValueError(f"shape mismatch: {truth.shape} vs {pred.shape}")
    if truth.size == 0:
        raise ValueError("empty metric input")

    accuracy = float(np.mean(truth == pred))
    true_labels = sorted(set(truth.tolist()))
    recalls: list[float] = []
    f1s: list[float] = []
    for label in true_labels:
        tp = float(np.sum((truth == label) & (pred == label)))
        fn = float(np.sum((truth == label) & (pred != label)))
        fp = float(np.sum((truth != label) & (pred == label)))
        recall = tp / (tp + fn) if tp + fn else 0.0
        precision = tp / (tp + fp) if tp + fp else 0.0
        f1 = (
            2.0 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        recalls.append(recall)
        f1s.append(f1)
    return {
        "accuracy": accuracy,
        "balanced_accuracy": float(np.mean(recalls)) if recalls else 0.0,
        "macro_f1": float(np.mean(f1s)) if f1s else 0.0,
    }


def multi_output_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    truth = np.asarray(y_true, dtype=np.float64)
    pred = np.asarray(y_pred, dtype=np.float64)
    if truth.shape != pred.shape:
        raise ValueError(f"shape mismatch: {truth.shape} vs {pred.shape}")
    if truth.ndim == 1:
        truth = truth[:, None]
        pred = pred[:, None]
    if truth.size == 0:
        raise ValueError("empty metric input")

    errors = pred - truth
    mse = float(np.mean(errors * errors))
    mae = float(np.mean(np.abs(errors)))
    norms = np.linalg.norm(truth, axis=1) * np.linalg.norm(pred, axis=1)
    dots = np.sum(truth * pred, axis=1)
    cosine = np.ones_like(dots)
    nonzero = norms > 0
    cosine[nonzero] = dots[nonzero] / norms[nonzero]
    return {
        "mse": mse,
        "mae": mae,
        "cosine": float(np.mean(cosine)),
    }


def calibration_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    *,
    n_bins: int = 10,
) -> dict[str, float]:
    """Binary calibration metrics for predicted probabilities.

    Returns Brier score, negative log-likelihood, expected calibration error
    (ECE), mean confidence, and threshold accuracy. Probabilities are clipped
    away from 0 and 1 for the log loss.
    """

    truth = _flatten(y_true)
    probs = _flatten(probabilities)
    if truth.shape != probs.shape:
        raise ValueError(f"shape mismatch: {truth.shape} vs {probs.shape}")
    if truth.size == 0:
        raise ValueError("empty metric input")
    if not np.all((truth == 0) | (truth == 1)):
        raise ValueError("calibration metrics require binary labels")
    if np.any(probs < 0.0) or np.any(probs > 1.0):
        raise ValueError("probabilities must be in [0, 1]")
    if n_bins <= 0:
        raise ValueError("n_bins must be positive")

    clipped = np.clip(probs, 1e-12, 1.0 - 1e-12)
    brier = float(np.mean((probs - truth) ** 2))
    nll = float(
        -np.mean(truth * np.log(clipped) + (1.0 - truth) * np.log(1.0 - clipped))
    )
    confidence = np.maximum(probs, 1.0 - probs)
    predicted = (probs >= 0.5).astype(np.float64)
    correct = (predicted == truth).astype(np.float64)
    ece = 0.0
    for index in range(n_bins):
        low = index / n_bins
        high = (index + 1) / n_bins
        if index == n_bins - 1:
            mask = (confidence >= low) & (confidence <= high)
        else:
            mask = (confidence >= low) & (confidence < high)
        count = int(np.sum(mask))
        if count:
            ece += (count / truth.size) * abs(
                float(np.mean(correct[mask])) - float(np.mean(confidence[mask]))
            )
    return {
        "brier": brier,
        "nll": nll,
        "ece": float(ece),
        "mean_confidence": float(np.mean(confidence)),
        "accuracy": float(np.mean(correct)),
    }
