from __future__ import annotations

import pytest

from fabline.harness.efficiency import (
    EfficiencyConfig,
    run_efficiency,
    write_efficiency_report,
)


def test_efficiency_config_validation() -> None:
    with pytest.raises(ValueError):
        EfficiencyConfig(repeats=0)
    with pytest.raises(ValueError):
        EfficiencyConfig(train_episodes=0)


def test_efficiency_runs(tmp_path) -> None:
    report = run_efficiency(
        EfficiencyConfig(
            repeats=1,
            world_ticks=10,
            observation_repeats=5,
            train_episodes=2,
            val_episodes=1,
            test_episodes=1,
            shift_episodes=1,
            episode_ticks=80,
            sample_interval=20,
        )
    )
    assert report["task"] == "factory.efficiency.v1"
    assert report["dataset"]["episodes"] == 7
    assert report["world"]["ticks_per_second"] > 0
    assert len(report["models"]) == 10
    path = write_efficiency_report(tmp_path, report)
    assert path.exists()
    assert "FABLINE efficiency table" in path.read_text()
