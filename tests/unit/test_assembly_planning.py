from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from fabline.env.assembly import AssemblyControlConfig, AssemblyControlEnv
from fabline.harness.assembly_planning import (
    AssemblyPlanningConfig,
    evaluate_plan,
    run_assembly_planning,
    write_assembly_planning_report,
)
from fabline.worlds.factory.config import FactoryConfig


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=300,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=False,
    )


def _planning() -> AssemblyPlanningConfig:
    return AssemblyPlanningConfig(
        blocks=3,
        block_ticks=100,
        population=4,
        elites=2,
        iterations=2,
        random_plans=4,
        success_score=100,
    )


def test_evaluate_plan_shape() -> None:
    planning = _planning()
    env = AssemblyControlEnv(
        _config(),
        AssemblyControlConfig(
            episode_ticks=planning.blocks * planning.block_ticks,
            decision_interval=10,
            success_score=planning.success_score,
        ),
    )
    score = evaluate_plan(env, (0, 1, 0), planning, seed=0)
    assert np.isfinite(score)
    with pytest.raises(ValueError):
        evaluate_plan(env, (0, 1), planning, seed=0)


def test_assembly_planning_runs_and_reports(tmp_path: Path) -> None:
    results = run_assembly_planning(
        _config(), _planning(), seeds=(0, 1)
    )
    assert "always_gear" in results
    assert "always_assembly" in results
    assert "cem" in results
    assert "oracle" in results
    assert results["oracle"]["mean_score"] >= results["always_gear"]["mean_score"]
    path = write_assembly_planning_report(
        tmp_path,
        results,
        config={
            "blocks": 3,
            "block_ticks": 100,
            "population": 4,
            "elites": 2,
            "iterations": 2,
        },
    )
    assert path.exists()
