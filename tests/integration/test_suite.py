from __future__ import annotations

import json

from fabline.harness.suite import SuiteConfig, run_suite
from fabline.worlds.factory.config import FactoryConfig


def test_suite_runs_five_tasks(tmp_path) -> None:
    factory = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        decision_interval=10,
        entity_budget=16,
        rock_density=0.02,
        ore_patches=1,
        starter_line=True,
    )
    suite = SuiteConfig(
        episodes=12,
        seed_start=0,
        throughput_horizon=20,
        throughput_warmup=40,
        throughput_episode_ticks=100,
        next_state_warmup=40,
        next_state_episode_ticks=100,
        control_episodes=1,
        control_train_episodes=20,
        control_seeds=(0,),
    )
    results = run_suite(tmp_path, suite, factory)
    tasks = results["tasks"]
    assert set(tasks) == {
        "throughput-vector",
        "throughput-grid",
        "throughput-entities",
        "next-state",
        "expand-control",
    }
    assert tasks["expand-control"]["metrics"]["scripted"]["success_rate"] == 1.0
    assert "mlp" in tasks["throughput-vector"]["metrics"]
    assert "mlp" in tasks["next-state"]["metrics"]

    report = (tmp_path / "suite_report.md").read_text(encoding="utf-8")
    assert "M2 task suite report" in report
    assert "expand-control" in report
    payload = json.loads((tmp_path / "suite_results.json").read_text(encoding="utf-8"))
    assert payload["metadata"]["world_version"] == "factory-0.1.0"
