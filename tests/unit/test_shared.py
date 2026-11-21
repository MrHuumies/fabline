from __future__ import annotations

import json

import numpy as np
import pytest

from fabline.core.hashing import config_hash
from fabline.harness.shared_data import (
    MASKED_GRID_PATCH,
    load_shared_dataset,
    project_bottleneck,
    project_masked_grid,
    project_next_state,
    project_tasks,
    project_throughput_entities,
    project_throughput_grid,
    project_throughput_vector,
)
from fabline.record.replay import validate_replay
from fabline.record.shared_writer import write_shared_dataset
from fabline.tasks.shared import (
    SharedEpisodeConfig,
    generate_shared_dataset,
    generate_shared_episode,
)
from fabline.tasks.splits import SplitPlan
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.world import FactoryWorld


@pytest.fixture
def shared_config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )


@pytest.fixture
def shared_plan() -> SplitPlan:
    return SplitPlan(
        name="test-plan",
        scenarios={
            "train": ("ingot", "gear"),
            "val": ("extra_ingot",),
            "test": ("extra_gear",),
            "shift": ("shift_gear",),
            "broken": ("broken_gear",),
        },
        episodes_per_scenario={
            "train": 2,
            "val": 1,
            "test": 1,
            "shift": 1,
            "broken": 1,
        },
    )


def test_generate_shared_episode_shapes(shared_config) -> None:
    episode = generate_shared_episode(
        shared_config,
        seed=0,
        scenario_name="gear",
        split="train",
        episode_config=SharedEpisodeConfig(
            warmup_ticks=20,
            warmup_jitter=0,
            episode_ticks=80,
            sample_interval=10,
            horizon=20,
            bottleneck_horizon=10,
        ),
    )
    assert episode.views["vector"].shape[1] == 18
    assert episode.views["grid"].shape[1:] == (8, 16, 6)
    assert episode.views["entity_features"].shape[1] == 32
    assert episode.targets["future_score"].shape == (6,)
    assert episode.targets["next_vector"].shape == (6, 18)
    assert episode.targets["bottleneck"].shape == (6,)
    assert len(episode.sample_ticks) == 6
    assert len(episode.state_hashes) == 6


def test_shared_dataset_roundtrip(tmp_path, shared_config, shared_plan) -> None:
    episodes = generate_shared_dataset(
        shared_config,
        shared_plan,
        SharedEpisodeConfig(
            warmup_ticks=20,
            episode_ticks=80,
            sample_interval=10,
            horizon=20,
            bottleneck_horizon=10,
        ),
    )
    manifest = write_shared_dataset(
        tmp_path / "shared",
        "shared-test",
        episodes,
        {
            "world_version": WORLD_VERSION,
            "config_hash": config_hash(shared_config),
            "plan_name": shared_plan.name,
            "plan_metadata": shared_plan.metadata,
            "episode_config": {},
        },
    )
    assert manifest["stats"]["episodes"] == 8
    assert manifest["stats"]["samples"] > 0
    assert "none" in manifest["stats"]["bottleneck"]
    assert (tmp_path / "shared" / "dataset_card.md").exists()

    dataset = load_shared_dataset(tmp_path / "shared")
    assert len(dataset.splits) == len(dataset.targets["future_score"])
    assert set(dataset.splits) == {"train", "val", "test", "shift", "broken"}
    assert set(dataset.scenarios) >= {"ingot", "gear", "extra_gear", "broken_gear"}

    vector = project_throughput_vector(dataset)
    grid = project_throughput_grid(dataset)
    entities = project_throughput_entities(dataset)
    next_state = project_next_state(dataset)
    bottleneck = project_bottleneck(dataset)
    masked = project_masked_grid(dataset)
    assert vector.X.shape[1] == 18
    assert grid.X.shape[1] == 8 * 16 * 6
    assert entities.graph is not None
    assert entities.graph["adjacency"].ndim == 3
    assert next_state.y.shape == vector.X.shape
    assert bottleneck.y.ndim == 1
    y0, y1, x0, x1 = MASKED_GRID_PATCH
    assert masked.y.shape[1] == (y1 - y0) * (x1 - x0) * 6
    masked_grid = masked.X.reshape(-1, 8, 16, 6)
    assert np.all(masked_grid[:, y0:y1, x0:x1, :] == 0)

    projections = project_tasks(dataset)
    assert set(projections) == {
        "throughput-vector",
        "throughput-grid",
        "throughput-entities",
        "next-state",
        "bottleneck",
        "masked-grid",
    }


def test_warmup_jitter_varies(shared_config) -> None:
    actual = []
    for seed in range(10):
        episode = generate_shared_episode(
            shared_config,
            seed=seed,
            scenario_name="gear",
            split="train",
            episode_config=SharedEpisodeConfig(
                warmup_ticks=20,
                warmup_jitter=20,
                episode_ticks=100,
                sample_interval=10,
                horizon=20,
                bottleneck_horizon=10,
            ),
        )
        actual.append(episode.meta["warmup_ticks_actual"])
    assert len(set(actual)) > 1
    assert min(actual) >= 20
    assert max(actual) <= 40


def test_shared_replay_validates(tmp_path, shared_config) -> None:
    episode = generate_shared_episode(
        shared_config,
        seed=4,
        scenario_name="gear",
        split="test",
        episode_config=SharedEpisodeConfig(
            warmup_ticks=20,
            episode_ticks=80,
            sample_interval=10,
            horizon=20,
            bottleneck_horizon=10,
        ),
    )
    write_shared_dataset(
        tmp_path / "shared",
        "shared-test",
        [episode],
        {
            "world_version": WORLD_VERSION,
            "config_hash": config_hash(shared_config),
            "plan_name": "test",
        },
    )
    replay = json.loads(
        (tmp_path / "shared" / "episodes" / episode.episode_id / "replay.json").read_text()
    )
    validate_replay(FactoryWorld(shared_config), replay)


def test_split_plan_rejects_unknown_scenario() -> None:
    with pytest.raises(ValueError):
        SplitPlan(
            name="bad",
            scenarios={"train": ("unknown",)},
            episodes_per_scenario={"train": 1},
        )
