"""The M1 supervised task: predict future depot output from a state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from fabline.core.hashing import config_hash
from fabline.harness.metrics import regression_metrics
from fabline.obs.base import ObservationAdapter, flatten_observation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import Scenario
from fabline.worlds.factory.labels import future_score
from fabline.worlds.factory.world import FactoryWorld

from .base import EpisodeData
from .splits import assign_split


@dataclass(frozen=True)
class ThroughputConfig:
    horizon: int = 100
    warmup_ticks: int = 200
    episode_ticks: int = 500
    sample_interval: int = 10

    def __post_init__(self) -> None:
        if self.horizon <= 0:
            raise ValueError("horizon must be positive")
        if self.warmup_ticks < 0:
            raise ValueError("warmup_ticks must be non-negative")
        if self.sample_interval <= 0:
            raise ValueError("sample_interval must be positive")
        if self.episode_ticks <= self.warmup_ticks + self.horizon:
            raise ValueError("episode_ticks must exceed warmup_ticks + horizon")


class ThroughputTask:
    """Predict depot score over the next ``horizon`` ticks.

    The label is computed by cloning the world and running it forward with no
    actions. This is a supervised, offline task; it does not use the action
    adapter.
    """

    id = "factory.throughput.predict.v1"
    version = "0.1.0"

    def __init__(
        self,
        config: FactoryConfig,
        task_config: ThroughputConfig,
        observation: ObservationAdapter,
        *,
        keep_events: bool = False,
        scenario: Scenario | None = None,
        flatten: bool = True,
    ) -> None:
        self.config = config
        self.task_config = task_config
        self.observation = observation
        self.keep_events = keep_events
        self.scenario = scenario
        self.flatten = flatten

    def generate_episode(self, seed: int, split: str | None = None) -> EpisodeData:
        split = split or assign_split(seed)
        world = FactoryWorld(self.config)
        world.reset(seed, self.scenario)
        world.run_ticks(self.task_config.warmup_ticks)

        observations: list[np.ndarray] = []
        labels: list[int] = []
        sample_ticks: list[int] = []
        hashes: list[str] = []

        while world.state.tick + self.task_config.horizon <= self.task_config.episode_ticks:
            raw = self.observation.observe(world.state)
            observations.append(
                flatten_observation(self.observation, raw)
                if self.flatten
                else np.asarray(raw, dtype=np.float32)
            )
            labels.append(future_score(world, self.task_config.horizon))
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
            "target_name": "future_score",
            "observation": {
                "name": spec.name,
                "version": spec.version,
                "shape": list(spec.shape) if spec.shape is not None else None,
                "feature_names": list(spec.feature_names) if spec.feature_names else None,
            },
            "horizon": self.task_config.horizon,
            "warmup_ticks": self.task_config.warmup_ticks,
            "episode_ticks": self.task_config.episode_ticks,
            "sample_interval": self.task_config.sample_interval,
            "config_hash": config_hash(self.config),
            "seed": seed,
            "split": split,
            "scenario": self.scenario.name if self.scenario is not None else None,
        }

        return EpisodeData(
            episode_id=f"ep_{seed:06d}",
            seed=seed,
            split=split,
            observations=np.stack(observations),
            labels=np.asarray(labels, dtype=np.float32),
            sample_ticks=sample_ticks,
            state_hashes=hashes,
            events=list(world.state.events) if self.keep_events else [],
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
        return regression_metrics(y_true, y_pred)
