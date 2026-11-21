from __future__ import annotations

import numpy as np
import pytest

from fabline.core.hashing import config_hash
from fabline.harness.baselines import (
    evaluate_baselines,
    evaluate_next_state_baselines,
)
from fabline.harness.data import load_dataset
from fabline.harness.metrics import multi_output_metrics
from fabline.obs.base import flatten_observation
from fabline.obs.vector import FEATURES, VectorObservation
from fabline.record.writer import write_dataset
from fabline.tasks.next_state import NextStateConfig, NextStateTask
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.world import FactoryWorld


@pytest.fixture
def next_state_config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )


def test_next_state_pairs_match_manual_rollout(next_state_config) -> None:
    task = NextStateTask(
        next_state_config,
        NextStateConfig(warmup_ticks=50, episode_ticks=150, sample_interval=10),
        VectorObservation(next_state_config),
    )
    episode = task.generate_episode(3)
    assert episode.observations.shape[1] == len(FEATURES)
    assert episode.labels.shape == episode.observations.shape

    world = FactoryWorld(next_state_config)
    world.reset(3)
    world.run_ticks(50)
    adapter = VectorObservation(next_state_config)
    first = flatten_observation(adapter, adapter.observe(world.state))
    world.run_ticks(10)
    second = flatten_observation(adapter, adapter.observe(world.state))
    assert np.allclose(episode.observations[0], first)
    assert np.allclose(episode.labels[0], second)


def test_next_state_dataset_roundtrip(tmp_path, next_state_config) -> None:
    adapter = VectorObservation(next_state_config)
    task = NextStateTask(
        next_state_config,
        NextStateConfig(warmup_ticks=50, episode_ticks=150, sample_interval=10),
        adapter,
    )
    episodes = task.generate(12)
    manifest = write_dataset(
        tmp_path / "dataset",
        "next-state-test",
        episodes,
        {
            "world_version": WORLD_VERSION,
            "config_hash": config_hash(next_state_config),
            "task_id": task.id,
            "task_version": task.version,
            "target_name": "next_observation",
            "observation": {
                "name": adapter.spec.name,
                "version": adapter.spec.version,
                "shape": list(adapter.spec.shape),
                "feature_names": list(adapter.spec.feature_names),
            },
        },
    )
    assert manifest["target_name"] == "next_observation"
    loaded = load_dataset(tmp_path / "dataset")
    assert loaded.y.ndim == 2
    assert loaded.y.shape == loaded.X.shape
    assert set(loaded.splits) == {"train", "val", "test"}


def test_multi_output_metrics() -> None:
    truth = np.array([[1.0, 0.0], [0.0, 1.0]])
    metrics = multi_output_metrics(truth, truth)
    assert metrics["mse"] == 0.0
    assert metrics["cosine"] == pytest.approx(1.0)
    shifted = multi_output_metrics(truth, truth + 1.0)
    assert shifted["mse"] == pytest.approx(1.0)
    assert shifted["cosine"] < 1.0


def test_next_state_baselines(next_state_config) -> None:
    adapter = VectorObservation(next_state_config)
    task = NextStateTask(
        next_state_config,
        NextStateConfig(warmup_ticks=50, episode_ticks=150, sample_interval=10),
        adapter,
    )
    episodes = task.generate(12)
    X = np.concatenate([episode.observations for episode in episodes])
    y = np.concatenate([episode.labels for episode in episodes])
    splits = np.concatenate(
        [
            np.full(len(episode.labels), episode.split, dtype=object)
            for episode in episodes
        ]
    )
    train = splits == "train"
    val = splits == "val"
    test = splits == "test"
    results = evaluate_next_state_baselines(
        X[train], y[train], X[val], y[val], X[test], y[test]
    )
    assert set(results) == {"copy", "linear", "mlp"}
    assert "test" in results["mlp"]


def test_learned_tabular_baselines() -> None:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(60, 4))
    y = 2.0 * X[:, 0] - X[:, 1] + 0.1
    results = evaluate_baselines(
        X[:40],
        y[:40],
        X[40:50],
        y[40:50],
        X[50:],
        y[50:],
        feature_names=None,
        include_models=True,
    )
    assert {"mean", "linear", "gbdt", "mlp"} <= set(results)
    assert "skipped" in results["persistence"]
    assert "test" in results["gbdt"]
