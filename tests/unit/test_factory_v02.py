from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from fabline.cli.main import cmd_benchmark_v02
from fabline.harness.factory_v02 import (
    FactoryV02Config,
    build_expected_summary,
    compare_expected_summary,
    run_factory_v02,
    v02_plan,
)


def test_v02_plan_counts() -> None:
    plan = v02_plan(FactoryV02Config())
    assert plan.name == "compositional-v0.2"
    assert plan.episodes_per_scenario == {
        "train": 33,
        "val": 10,
        "test": 20,
        "shift": 20,
    }
    assert plan.scenarios["test"] == ("extra_gear",)
    assert plan.scenarios["shift"] == ("shift_gear",)


def test_committed_expected_summary_shape() -> None:
    path = (
        Path(__file__).resolve().parents[2]
        / "benchmarks"
        / "factory-v0.2"
        / "expected"
        / "summary.json"
    )
    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["benchmark"] == "factory-v0.2"
    assert summary["version"] == "0.2.0"
    assert (
        summary["core"]["config_hash"]
        == "5f0d54f34731d40a0dd8826b591de38cf3e8da30a2066ce285939515599cb475"
    )
    assert summary["core"]["episodes"] == 159
    assert summary["core"]["splits"] == {
        "train": 99,
        "val": 20,
        "test": 20,
        "shift": 20,
    }
    assert summary["headline_tasks"] == list(
        (
            "throughput-vector",
            "throughput-grid",
            "throughput-entities",
            "masked-grid",
            "bottleneck",
            "expand-control",
            "control-dynamics",
            "planning-triage",
            "fault-calibration",
            "causal-removal",
        )
    )
    assert summary["diagnostics"] == [
        "fault-prediction",
        "power-brownout",
        "next-state",
    ]
    assert len(summary["calibration"]["blocks"]) == 3
    assert len(summary["causal"]["blocks"]) == 3
    assert "planning" in summary


def test_v02_config_validation() -> None:
    with pytest.raises(ValueError):
        FactoryV02Config(core_train_per_scenario=0)
    with pytest.raises(ValueError):
        FactoryV02Config(core_val_per_scenario=0)
    with pytest.raises(ValueError):
        FactoryV02Config(fault_episodes=0)
    with pytest.raises(ValueError):
        FactoryV02Config(planning_seeds=())
    with pytest.raises(ValueError):
        FactoryV02Config(causal_seeds=())


def test_v02_expected_requires_planning(tmp_path) -> None:
    args = SimpleNamespace(
        out=str(tmp_path / "out"),
        expected=str(tmp_path / "summary.json"),
        check_expected=None,
        skip_planning=True,
        skip_diagnostics=True,
    )
    assert cmd_benchmark_v02(args) == 2
    assert not (tmp_path / "out").exists()


def test_v02_expected_summary_round_trip(tmp_path) -> None:
    config = FactoryV02Config(
        core_train_per_scenario=1,
        core_val_per_scenario=1,
        core_test_episodes=1,
        core_shift_episodes=1,
        control_episodes=1,
        control_train_episodes=10,
        control_seeds=(0,),
        fault_episodes=1,
        power_episodes=1,
        planning_seeds=(62000,),
        calibration_seeds=(63000,),
        calibration_episodes=10,
        causal_seeds=(64000,),
        causal_episodes=10,
    )
    report = run_factory_v02(
        tmp_path,
        config,
        include_planning=False,
        include_diagnostics=False,
    )
    expected = build_expected_summary(report)
    assert expected["core"]["episodes"] == 7
    assert expected["core"]["splits"] == {
        "train": 3,
        "val": 2,
        "test": 1,
        "shift": 1,
    }
    assert "planning" not in expected
    assert len(compare_expected_summary(expected, expected)) == 0

    drifted = copy.deepcopy(expected)
    drifted["core"]["episodes"] = 8
    mismatches = compare_expected_summary(expected, drifted)
    assert any("core.episodes" in mismatch for mismatch in mismatches)

    tolerated = copy.deepcopy(expected)
    value = tolerated["core"]["tasks"]["throughput-vector"]["metrics"]["linear"][
        "test"
    ]["r2"]
    tolerated["core"]["tasks"]["throughput-vector"]["metrics"]["linear"]["test"][
        "r2"
    ] = value + 0.001
    assert not any(
        "throughput-vector.metrics.linear.test.r2" in mismatch
        for mismatch in compare_expected_summary(expected, tolerated)
    )
