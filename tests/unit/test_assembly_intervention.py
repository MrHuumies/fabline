from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from fabline.harness.assembly_intervention import (
    AssemblyInterventionConfig,
    generate_intervention_dataset,
    run_assembly_intervention,
    write_assembly_intervention_report,
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


def _task() -> AssemblyInterventionConfig:
    return AssemblyInterventionConfig(
        episodes=16,
        seed_start=58000,
        sample_steps=(5, 10),
        warmup_steps=2,
        random_action_prob=0.3,
        success_score=100,
    )


def test_intervention_config_validates() -> None:
    with pytest.raises(ValueError):
        AssemblyInterventionConfig(episodes=0)
    with pytest.raises(ValueError):
        AssemblyInterventionConfig(sample_steps=())
    with pytest.raises(ValueError):
        AssemblyInterventionConfig(sample_steps=(3,), warmup_steps=5)
    with pytest.raises(ValueError):
        AssemblyInterventionConfig(random_action_prob=1.0)


def test_intervention_dataset_is_episode_split() -> None:
    dataset = generate_intervention_dataset(_config(), _task())
    assert dataset.X.shape[1] == 12
    assert len(dataset.X) == len(dataset.effect) == len(dataset.splits)
    assert set(dataset.splits) <= {"train", "val", "test"}
    assert dataset.episode_ids.min() == 58000
    assert dataset.episode_ids.max() == 58015
    assert np.isfinite(dataset.effect).all()
    np.testing.assert_allclose(
        dataset.effect,
        dataset.outcome_switch - dataset.outcome_continue,
    )
    for split in ("train", "val", "test"):
        episodes = set(
            dataset.episode_ids[dataset.splits == split].tolist()
        )
        for other in ("train", "val", "test"):
            if other == split:
                continue
            other_episodes = set(
                dataset.episode_ids[dataset.splits == other].tolist()
            )
            assert episodes.isdisjoint(other_episodes)


def test_assembly_intervention_runs_and_reports(tmp_path: Path) -> None:
    report = run_assembly_intervention(_config(), _task())
    assert report["task"]["id"] == "factory.assembly.recipe_intervention.v1"
    assert report["dataset"]["samples"] > 0
    assert "linear" in report["metrics"]
    assert "gbdt" in report["metrics"]
    assert "mlp" in report["metrics"]
    assert set(report["gates"]) == {
        "H1_skill",
        "H2_nonlinear",
        "H3_not_saturated",
        "H4_decision",
        "H5_mlp_skill",
    }
    assert "model_gain" in report["decisions"]
    assert "oracle_gain" in report["decisions"]
    path = write_assembly_intervention_report(tmp_path, report)
    assert path.exists()
    assert "Assembly recipe intervention" in path.read_text(encoding="utf-8")
