"""Public baseline models for FABLINE's structured observation views.

The implementations are original FABLINE code and use only PyTorch core. No
third-party model code is vendored. See ``README.md`` for the public-tree
policy and licensing note.
"""

from fabline.harness.models.cnn import CNNRegressor
from fabline.harness.models.common import (
    TorchTrainConfig,
    TorchTrainReport,
    torch_available,
)
from fabline.harness.models.gnn import MPNNRegressor
from fabline.harness.models.sequence import GRURegressor, TransformerRegressor

__all__ = [
    "CNNRegressor",
    "GRURegressor",
    "MPNNRegressor",
    "TorchTrainConfig",
    "TorchTrainReport",
    "TransformerRegressor",
    "torch_available",
]
