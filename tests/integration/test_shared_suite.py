from __future__ import annotations

import json

from fabline.harness.shared_suite import SharedSuiteConfig, run_shared_suite
from fabline.tasks.shared import SharedEpisodeConfig
from fabline.tasks.splits import SplitPlan
from fabline.worlds.factory.config import FactoryConfig


def test_shared_suite_runs_all_projections(tmp_path) -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )
    plan = SplitPlan(
        name="test-plan",
        scenarios={
            "train": ("ingot", "gear"),
            "val": ("ingot",),
            "test": ("extra_gear",),
            "shift": ("shift_gear",),
        },
        episodes_per_scenario={"train": 2, "val": 1, "test": 1, "shift": 1},
    )
    suite = SharedSuiteConfig(
        plan=plan,
        episode_config=SharedEpisodeConfig(
            warmup_ticks=20,
            episode_ticks=80,
            sample_interval=10,
            horizon=20,
            bottleneck_horizon=10,
        ),
        control_episodes=1,
        control_train_episodes=20,
        control_seeds=(0,),
        with_ci=True,
    )
    results = run_shared_suite(tmp_path, suite, config)

    assert set(results["tasks"]) == {
        "throughput-vector",
        "throughput-grid",
        "throughput-entities",
        "next-state",
        "masked-grid",
        "bottleneck",
        "expand-control",
        "control-dynamics",
    }
    vector_metrics = results["tasks"]["throughput-vector"]["metrics"]
    assert "ci" in vector_metrics["linear"]
    assert "shift" in vector_metrics["linear"]
    assert "graph_mp" in results["tasks"]["throughput-entities"]["metrics"]
    assert results["tasks"]["expand-control"]["metrics"]["scripted"]["success_rate"] == 1.0
    assert results["metadata"]["replays_validated"] == results["dataset"]["stats"]["episodes"]

    report = (tmp_path / "suite_report.md").read_text(encoding="utf-8")
    assert "Shared-episode benchmark report" in report
    assert "masked-grid" in report
    assert "control-dynamics" in report
    assert (tmp_path / "dataset" / "dataset_card.md").exists()
    payload = json.loads((tmp_path / "suite_results.json").read_text(encoding="utf-8"))
    assert payload["metadata"]["plan_name"] == "test-plan"
