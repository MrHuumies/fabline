"""Task adapters."""

from __future__ import annotations

from .base import EpisodeData
from .fault_prediction import FaultPredictionTask, FaultTaskConfig
from .next_state import NextStateConfig, NextStateTask
from .power import PowerBrownoutTask, PowerTaskConfig
from .throughput import ThroughputConfig, ThroughputTask

__all__ = [
    "EpisodeData",
    "FaultPredictionTask",
    "FaultTaskConfig",
    "NextStateConfig",
    "NextStateTask",
    "PowerBrownoutTask",
    "PowerTaskConfig",
    "ThroughputConfig",
    "ThroughputTask",
]
