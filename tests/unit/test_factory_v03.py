from __future__ import annotations

import json

from fabline.harness.factory_v02 import FactoryV02Config
from fabline.harness.factory_v03 import (
    FactoryV03Config,
    build_expected_summary,
    run_factory_v03,
)


def test_v03_expected_summary_round_trip(tmp_path) -> None:
    cfg = FactoryV03Config(
        v02=FactoryV02Config(
            core_train_per_scenario=1,
            core_val_per_scenario=1,
            core_test_episodes=1,
            core_shift_episodes=1,
            control_episodes=1,
            control_train_episodes=10,
            control_seeds=(0,),
            fault_episodes=1,
            power_episodes=1,
            calibration_seeds=(63000,),
            calibration_episodes=10,
            causal_seeds=(64000,),
            causal_episodes=10,
        ),
        order_seeds=(72000,),
        order_episodes=1,
        order_q_episodes=2,
        planning_seeds=(74000,),
        planning_blocks=3,
        planning_population=4,
        planning_elites=2,
        planning_iterations=1,
        planning_random_samples=2,
    )
    report = run_factory_v03(
        tmp_path,
        cfg,
        include_v02_planning=False,
        include_diagnostics=False,
        include_production_diagnostic=False,
    )
    expected = build_expected_summary(report)
    assert expected["benchmark"] == "factory-v0.3"
    assert expected["core"]["episodes"] == 7
    assert "planning" not in expected
    assert "order_control" in expected
    assert "order_planning" in expected
    assert expected["headline_tasks"][-2:] == [
        "order-control",
        "order-planning",
    ]
    path = tmp_path / "expected.json"
    path.write_text(json.dumps(expected), encoding="utf-8")
    assert path.exists()
