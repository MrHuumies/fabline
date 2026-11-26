from __future__ import annotations

import pytest

from fabline.harness.order_planning import (
    OrderPlanningConfig,
    run_order_planning,
)
from fabline.worlds.factory.config import FactoryConfig


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=120,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )


def test_order_planning_config_validation() -> None:
    with pytest.raises(ValueError):
        OrderPlanningConfig(blocks=0)
    with pytest.raises(ValueError):
        OrderPlanningConfig(episode_ticks=100, blocks=3)


def test_order_planning_runs() -> None:
    cfg = OrderPlanningConfig(
        episode_ticks=120,
        decision_interval=10,
        blocks=3,
        population=4,
        elites=2,
        iterations=1,
        random_samples=2,
    )
    report = run_order_planning(
        _config(), cfg, seeds=(73000,)
    )
    assert set(report["results"]) == {
        "always_gear",
        "always_component",
        "edf_plan",
        "value_plan",
        "random_plan",
        "cem",
        "oracle",
    }
    assert report["results"]["oracle"]["mean_value"] >= 0.0
