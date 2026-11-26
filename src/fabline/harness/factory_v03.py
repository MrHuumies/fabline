"""The `factory-v0.3` benchmark orchestrator."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from fabline.harness.factory_v02 import (
    FactoryV02Config,
    run_factory_v02,
)
from fabline.harness.factory_v02 import (
    build_expected_summary as build_v02_expected,
)
from fabline.harness.order_control import (
    run_order_control,
    write_order_control_report,
)
from fabline.harness.order_planning import (
    OrderPlanningConfig,
    run_order_planning,
    write_order_planning_report,
)
from fabline.harness.production_mix import (
    run_production_mix,
    write_production_mix_report,
)
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.production import ProductionConfig

BENCHMARK_ID = "factory-v0.3"
BENCHMARK_VERSION = "0.3.0"
BENCHMARK_DATE = "2026-11-26"

ORDER_TASKS = ("order-control", "order-planning")
DIAGNOSTIC_TASKS = (
    "fault-prediction",
    "power-brownout",
    "next-state",
    "production-mix",
    "order-rl",
)


@dataclass(frozen=True)
class FactoryV03Config:
    v02: FactoryV02Config = field(default_factory=FactoryV02Config)
    order_seeds: tuple[int, ...] = (72000, 72001, 72002, 72003, 72004)
    order_episodes: int = 5
    order_q_episodes: int = 100
    planning_seeds: tuple[int, ...] = (74000, 74001, 74002, 74003, 74004)
    planning_blocks: int = 5
    planning_population: int = 16
    planning_elites: int = 4
    planning_iterations: int = 4
    planning_random_samples: int = 32
    production_seeds: tuple[int, ...] = (70000, 70001, 70002, 70003, 70004)
    production_episodes: int = 5
    production_q_episodes: int = 50

    def __post_init__(self) -> None:
        if not self.order_seeds or not self.planning_seeds:
            raise ValueError("order/planning seeds must not be empty")
        if self.order_episodes <= 0 or self.production_episodes <= 0:
            raise ValueError("episode budgets must be positive")


def _order_config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=300,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )


def _compact_order_control(
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for name, row in results.items():
        compact[name] = {
            "mean_value": row["mean_value"],
            "value_ci": row["value_ci"],
            "success_rate": row["success_rate"],
            "mean_failed": row["mean_failed"],
            "mean_wasted": row["mean_wasted"],
            "mean_switches": row["mean_switches"],
        }
        if "model" in row:
            compact[name]["model"] = row["model"]
    return compact


def _compact_order_planning(report: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for name, row in report["results"].items():
        compact[name] = {
            "mean_value": row["mean_value"],
            "value_ci": row["value_ci"],
            "success_rate": row["success_rate"],
        }
    return compact


def run_factory_v03(
    out_dir: str | Path,
    config: FactoryV03Config | None = None,
    *,
    include_v02_planning: bool = True,
    include_diagnostics: bool = True,
    include_production_diagnostic: bool = True,
) -> dict[str, Any]:
    cfg = config or FactoryV03Config()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    v02 = run_factory_v02(
        out / "v02",
        cfg.v02,
        include_planning=include_v02_planning,
        include_diagnostics=include_diagnostics,
    )

    factory_config = _order_config()
    order_control = run_order_control(
        factory_config,
        seeds=cfg.order_seeds,
        episodes=cfg.order_episodes,
        q_episodes=cfg.order_q_episodes,
    )
    write_order_control_report(
        out / "order-control",
        order_control,
        config={
            "width": factory_config.width,
            "height": factory_config.height,
            "seeds": list(cfg.order_seeds),
            "success_value": 160,
        },
    )
    planning = OrderPlanningConfig(
        episode_ticks=300,
        decision_interval=10,
        blocks=cfg.planning_blocks,
        population=cfg.planning_population,
        elites=cfg.planning_elites,
        iterations=cfg.planning_iterations,
        random_samples=cfg.planning_random_samples,
    )
    order_planning = run_order_planning(
        factory_config,
        planning,
        seeds=cfg.planning_seeds,
    )
    write_order_planning_report(out / "order-planning", order_planning)

    diagnostics: dict[str, Any] = {}
    if include_production_diagnostic:
        production = run_production_mix(
            factory_config,
            seeds=cfg.production_seeds,
            episodes=cfg.production_episodes,
            q_episodes=cfg.production_q_episodes,
        )
        write_production_mix_report(
            out / "production-mix",
            production,
            config={
                "width": factory_config.width,
                "height": factory_config.height,
                "seeds": list(cfg.production_seeds),
                "success_score": 200,
                "component_score": ProductionConfig().component_score,
            },
        )
        diagnostics["production_mix"] = production

    report = {
        "benchmark": BENCHMARK_ID,
        "status": "candidate",
        "config": asdict(cfg),
        "blocks": {
            **v02["blocks"],
            "order_control": order_control,
            "order_planning": order_planning,
            **({"diagnostics": diagnostics} if diagnostics else {}),
        },
    }
    (out / "factory_v03_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return report


def build_expected_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Build the compact frozen summary for factory-v0.3."""

    v02_expected = build_v02_expected(
        {
            "blocks": {
                key: value
                for key, value in report["blocks"].items()
                if key in {"core", "planning", "calibration", "causal"}
            }
        }
    )
    expected: dict[str, Any] = {
        "benchmark": BENCHMARK_ID,
        "version": BENCHMARK_VERSION,
        "date": BENCHMARK_DATE,
        "world_version": WORLD_VERSION,
        "plan": "compositional-v0.3",
        "tolerance": {"rtol": 0.03, "atol": 0.02},
        "headline_tasks": [
            *v02_expected["headline_tasks"],
            *ORDER_TASKS,
        ],
        "diagnostics": list(DIAGNOSTIC_TASKS),
        "core": v02_expected["core"],
        "calibration": v02_expected["calibration"],
        "causal": v02_expected["causal"],
        "order_control": _compact_order_control(
            report["blocks"]["order_control"]
        ),
        "order_planning": _compact_order_planning(
            report["blocks"]["order_planning"]
        ),
    }
    if "planning" in v02_expected:
        expected["planning"] = v02_expected["planning"]
    return expected


def write_factory_v03_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    order_control = report["blocks"]["order_control"]
    order_planning = report["blocks"]["order_planning"]
    lines = [
        "# factory-v0.3 candidate",
        "",
        f"- status: {report['status']}",
        f"- core episodes: {report['blocks']['core']['episodes']}",
        f"- core samples: {report['blocks']['core']['samples']}",
        f"- core config hash: `{report['blocks']['core']['config_hash']}`",
        f"- order control value (value policy): "
        f"{order_control['value']['mean_value']:.1f}",
        f"- order planning value (CEM): "
        f"{order_planning['results']['cem']['mean_value']:.1f}",
        "",
        "Diagnostics: production mix; deep/offline RL is documented separately.",
        "",
        "This is the candidate; freeze only after the expected summary and CI "
        "check are checked in.",
        "",
    ]
    path = out / "factory_v03_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
