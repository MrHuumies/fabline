"""A small public CNN baseline for grid observations.

The model is deliberately small and fully convolutional. It is an original
FABLINE implementation using PyTorch core only.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from fabline.harness.models.common import (
    TorchTrainConfig,
    TorchTrainReport,
    _torch,
    fit_regressor,
    mlp_head,
    predict_regressor,
)


class CNNRegressor:
    """A small CNN for ``(N, H, W, C)`` grid tensors.

    Set ``channels_last=False`` when the input is already ``(N, C, H, W)``.
    """

    name = "cnn"

    def __init__(
        self,
        config: TorchTrainConfig | None = None,
        *,
        channels_last: bool = True,
        name: str = "cnn",
    ) -> None:
        self.config = config or TorchTrainConfig()
        self.channels_last = channels_last
        self.name = name
        self.model: Any | None = None
        self.mean: np.ndarray | None = None
        self.scale: np.ndarray | None = None
        self.report: TorchTrainReport | None = None
        self.input_shape: tuple[int, ...] | None = None

    def _prepare(self, grids: np.ndarray) -> np.ndarray:
        values = np.asarray(grids, dtype=np.float32)
        if values.ndim != 4:
            raise ValueError("grid input must be a 4-D array")
        if self.channels_last:
            return np.transpose(values, (0, 3, 1, 2))
        return values

    def _build(self, channels: int) -> Any:
        torch = _torch()
        hidden = self.config.hidden
        return torch.nn.Sequential(
            torch.nn.Conv2d(channels, hidden, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.Conv2d(hidden, hidden, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.AdaptiveAvgPool2d((1, 1)),
            torch.nn.Flatten(),
            mlp_head(torch, hidden, hidden, self.config.dropout),
        )

    def fit(self, grids: np.ndarray, targets: np.ndarray) -> CNNRegressor:
        _torch().manual_seed(self.config.seed)
        prepared = self._prepare(grids)
        self.input_shape = tuple(prepared.shape[1:])
        _torch().manual_seed(self.config.seed)
        self.model = self._build(prepared.shape[1])
        self.mean, self.scale, self.report = fit_regressor(
            self.model, prepared, targets, self.config
        )
        return self

    def predict(self, grids: np.ndarray) -> np.ndarray:
        if self.model is None or self.mean is None or self.scale is None:
            raise RuntimeError("CNNRegressor is not fitted")
        prepared = self._prepare(grids)
        if self.input_shape is not None and prepared.shape[1:] != self.input_shape:
            raise ValueError(
                f"expected grid shape {self.input_shape}, got {prepared.shape[1:]}"
            )
        return predict_regressor(self.model, prepared, self.mean, self.scale)
