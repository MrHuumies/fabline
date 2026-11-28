"""A small public message-passing baseline for entity graphs.

The model uses dense padded graphs, so it does not require PyTorch Geometric or
any other graph library. It is an original FABLINE implementation.
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


class MPNNRegressor:
    """A residual message-passing network over padded entity graphs.

    Inputs are ``(N, M, F)`` entity features, ``(N, M)`` masks, and
    ``(N, M, M)`` adjacency matrices. The output is one scalar per graph.
    """

    name = "mpnn"

    def __init__(
        self,
        config: TorchTrainConfig | None = None,
        *,
        layers: int = 2,
        name: str = "mpnn",
    ) -> None:
        if layers <= 0:
            raise ValueError("layers must be positive")
        self.config = config or TorchTrainConfig()
        self.layers = layers
        self.name = name
        self.model: Any | None = None
        self.mean: np.ndarray | None = None
        self.scale: np.ndarray | None = None
        self.report: TorchTrainReport | None = None
        self.input_shape: tuple[int, ...] | None = None

    @staticmethod
    def _validate(
        features: np.ndarray,
        mask: np.ndarray,
        adjacency: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        values = np.asarray(features, dtype=np.float32)
        mask_values = np.asarray(mask, dtype=np.float32)
        adjacency_values = np.asarray(adjacency, dtype=np.float32)
        if values.ndim != 3 or mask_values.ndim != 2 or adjacency_values.ndim != 3:
            raise ValueError("expected (N,M,F), (N,M), and (N,M,M) arrays")
        if values.shape[:2] != mask_values.shape:
            raise ValueError("entity features and mask must agree on (N, M)")
        if adjacency_values.shape != (values.shape[0], values.shape[1], values.shape[1]):
            raise ValueError("adjacency must be (N, M, M)")
        return values, mask_values, adjacency_values

    def _build(self, input_dim: int) -> Any:
        torch = _torch()
        hidden = self.config.hidden
        dropout = self.config.dropout
        layer_count = self.layers

        class _MPNN(torch.nn.Module):  # type: ignore[name-defined,misc]
            def __init__(self) -> None:
                super().__init__()
                self.input = torch.nn.Linear(input_dim, hidden)
                self.layers = torch.nn.ModuleList(
                    [
                        torch.nn.Linear(hidden * 2, hidden)
                        for _ in range(layer_count)
                    ]
                )
                self.head = mlp_head(torch, hidden * 2, hidden, dropout)

            def forward(
                self,
                features: Any,
                mask: Any,
                adjacency: Any,
            ) -> Any:
                node_mask = mask.unsqueeze(-1).float()
                hidden_state = torch.relu(self.input(features)) * node_mask
                identity = torch.eye(
                    adjacency.shape[-1], dtype=adjacency.dtype, device=adjacency.device
                )
                normalized = adjacency + identity
                degree = normalized.sum(dim=-1, keepdim=True).clamp_min(1.0)
                for layer in self.layers:
                    aggregate = torch.matmul(normalized / degree, hidden_state)
                    hidden_state = torch.relu(
                        layer(torch.cat([hidden_state, aggregate], dim=-1))
                    ) * node_mask
                denominator = node_mask.sum(dim=1).clamp_min(1.0)
                mean = (hidden_state * node_mask).sum(dim=1) / denominator
                padded = hidden_state.masked_fill(
                    node_mask <= 0.0, -1e9
                )
                maximum = padded.max(dim=1).values
                return self.head(torch.cat([mean, maximum], dim=-1))

        return _MPNN()

    def fit(
        self,
        features: np.ndarray,
        mask: np.ndarray,
        adjacency: np.ndarray,
        targets: np.ndarray,
    ) -> MPNNRegressor:
        values, mask_values, adjacency_values = self._validate(
            features, mask, adjacency
        )
        self.input_shape = (values.shape[1], values.shape[2])
        _torch().manual_seed(self.config.seed)
        self.model = self._build(values.shape[2])
        self.mean, self.scale, self.report = fit_regressor(
            self.model,
            (values, mask_values, adjacency_values),
            targets,
            self.config,
        )
        return self

    def predict(
        self,
        features: np.ndarray,
        mask: np.ndarray,
        adjacency: np.ndarray,
    ) -> np.ndarray:
        if self.model is None or self.mean is None or self.scale is None:
            raise RuntimeError("MPNNRegressor is not fitted")
        values, mask_values, adjacency_values = self._validate(
            features, mask, adjacency
        )
        if self.input_shape is not None and values.shape[1:] != self.input_shape:
            raise ValueError(
                f"expected entity shape {self.input_shape}, got {values.shape[1:]}"
            )
        return predict_regressor(
            self.model,
            (values, mask_values, adjacency_values),
            self.mean,
            self.scale,
        )
