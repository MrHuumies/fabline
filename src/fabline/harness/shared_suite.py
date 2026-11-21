"""Shared-episode benchmark suite: one dataset, many task projections."""

from __future__ import annotations

import json
import platform
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from fabline import __version__
from fabline.core.hashing import config_hash
from fabline.env.control import ControlConfig
from fabline.harness.baselines import (
    evaluate_baselines,
    evaluate_classification_baselines,
    evaluate_next_state_baselines,
)
from fabline.harness.control import evaluate_control_policies
from fabline.harness.graph_models import evaluate_graph_baseline
from fabline.harness.shared_data import (
    TaskProjection,
    load_shared_dataset,
    project_tasks,
)
from fabline.record.replay import validate_replay
from fabline.record.shared_writer import write_shared_dataset
from fabline.tasks.control_dynamics import generate_control_transitions
from fabline.tasks.shared import (
    SharedEpisodeConfig,
    generate_shared_dataset,
)
from fabline.tasks.splits import SplitPlan, default_split_plan
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.world import FactoryWorld


@dataclass(frozen=True)
class SharedSuiteConfig:
    plan: SplitPlan = field(default_factory=default_split_plan)
    episode_config: SharedEpisodeConfig = field(default_factory=SharedEpisodeConfig)
    control_episodes: int = 5
    control_train_episodes: int = 200
    control_seeds: tuple[int, ...] = (0, 1, 2)
    with_ci: bool = True

    def __post_init__(self) -> None:
        if self.control_episodes <= 0 or self.control_train_episodes <= 0:
            raise ValueError("control budgets must be positive")
        if not self.control_seeds:
            raise ValueError("control_seeds must not be empty")


def _default_factory_config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )


def _split_arrays(projection: TaskProjection) -> dict[str, np.ndarray]:
    splits = np.asarray(projection.splits)
    masks = {name: splits == name for name in ("train", "val", "test", "shift")}
    for name, mask in masks.items():
        if not mask.any():
            raise ValueError(f"projection {projection.name} has no {name} split")
    return masks


def _projection_result(
    projection: TaskProjection,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": projection.kind,
        "observation": projection.name,
        "samples": int(len(projection.y)),
        "metrics": metrics,
    }


def _fmt(value: float, interval: tuple[float, float] | list[float] | None = None) -> str:
    if interval is None:
        return f"{value:.4f}"
    low, high = interval[0], interval[1]
    return f"{value:.4f} [{low:.4f}, {high:.4f}]"


def _metric_cell(
    result: dict[str, Any],
    split: str,
    metric: str,
) -> str:
    if "skipped" in result:
        return "—"
    value = result[split][metric]
    interval = result.get("ci", {}).get(split, {}).get(metric)
    return _fmt(value, interval)


def _write_report(out: Path, results: dict[str, Any]) -> None:
    tasks = results["tasks"]
    metadata = results["metadata"]
    dataset = results["dataset"]
    stats = dataset["stats"]
    hardware = metadata["hardware"]
    lines = [
        "# Shared-episode benchmark report",
        "",
        "This is the M3 benchmark candidate, not a public release.",
        "",
        "## Run metadata",
        "",
        f"- world: `{metadata['world_version']}`",
        f"- fabline: `{metadata['fabline_version']}`",
        f"- config hash: `{metadata['config_hash']}`",
        f"- plan: `{metadata['plan_name']}`",
        f"- machine: `{hardware['machine']}` / `{hardware['processor']}`",
        f"- python: `{hardware['python']}`",
        f"- duration: {metadata['duration_seconds']:.2f} s",
        f"- replays validated: {metadata['replays_validated']}",
        "",
        "## Dataset",
        "",
        f"- episodes: {stats['episodes']}",
        f"- samples: {stats['samples']}",
        f"- splits: {stats['splits']}",
        f"- scenarios: {stats['scenarios']}",
        "",
        "## Tasks",
        "",
        "| task | kind | samples |",
        "|---|---|---:|",
    ]
    for name, payload in tasks.items():
        lines.append(f"| {name} | {payload['kind']} | {payload['samples']} |")
    lines.append("")

    for name in ("throughput-vector", "throughput-grid", "throughput-entities"):
        if name not in tasks:
            continue
        lines.extend(
            [
                f"## {name}",
                "",
                "| method | test MAE | test R² | shift MAE | shift R² |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for method, result in tasks[name]["metrics"].items():
            if "skipped" in result:
                lines.append(f"| {method} | — | — | — | — |")
                continue
            lines.append(
                f"| {method} | {_metric_cell(result, 'test', 'mae')} | "
                f"{_metric_cell(result, 'test', 'r2')} | "
                f"{_metric_cell(result, 'shift', 'mae')} | "
                f"{_metric_cell(result, 'shift', 'r2')} |"
            )
        lines.append("")

    for name in ("next-state", "masked-grid"):
        if name not in tasks:
            continue
        lines.extend(
            [
                f"## {name}",
                "",
                "| method | test MSE | test cosine | shift MSE | shift cosine |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for method, result in tasks[name]["metrics"].items():
            lines.append(
                f"| {method} | {_metric_cell(result, 'test', 'mse')} | "
                f"{_metric_cell(result, 'test', 'cosine')} | "
                f"{_metric_cell(result, 'shift', 'mse')} | "
                f"{_metric_cell(result, 'shift', 'cosine')} |"
            )
        lines.append("")

    if "bottleneck" in tasks:
        lines.extend(
            [
                "## bottleneck",
                "",
                "| method | test accuracy | test balanced | shift accuracy | shift balanced |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for method, result in tasks["bottleneck"]["metrics"].items():
            lines.append(
                f"| {method} | {_metric_cell(result, 'test', 'accuracy')} | "
                f"{_metric_cell(result, 'test', 'balanced_accuracy')} | "
                f"{_metric_cell(result, 'shift', 'accuracy')} | "
                f"{_metric_cell(result, 'shift', 'balanced_accuracy')} |"
            )
        lines.append("")

    if "control-dynamics" in tasks:
        lines.extend(
            [
                "## control-dynamics",
                "",
                "| method | test MSE | test cosine |",
                "|---|---:|---:|",
            ]
        )
        for method, result in tasks["control-dynamics"]["metrics"].items():
            lines.append(
                f"| {method} | {_metric_cell(result, 'test', 'mse')} | "
                f"{_metric_cell(result, 'test', 'cosine')} |"
            )
        lines.append("")

    if "expand-control" in tasks:
        lines.extend(
            [
                "## expand-control",
                "",
                "| policy | mean score | success rate | mean reward | path complete |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for policy, result in tasks["expand-control"]["metrics"].items():
            score_ci = result.get("score_ci")
            success_ci = result.get("success_ci")
            lines.append(
                f"| {policy} | {_fmt(result['mean_score'], score_ci)} | "
                f"{_fmt(result['success_rate'], success_ci)} | "
                f"{result['mean_reward']:.2f} | "
                f"{result['path_complete_rate']:.2f} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Caveats",
            "",
            "- The test split is the held-out `extra_gear` combination; shift is",
            "  `shift_gear` with one ore patch and higher rock density.",
            "- Scenario splits are a compositional/shift proxy, not a causal test.",
            "- CIs are bootstrap intervals over test samples or episodes.",
            "- The graph message-passing baseline uses pooled one/two-hop features,",
            "  not an end-to-end GNN.",
            "- Control remains a fixed six-tile construction puzzle.",
            "- This is a benchmark candidate, not a frozen public release yet.",
            "",
        ]
    )
    (out / "suite_report.md").write_text("\n".join(lines), encoding="utf-8")


def run_shared_suite(
    out_dir: str | Path,
    suite: SharedSuiteConfig | None = None,
    config: FactoryConfig | None = None,
) -> dict[str, Any]:
    """Generate shared episodes and evaluate all offline task projections."""

    suite = suite or SharedSuiteConfig()
    config = config or _default_factory_config()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    episodes = generate_shared_dataset(config, suite.plan, suite.episode_config)
    manifest = write_shared_dataset(
        out / "dataset",
        "factory-shared-v0.1",
        episodes,
        {
            "world_version": WORLD_VERSION,
            "config_hash": config_hash(config),
            "factory_config": config.as_dict(),
            "plan_name": suite.plan.name,
            "plan_metadata": suite.plan.metadata,
            "episode_config": asdict(suite.episode_config),
        },
    )

    world = FactoryWorld(config)
    replays_validated = 0
    for episode in episodes:
        validate_replay(
            world,
            {
                "seed": episode.seed,
                "scenario": episode.scenario,
                "sample_ticks": episode.sample_ticks,
                "state_hashes": episode.state_hashes,
                "actions": [],
            },
        )
        replays_validated += 1

    dataset = load_shared_dataset(out / "dataset")
    projections = project_tasks(dataset)
    results: dict[str, Any] = {
        "metadata": {
            "world_version": WORLD_VERSION,
            "fabline_version": __version__,
            "created_at": datetime.now(UTC).isoformat(),
            "config_hash": config_hash(config),
            "plan_name": suite.plan.name,
            "suite_config": asdict(suite),
            "hardware": {
                "machine": platform.machine(),
                "processor": platform.processor() or "unknown",
                "python": platform.python_version(),
            },
            "replays_validated": replays_validated,
        },
        "dataset": manifest,
        "tasks": {},
    }

    for name in ("throughput-vector", "throughput-grid", "throughput-entities"):
        projection = projections[name]
        masks = _split_arrays(projection)
        metrics = evaluate_baselines(
            projection.X[masks["train"]],
            projection.y[masks["train"]],
            projection.X[masks["val"]],
            projection.y[masks["val"]],
            projection.X[masks["test"]],
            projection.y[masks["test"]],
            projection.feature_names,
            include_models=True,
            with_ci=suite.with_ci,
            X_extra=projection.X[masks["shift"]],
            y_extra=projection.y[masks["shift"]],
        )
        if name == "throughput-entities" and projection.graph is not None:
            graph = projection.graph
            graph_extra = {
                key: value[masks["shift"]] for key, value in graph.items()
            }
            metrics.update(
                evaluate_graph_baseline(
                    graph,
                    projection.splits,
                    projection.y,
                    graph_extra=graph_extra,
                    y_extra=projection.y[masks["shift"]],
                )
            )
        results["tasks"][name] = _projection_result(projection, metrics)

    for name in ("next-state", "masked-grid"):
        projection = projections[name]
        masks = _split_arrays(projection)
        metrics = evaluate_next_state_baselines(
            projection.X[masks["train"]],
            projection.y[masks["train"]],
            projection.X[masks["val"]],
            projection.y[masks["val"]],
            projection.X[masks["test"]],
            projection.y[masks["test"]],
            with_ci=suite.with_ci,
            X_extra=projection.X[masks["shift"]],
            y_extra=projection.y[masks["shift"]],
        )
        results["tasks"][name] = _projection_result(projection, metrics)

    projection = projections["bottleneck"]
    masks = _split_arrays(projection)
    metrics = evaluate_classification_baselines(
        projection.X[masks["train"]],
        projection.y[masks["train"]],
        projection.X[masks["val"]],
        projection.y[masks["val"]],
        projection.X[masks["test"]],
        projection.y[masks["test"]],
        with_ci=suite.with_ci,
        X_extra=projection.X[masks["shift"]],
        y_extra=projection.y[masks["shift"]],
    )
    results["tasks"]["bottleneck"] = _projection_result(projection, metrics)

    control_config = ControlConfig(
        episode_ticks=300,
        decision_interval=10,
        build_penalty=0.05,
        success_score=20,
    )
    control_factory = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=300,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        starter_line=False,
    )
    control_metrics = evaluate_control_policies(
        control_factory,
        control_config,
        episodes=suite.control_episodes,
        train_episodes=suite.control_train_episodes,
        seeds=suite.control_seeds,
    )
    results["tasks"]["expand-control"] = {
        "kind": "control",
        "observation": "control",
        "samples": suite.control_episodes * len(suite.control_seeds),
        "metrics": control_metrics,
    }

    transitions = generate_control_transitions(
        control_factory,
        control_config,
        episodes=30,
        seed=0,
    )
    masks = {
        name: transitions.splits == name for name in ("train", "val", "test")
    }
    dynamics_metrics = evaluate_next_state_baselines(
        transitions.X[masks["train"]],
        transitions.y[masks["train"]],
        transitions.X[masks["val"]],
        transitions.y[masks["val"]],
        transitions.X[masks["test"]],
        transitions.y[masks["test"]],
        with_ci=suite.with_ci,
    )
    results["tasks"]["control-dynamics"] = {
        "kind": "self_supervised_action",
        "observation": "control",
        "samples": int(len(transitions.X)),
        "metrics": dynamics_metrics,
    }

    results["metadata"]["duration_seconds"] = time.perf_counter() - started
    (out / "suite_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    _write_report(out, results)
    return results
