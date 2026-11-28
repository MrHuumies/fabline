"""Public sequence baselines: GRU and a small Transformer.

The models accept ``(N, T, F)`` windows and predict one scalar per window. They
are original FABLINE implementations using PyTorch core only.
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


def _validate_sequences(sequences: np.ndarray) -> np.ndarray:
    values = np.asarray(sequences, dtype=np.float32)
    if values.ndim != 3:
        raise ValueError("sequence input must be a 3-D (N, T, F) array")
    if values.shape[1] <= 0 or values.shape[2] <= 0:
        raise ValueError("sequence dimensions must be positive")
    return values


class GRURegressor:
    """A one-layer GRU regressor over fixed-length windows."""

    name = "gru"

    def __init__(
        self,
        config: TorchTrainConfig | None = None,
        *,
        name: str = "gru",
    ) -> None:
        self.config = config or TorchTrainConfig()
        self.name = name
        self.model: Any | None = None
        self.mean: np.ndarray | None = None
        self.scale: np.ndarray | None = None
        self.report: TorchTrainReport | None = None
        self.input_shape: tuple[int, int] | None = None

    def _build(self, input_dim: int) -> Any:
        torch = _torch()
        hidden = self.config.hidden
        dropout = self.config.dropout

        class _GRU(torch.nn.Module):  # type: ignore[name-defined,misc]
            def __init__(self) -> None:
                super().__init__()
                self.gru = torch.nn.GRU(
                    input_size=input_dim,
                    hidden_size=hidden,
                    batch_first=True,
                )
                self.head = mlp_head(torch, hidden, hidden, dropout)

            def forward(self, values: Any) -> Any:
                output, _ = self.gru(values)
                return self.head(output[:, -1])

        return _GRU()

    def fit(self, sequences: np.ndarray, targets: np.ndarray) -> GRURegressor:
        values = _validate_sequences(sequences)
        self.input_shape = (values.shape[1], values.shape[2])
        _torch().manual_seed(self.config.seed)
        self.model = self._build(values.shape[2])
        self.mean, self.scale, self.report = fit_regressor(
            self.model, values, targets, self.config
        )
        return self

    def predict(self, sequences: np.ndarray) -> np.ndarray:
        if self.model is None or self.mean is None or self.scale is None:
            raise RuntimeError("GRURegressor is not fitted")
        values = _validate_sequences(sequences)
        if self.input_shape is not None and values.shape[1:] != self.input_shape:
            raise ValueError(
                f"expected sequence shape {self.input_shape}, got {values.shape[1:]}"
            )
        return predict_regressor(self.model, values, self.mean, self.scale)


class TransformerRegressor:
    """A small Transformer encoder regressor over fixed-length windows."""

    name = "transformer"

    def __init__(
        self,
        config: TorchTrainConfig | None = None,
        *,
        layers: int = 2,
        heads: int = 4,
        max_length: int = 128,
        name: str = "transformer",
    ) -> None:
        if layers <= 0:
            raise ValueError("layers must be positive")
        if heads <= 0:
            raise ValueError("heads must be positive")
        if max_length <= 0:
            raise ValueError("max_length must be positive")
        self.config = config or TorchTrainConfig()
        if self.config.hidden % heads != 0:
            raise ValueError("hidden must be divisible by heads")
        self.layers = layers
        self.heads = heads
        self.max_length = max_length
        self.name = name
        self.model: Any | None = None
        self.mean: np.ndarray | None = None
        self.scale: np.ndarray | None = None
        self.report: TorchTrainReport | None = None
        self.input_shape: tuple[int, int] | None = None

    def _build(self, input_dim: int) -> Any:
        torch = _torch()
        hidden = self.config.hidden
        dropout = self.config.dropout
        layers = self.layers
        heads = self.heads
        max_length = self.max_length

        class _Transformer(torch.nn.Module):  # type: ignore[name-defined,misc]
            def __init__(self) -> None:
                super().__init__()
                self.input = torch.nn.Linear(input_dim, hidden)
                self.position = torch.nn.Parameter(
                    torch.zeros(1, max_length, hidden)
                )
                encoder_layer = torch.nn.TransformerEncoderLayer(
                    d_model=hidden,
                    nhead=heads,
                    dim_feedforward=hidden * 2,
                    dropout=dropout,
                    batch_first=True,
                )
                self.encoder = torch.nn.TransformerEncoder(
                    encoder_layer, num_layers=layers
                )
                self.head = mlp_head(torch, hidden, hidden, dropout)

            def forward(self, values: Any) -> Any:
                length = values.shape[1]
                if length > max_length:
                    raise ValueError(
                        f"sequence length {length} exceeds max_length {max_length}"
                    )
                hidden_state = self.input(values) + self.position[:, :length]
                encoded = self.encoder(hidden_state)
                return self.head(encoded.mean(dim=1))

        return _Transformer()

    def fit(
        self, sequences: np.ndarray, targets: np.ndarray
    ) -> TransformerRegressor:
        values = _validate_sequences(sequences)
        if values.shape[1] > self.max_length:
            raise ValueError(
                f"sequence length {values.shape[1]} exceeds max_length {self.max_length}"
            )
        self.input_shape = (values.shape[1], values.shape[2])
        self.model = self._build(values.shape[2])
        self.mean, self.scale, self.report = fit_regressor(
            self.model, values, targets, self.config
        )
        return self

    def predict(self, sequences: np.ndarray) -> np.ndarray:
        if self.model is None or self.mean is None or self.scale is None:
            raise RuntimeError("TransformerRegressor is not fitted")
        values = _validate_sequences(sequences)
        if self.input_shape is not None and values.shape[1:] != self.input_shape:
            raise ValueError(
                f"expected sequence shape {self.input_shape}, got {values.shape[1:]}"
            )
        return predict_regressor(self.model, values, self.mean, self.scale)
