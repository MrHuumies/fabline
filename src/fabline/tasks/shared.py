"""Shared episode recording: one rollout, several views and targets."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

import numpy as np

from fabline.core.hashing import config_hash
from fabline.obs.entities import EntitiesObservation
from fabline.obs.grid import GridObservation
from fabline.obs.vector import VectorObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.labels import bottleneck_label, future_score
from fabline.worlds.factory.world import FactoryWorld

from .splits import SplitPlan


@dataclass(frozen=True)
class SharedEpisodeConfig:
    warmup_ticks: int = 100
    warmup_jitter: int = 20
    episode_ticks: int = 300
    sample_interval: int = 10
    horizon: int = 50
    bottleneck_horizon: int = 30

    def __post_init__(self) -> None:
        if self.warmup_ticks < 0:
            raise ValueError("warmup_ticks must be non-negative")
        if self.warmup_jitter < 0:
            raise ValueError("warmup_jitter must be non-negative")
        if self.sample_interval <= 0:
            raise ValueError("sample_interval must be positive")
        if (
            self.episode_ticks
            <= self.warmup_ticks + self.warmup_jitter + self.sample_interval
        ):
            raise ValueError("episode_ticks is too short")
        if self.horizon <= 0 or self.bottleneck_horizon <= 0:
            raise ValueError("label horizons must be positive")


@dataclass
class SharedEpisode:
    episode_id: str
    seed: int
    scenario: str
    split: str
    sample_ticks: list[int]
    state_hashes: list[str]
    views: dict[str, np.ndarray]
    targets: dict[str, np.ndarray]
    meta: dict[str, Any]


def generate_shared_episode(
    config: FactoryConfig,
    seed: int,
    scenario_name: str,
    split: str,
    episode_config: SharedEpisodeConfig,
) -> SharedEpisode:
    """Run one passive episode and record all views and targets."""

    if scenario_name not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario_name}")
    scenario = SCENARIOS[scenario_name]
    vector = VectorObservation(config)
    grid = GridObservation(config)
    entities = EntitiesObservation(config)

    world = FactoryWorld(config)
    world.reset(seed, scenario)
    jitter_rng = random.Random(seed)
    warmup_actual = episode_config.warmup_ticks
    if episode_config.warmup_jitter:
        warmup_actual += jitter_rng.randrange(0, episode_config.warmup_jitter + 1)
    world.run_ticks(warmup_actual)

    vectors: list[np.ndarray] = []
    grids: list[np.ndarray] = []
    entity_features: list[np.ndarray] = []
    entity_masks: list[np.ndarray] = []
    adjacencies: list[np.ndarray] = []
    future_scores: list[int] = []
    bottlenecks: list[str] = []
    next_vectors: list[np.ndarray] = []
    sample_ticks: list[int] = []
    hashes: list[str] = []

    while (
        world.state.tick + episode_config.sample_interval
        <= episode_config.episode_ticks
    ):
        sample_ticks.append(world.state.tick)
        hashes.append(world.state_hash())
        vectors.append(vector.observe(world.state))
        grids.append(grid.observe(world.state))
        graph = entities.observe(world.state)
        entity_features.append(graph.entity_features)
        entity_masks.append(graph.entity_mask)
        adjacencies.append(graph.adjacency)
        future_scores.append(future_score(world, episode_config.horizon))
        bottlenecks.append(
            bottleneck_label(world, episode_config.bottleneck_horizon)
        )
        world.run_ticks(episode_config.sample_interval)
        next_vectors.append(vector.observe(world.state))

    spec_meta = {
        "task_id": "factory.shared_episode.v1",
        "task_version": "0.1.0",
        "scenario": scenario_name,
        "split": split,
        "seed": seed,
        "warmup_ticks": episode_config.warmup_ticks,
        "warmup_ticks_actual": warmup_actual,
        "warmup_jitter": episode_config.warmup_jitter,
        "episode_ticks": episode_config.episode_ticks,
        "sample_interval": episode_config.sample_interval,
        "horizon": episode_config.horizon,
        "bottleneck_horizon": episode_config.bottleneck_horizon,
        "config_hash": config_hash(config),
        "views": {
            "vector": {
                "version": vector.spec.version,
                "shape": list(vector.spec.shape or ()),
            },
            "grid": {"version": grid.spec.version, "shape": list(grid.spec.shape or ())},
            "entities": {
                "version": entities.spec.version,
                "max_entities": entities.max_entities,
                "feature_names": list(entities.spec.feature_names or ()),
            },
        },
    }

    return SharedEpisode(
        episode_id=f"{split}_{scenario_name}_{seed:06d}",
        seed=seed,
        scenario=scenario_name,
        split=split,
        sample_ticks=sample_ticks,
        state_hashes=hashes,
        views={
            "vector": np.stack(vectors),
            "grid": np.stack(grids),
            "entity_features": np.stack(entity_features),
            "entity_mask": np.stack(entity_masks),
            "adjacency": np.stack(adjacencies),
        },
        targets={
            "future_score": np.asarray(future_scores, dtype=np.float32),
            "bottleneck": np.asarray(bottlenecks),
            "next_vector": np.stack(next_vectors),
        },
        meta=spec_meta,
    )


def generate_shared_dataset(
    config: FactoryConfig,
    plan: SplitPlan,
    episode_config: SharedEpisodeConfig,
) -> list[SharedEpisode]:
    """Generate episodes for every split/scenario in the plan."""

    episodes: list[SharedEpisode] = []
    seed = plan.seed_start
    for split, scenarios in plan.scenarios.items():
        for scenario_name in scenarios:
            for _ in range(plan.episodes_per_scenario[split]):
                episodes.append(
                    generate_shared_episode(
                        config,
                        seed=seed,
                        scenario_name=scenario_name,
                        split=split,
                        episode_config=episode_config,
                    )
                )
                seed += 1
    return episodes
