"""Shared training utilities for the optional Torch baseline models.

These utilities are intentionally small and original. They standardize the
regression target, use a deterministic seed, and report a cost fingerprint so a
benchmark result is comparable at a declared budget.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np

Features = np.ndarray | tuple[np.ndarray, ...]


@dataclass(frozen=True)
class TorchTrainConfig:
    """A fixed training budget for a public baseline."""

    epochs: int = 50
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 0.0
    seed: int = 0
    hidden: int = 32
    dropout: float = 0.0

    def __post_init__(self) -> None:
        if self.epochs <= 0:
            raise ValueError("epochs must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.learning_rate <= 0.0:
            raise ValueError("learning_rate must be positive")
        if self.weight_decay < 0.0:
            raise ValueError("weight_decay must be non-negative")
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        if self.hidden <= 0:
            raise ValueError("hidden must be positive")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")


@dataclass(frozen=True)
class TorchTrainReport:
    """Cost and optimization fingerprint for one fitted model."""

    epochs: int
    batch_size: int
    samples: int
    parameters: int
    train_seconds: float
    final_loss: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "samples": self.samples,
            "parameters": self.parameters,
            "train_seconds": self.train_seconds,
            "final_loss": self.final_loss,
        }


@lru_cache(maxsize=1)
def _torch() -> Any:
    try:
        import torch  # type: ignore[import-not-found,unused-ignore]

        torch.set_num_threads(1)
        return torch
    except ImportError as exc:  # pragma: no cover - optional path
        raise RuntimeError(
            "public baseline models require the optional train extra: "
            "uv pip install --python .venv/Scripts/python.exe -e '.[train]'"
        ) from exc


def torch_available() -> bool:
    """Return whether the optional Torch dependency can be imported."""

    try:
        _torch()
    except RuntimeError:
        return False
    return True


def require_torch() -> Any:
    """Return the torch module or raise a clear optional-dependency error."""

    return _torch()


def _seed_everything(torch: Any, seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():  # pragma: no cover - CPU baseline
        torch.cuda.manual_seed_all(seed)


def _as_float_tensor(torch: Any, values: np.ndarray) -> Any:
    return torch.as_tensor(np.asarray(values, dtype=np.float32))


def _feature_count(features: Features) -> int:
    if isinstance(features, tuple):
        return len(features[0]) if features else 0
    return len(features)


def _take(features: Features, indices: Any) -> Features:
    if isinstance(features, tuple):
        return tuple(np.asarray(values[indices]) for values in features)
    return np.asarray(features[indices])


def _forward(model: Any, batch: Features, torch: Any) -> Any:
    if isinstance(batch, tuple):
        tensors = tuple(_as_float_tensor(torch, values) for values in batch)
        return model(*tensors)
    return model(_as_float_tensor(torch, batch))


def fit_regressor(
    model: Any,
    features: Features,
    targets: np.ndarray,
    config: TorchTrainConfig,
) -> tuple[np.ndarray, np.ndarray, TorchTrainReport]:
    """Fit a scalar regressor and return the target standardizer plus report.

    ``features`` is either one array for single-input models or a tuple of
    arrays for structured models (for example entity features, mask, and
    adjacency). The caller owns the model.
    """

    torch = _torch()
    _seed_everything(torch, config.seed)

    y = np.asarray(targets, dtype=np.float32).reshape(-1)
    count = _feature_count(features)
    if len(y) != count:
        raise ValueError("features and targets must have the same length")
    if len(y) == 0:
        raise ValueError("cannot fit an empty dataset")

    mean = float(y.mean())
    scale = float(y.std())
    if scale < 1e-6:
        scale = 1.0

    y_tensor = _as_float_tensor(torch, (y - mean) / scale)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    loss_fn = torch.nn.functional.mse_loss
    start = time.perf_counter()
    final_loss = float("nan")

    for _ in range(config.epochs):
        permutation = torch.randperm(count)
        epoch_loss = 0.0
        batches = 0
        for offset in range(0, count, config.batch_size):
            batch = permutation[offset : offset + config.batch_size]
            indices = batch.cpu().numpy()
            prediction = _forward(model, _take(features, indices), torch).reshape(-1)
            loss = loss_fn(prediction, y_tensor[batch])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += float(loss.detach().item())
            batches += 1
        final_loss = epoch_loss / max(1, batches)

    seconds = time.perf_counter() - start
    parameters = int(sum(parameter.numel() for parameter in model.parameters()))
    report = TorchTrainReport(
        epochs=config.epochs,
        batch_size=config.batch_size,
        samples=int(len(y)),
        parameters=parameters,
        train_seconds=seconds,
        final_loss=final_loss,
    )
    return np.asarray([mean], dtype=np.float64), np.asarray(
        [scale], dtype=np.float64
    ), report


def predict_regressor(
    model: Any,
    features: Features,
    mean: np.ndarray,
    scale: np.ndarray,
    *,
    batch_size: int = 256,
) -> np.ndarray:
    """Predict in the original target scale."""

    torch = _torch()
    count = _feature_count(features)
    outputs: list[np.ndarray] = []
    with torch.no_grad():
        for offset in range(0, count, batch_size):
            indices = np.arange(offset, min(offset + batch_size, count))
            prediction = _forward(
                model, _take(features, indices), torch
            ).reshape(-1)
            outputs.append(
                np.asarray(prediction.cpu().numpy(), dtype=np.float64)
            )
    if not outputs:
        return np.empty(0, dtype=np.float64)
    normalized = np.concatenate(outputs)
    return normalized * float(scale[0]) + float(mean[0])


def mlp_head(torch: Any, input_dim: int, hidden: int, dropout: float) -> Any:
    """A small regression head shared by the structured models."""

    layers: list[Any] = [
        torch.nn.Linear(input_dim, hidden),
        torch.nn.ReLU(),
    ]
    if dropout > 0.0:
        layers.append(torch.nn.Dropout(dropout))
    layers.append(torch.nn.Linear(hidden, 1))
    return torch.nn.Sequential(*layers)
