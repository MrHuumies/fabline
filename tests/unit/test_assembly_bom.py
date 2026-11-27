from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from fabline.harness.assembly_bom import (
    AssemblyBOMConfig,
    generate_bom_dataset,
    run_assembly_bom,
    write_assembly_bom_report,
)
from fabline.worlds.factory.config import FactoryConfig


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=False,
    )


def _task() -> AssemblyBOMConfig:
    return AssemblyBOMConfig(
        episodes=8,
        warmup_steps=5,
        horizon_steps=5,
        train_fraction=0.5,
        val_fraction=0.25,
        success_score=100,
        random_action_prob=0.3,
    )


def test_bom_config_validates() -> None:
    with pytest.raises(ValueError):
        AssemblyBOMConfig(episodes=0)
    with pytest.raises(ValueError):
        AssemblyBOMConfig(horizon_steps=0)
    with pytest.raises(ValueError):
        AssemblyBOMConfig(train_fraction=0.9, val_fraction=0.2)
    with pytest.raises(ValueError):
        AssemblyBOMConfig(random_action_prob=1.0)


def test_bom_dataset_is_episode_split() -> None:
    dataset = generate_bom_dataset(_config(), _task())
    assert dataset.X.shape[1] == 12
    assert len(dataset.X) == len(dataset.y) == len(dataset.splits)
    assert set(dataset.splits) == {"train", "val", "test"}
    assert dataset.episode_ids.min() == 0
    assert dataset.episode_ids.max() == 7
    for split in ("train", "val", "test"):
        episodes = set(
            dataset.episode_ids[dataset.splits == split].tolist()
        )
        assert episodes
        for other in ("train", "val", "test"):
            if other == split:
                continue
            other_episodes = set(
                dataset.episode_ids[dataset.splits == other].tolist()
            )
            assert episodes.isdisjoint(other_episodes)
    assert np.isfinite(dataset.y).all()


def test_assembly_bom_runs_and_reports(tmp_path: Path) -> None:
    report = run_assembly_bom(_config(), _task())
    assert report["task"]["id"] == "factory.assembly.bom.v1"
    assert report["dataset"]["splits"]["train"] > 0
    assert report["dataset"]["splits"]["test"] > 0
    assert "linear" in report["metrics"]
    assert "gbdt" in report["metrics"]
    assert "mlp" in report["metrics"]
    assert set(report["gates"]) == {
        "H1_skill",
        "H2_nonlinear",
        "H3_not_saturated",
        "H4_mlp_skill",
    }
    path = write_assembly_bom_report(tmp_path, report)
    assert path.exists()
    assert "Assembly BOM forecast" in path.read_text(encoding="utf-8")
