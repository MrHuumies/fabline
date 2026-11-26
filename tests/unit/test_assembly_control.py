from __future__ import annotations

from pathlib import Path

from fabline.env.assembly import AssemblyControlConfig, AssemblyControlEnv
from fabline.harness.assembly_control import (
    run_assembly_control,
    write_assembly_control_report,
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


def test_assembly_env_direct_and_assembly() -> None:
    env = AssemblyControlEnv(_config(), AssemblyControlConfig())
    _, info = env.reset(0)
    done = False
    while not done:
        _, _, terminated, truncated, info = env.step(1)
        done = terminated or truncated
    assert info["score"] > 0
    assert info["delivered_gear"] > 0
    direct_env = AssemblyControlEnv(_config(), AssemblyControlConfig())
    direct_env.reset(0)
    done = False
    while not done:
        _, _, terminated, truncated, info = direct_env.step(0)
        done = terminated or truncated
    assert info["score"] > 0


def test_assembly_control_harness_runs(tmp_path: Path) -> None:
    results = run_assembly_control(
        _config(),
        AssemblyControlConfig(),
        seeds=(0, 1),
        episodes=1,
        q_episodes=10,
    )
    assert "always_gear" in results
    assert "always_assembly" in results
    assert "buffer_aware" in results
    assert "tabular_q" in results
    assert results["buffer_aware"]["mean_score"] > results["always_gear"]["mean_score"]
    report = write_assembly_control_report(
        tmp_path,
        results,
        config={"success_score": 100, "seeds": [0, 1]},
    )
    assert report.exists()
