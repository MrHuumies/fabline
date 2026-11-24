from __future__ import annotations

import json

from fabline.harness.faults import run_fault_benchmark
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig


def test_fault_benchmark_end_to_end(tmp_path) -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    faults = FaultConfig(
        enabled=True,
        wear_per_craft=1,
        fault_threshold=5,
        repair_ticks=10,
    )
    results = run_fault_benchmark(
        tmp_path,
        episodes=12,
        seed_start=0,
        config=config,
        faults=faults,
    )
    assert set(results["views"]) == {"vector", "diagnostics"}
    for view in results["views"].values():
        assert view["samples"] > 0
        assert 0.0 <= view["positive_rate"] <= 1.0
        assert "gbdt" in view["metrics"]
        assert set(view["calibration"]) == {"gbdt", "mlp"}
        for method in view["calibration"].values():
            for key in ("brier", "nll", "ece"):
                assert key in method["test"]
    report = (tmp_path / "fault_report.md").read_text(encoding="utf-8")
    assert "Fault-mechanic benchmark" in report
    assert "| method | Brier | NLL | ECE |" in report
    payload = json.loads((tmp_path / "fault_results.json").read_text())
    assert payload["faults"]["enabled"] is True
