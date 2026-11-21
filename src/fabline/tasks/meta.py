"""Shared manifest metadata for task projections."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Protocol

from fabline.core.hashing import config_hash
from fabline.obs.base import ObservationAdapter
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig


class _TaskLike(Protocol):
    id: str
    version: str


def manifest_meta(
    config: FactoryConfig,
    task: _TaskLike,
    observation: ObservationAdapter,
    target_name: str,
    power: PowerConfig | None = None,
) -> dict[str, Any]:
    spec = observation.spec
    result: dict[str, Any] = {
        "world_version": WORLD_VERSION,
        "config_hash": config_hash(config),
        "task_id": task.id,
        "task_version": task.version,
        "target_name": target_name,
        "observation": {
            "name": spec.name,
            "version": spec.version,
            "shape": list(spec.shape) if spec.shape is not None else None,
            "feature_names": list(spec.feature_names) if spec.feature_names else None,
        },
    }
    if power is not None and power.enabled:
        result["power"] = asdict(power)
    return result
