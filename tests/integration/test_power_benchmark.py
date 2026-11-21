from __future__ import annotations

import json

from fabline.harness.power import run_power_benchmark
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig


def test_power_benchmark_end_to_end(tmp_path) -> None:
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
    power = PowerConfig(
        enabled=True,
        generator_count=1,
        generator_capacity=9,
        generator_radius=8,
    )
    results = run_power_benchmark(
        tmp_path,
        episodes=12,
        seed_start=0,
        config=config,
        power=power,
    )
    assert set(results["views"]) == {"vector", "power"}
    for view in results["views"].values():
        assert view["samples"] > 0
        assert 0.0 <= view["positive_rate"] <= 1.0
        assert "gbdt" in view["metrics"]
        assert set(view["calibration"]) == {"gbdt", "mlp"}
        assert "ece" in view["calibration"]["gbdt"]["test"]
    report = (tmp_path / "power_report.md").read_text(encoding="utf-8")
    assert "Power-grid benchmark" in report
    assert "### Calibration" in report
    payload = json.loads((tmp_path / "power_results.json").read_text())
    assert payload["power"]["enabled"] is True
