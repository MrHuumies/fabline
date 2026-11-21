"""Brownout-within-horizon prediction over the opt-in power grid."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from fabline.core.hashing import config_hash
from fabline.harness.metrics import classification_metrics
from fabline.obs.base import ObservationAdapter, flatten_observation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.labels import future_brownout
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.world import FactoryWorld

from .base import EpisodeData
from .splits import assign_split


@dataclass(frozen=True)
class PowerTaskConfig:
    warmup_ticks: int = 100
    episode_ticks: int = 500
    sample_interval: int = 5
    horizon: int = 5
    power: PowerConfig = field(
        default_factory=lambda: PowerConfig(
            enabled=True,
            generator_count=1,
            generator_capacity=9,
            generator_radius=8,
        )
    )
    faults: FaultConfig = field(default_factory=FaultConfig)

    def __post_init__(self) -> None:
        if self.warmup_ticks < 0:
            raise ValueError("warmup_ticks must be non-negative")
        if self.sample_interval <= 0:
            raise ValueError("sample_interval must be positive")
        if self.episode_ticks <= self.warmup_ticks + self.horizon:
            raise ValueError("episode_ticks is too short")
        if not self.power.enabled:
            raise ValueError("power prediction requires power.enabled")


class PowerBrownoutTask:
    """Predict whether a new brownout starts in the next horizon."""

    id = "factory.power.brownout.v1"
    version = "0.1.0"

    def __init__(
        self,
        config: FactoryConfig,
        task_config: PowerTaskConfig,
        observation: ObservationAdapter,
    ) -> None:
        if not config.starter_line:
            raise ValueError("power prediction requires a starter line")
        if not config.emit_events:
            raise ValueError("power prediction requires emit_events")
        self.config = config
        self.task_config = task_config
        self.observation = observation

    def generate_episode(self, seed: int, split: str | None = None) -> EpisodeData:
        split = split or assign_split(seed)
        world = FactoryWorld(
            self.config,
            self.task_config.faults,
            self.task_config.power,
        )
        world.reset(seed, SCENARIOS["gear"])
        world.run_ticks(self.task_config.warmup_ticks)

        observations: list[np.ndarray] = []
        labels: list[int] = []
        sample_ticks: list[int] = []
        hashes: list[str] = []

        while (
            world.state.tick + self.task_config.horizon
            <= self.task_config.episode_ticks
        ):
            observations.append(
                flatten_observation(
                    self.observation,
                    self.observation.observe(world.state),
                )
            )
            labels.append(future_brownout(world, self.task_config.horizon))
            sample_ticks.append(world.state.tick)
            hashes.append(world.state_hash())
            if (
                world.state.tick
                + self.task_config.sample_interval
                + self.task_config.horizon
                > self.task_config.episode_ticks
            ):
                break
            world.run_ticks(self.task_config.sample_interval)

        spec = self.observation.spec
        meta: dict[str, Any] = {
            "task_id": self.id,
            "task_version": self.version,
            "target_name": "brownout_within_horizon",
            "observation": {
                "name": spec.name,
                "version": spec.version,
                "shape": list(spec.shape) if spec.shape is not None else None,
                "feature_names": list(spec.feature_names) if spec.feature_names else None,
            },
            "scenario": "gear",
            "warmup_ticks": self.task_config.warmup_ticks,
            "episode_ticks": self.task_config.episode_ticks,
            "sample_interval": self.task_config.sample_interval,
            "horizon": self.task_config.horizon,
            "power": asdict(self.task_config.power),
            "config_hash": config_hash(self.config),
            "seed": seed,
            "split": split,
        }
        if self.task_config.faults.enabled:
            meta["faults"] = asdict(self.task_config.faults)
        return EpisodeData(
            episode_id=f"power_{seed:06d}",
            seed=seed,
            split=split,
            observations=np.stack(observations),
            labels=np.asarray(labels, dtype=np.float32),
            sample_ticks=sample_ticks,
            state_hashes=hashes,
            events=[],
            meta=meta,
        )

    def generate(self, episodes: int, seed_start: int = 0) -> list[EpisodeData]:
        if episodes <= 0:
            raise ValueError("episodes must be positive")
        return [
            self.generate_episode(seed)
            for seed in range(seed_start, seed_start + episodes)
        ]

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
        return classification_metrics(y_true, y_pred)
