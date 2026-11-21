"""Shared task records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from fabline.core.events import Event


@dataclass
class EpisodeData:
    """A recorded episode projection used by the dataset writer."""

    episode_id: str
    seed: int
    split: str
    observations: np.ndarray
    labels: np.ndarray
    sample_ticks: list[int]
    state_hashes: list[str]
    events: list[Event]
    meta: dict[str, Any]
