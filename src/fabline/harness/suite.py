"""The M2 debug task suite: five tasks, one command."""

from __future__ import annotations

import json
import platform
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from fabline import __version__
from fabline.core.hashing import config_hash
from fabline.env.control import (
    CONTROL_TASK_ID,
    CONTROL_TASK_VERSION,
    ControlConfig,
)
from fabline.harness.baselines import (
    evaluate_baselines,
    evaluate_next_state_baselines,
)
from fabline.harness.control import evaluate_control_policies
from fabline.harness.data import LoadedDataset, load_dataset
from fabline.obs.base import build_observation
from fabline.obs.vector import VectorObservation
from fabline.record.writer import write_dataset
from fabline.tasks.meta import manifest_meta
from fabline.tasks.next_state import NextStateConfig, NextStateTask
from fabline.tasks.throughput import ThroughputConfig, ThroughputTask
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.config import FactoryConfig


@dataclass(frozen=True)
class SuiteConfig:
    episodes: int = 20
    seed_start: int = 0
    throughput_horizon: int = 50
    throughput_warmup: int = 100
    throughput_episode_ticks: int = 300
    next_state_warmup: int = 100
    next_state_episode_ticks: int = 300
    control_episodes: int = 5
    control_train_episodes: int = 200
    control_seeds: tuple[int, ...] = (0, 1, 2)

    def __post_init__(self) -> None:
        if self.episodes <= 0:
            raise ValueError("episodes must be positive")
        if self.throughput_episode_ticks <= self.throughput_warmup + self.throughput_horizon:
            raise ValueError("throughput episode is too short")
        if self.next_state_episode_ticks <= self.next_state_warmup:
            raise ValueError("next-state episode is too short")
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


def _split_xy(
    loaded: LoadedDataset,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    splits = np.asarray(loaded.splits)
    train = splits == "train"
    val = splits == "val"
    test = splits == "test"
    if not train.any() or not val.any() or not test.any():
        raise ValueError("suite dataset does not contain train, val, and test")
    return (
        loaded.X[train],
        loaded.y[train],
        loaded.X[val],
        loaded.y[val],
        loaded.X[test],
        loaded.y[test],
    )


def _run_throughput_variant(
    out: Path,
    config: FactoryConfig,
    suite: SuiteConfig,
    observation_name: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    adapter = build_observation(observation_name, config)
    task = ThroughputTask(
        config,
        ThroughputConfig(
            horizon=suite.throughput_horizon,
            warmup_ticks=suite.throughput_warmup,
            episode_ticks=suite.throughput_episode_ticks,
        ),
        adapter,
    )
    episodes = task.generate(suite.episodes, suite.seed_start)
    dataset_dir = out / "datasets" / f"throughput-{observation_name}"
    write_dataset(
        dataset_dir,
        f"m2-throughput-{observation_name}",
        episodes,
        manifest_meta(config, task, adapter, "future_score"),
    )
    loaded = load_dataset(dataset_dir)
    X_train, y_train, X_val, y_val, X_test, y_test = _split_xy(loaded)
    metrics = evaluate_baselines(
        X_train,
        y_train,
        X_val,
        y_val,
        X_test,
        y_test,
        loaded.feature_names,
        include_models=True,
    )
    return {
        "kind": "supervised",
        "task_id": task.id,
        "task_version": task.version,
        "observation": observation_name,
        "episodes": len(episodes),
        "samples": int(len(loaded.y)),
        "seed_start": suite.seed_start,
        "duration_seconds": time.perf_counter() - started,
        "metrics": metrics,
    }


def _run_next_state(
    out: Path,
    config: FactoryConfig,
    suite: SuiteConfig,
) -> dict[str, Any]:
    started = time.perf_counter()
    adapter = VectorObservation(config)
    task = NextStateTask(
        config,
        NextStateConfig(
            warmup_ticks=suite.next_state_warmup,
            episode_ticks=suite.next_state_episode_ticks,
        ),
        adapter,
    )
    episodes = task.generate(suite.episodes, suite.seed_start)
    dataset_dir = out / "datasets" / "next-state"
    write_dataset(
        dataset_dir,
        "m2-next-state",
        episodes,
        manifest_meta(config, task, adapter, "next_observation"),
    )
    loaded = load_dataset(dataset_dir)
    X_train, y_train, X_val, y_val, X_test, y_test = _split_xy(loaded)
    metrics = evaluate_next_state_baselines(
        X_train,
        y_train,
        X_val,
        y_val,
        X_test,
        y_test,
    )
    return {
        "kind": "self_supervised",
        "task_id": task.id,
        "task_version": task.version,
        "observation": "vector",
        "episodes": len(episodes),
        "samples": int(len(loaded.y)),
        "seed_start": suite.seed_start,
        "duration_seconds": time.perf_counter() - started,
        "metrics": metrics,
    }


def _run_control(suite: SuiteConfig) -> dict[str, Any]:
    started = time.perf_counter()
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
    metrics = evaluate_control_policies(
        control_factory,
        control_config,
        episodes=suite.control_episodes,
        train_episodes=suite.control_train_episodes,
        seeds=suite.control_seeds,
    )
    return {
        "kind": "control",
        "task_id": CONTROL_TASK_ID,
        "task_version": CONTROL_TASK_VERSION,
        "observation": "control",
        "episodes": suite.control_episodes * len(suite.control_seeds),
        "samples": 0,
        "seeds": list(suite.control_seeds),
        "train_episodes": suite.control_train_episodes,
        "duration_seconds": time.perf_counter() - started,
        "metrics": metrics,
    }


def _write_report(out: Path, results: dict[str, Any]) -> None:
    tasks = results["tasks"]
    metadata = results["metadata"]
    hardware = metadata["hardware"]
    lines = [
        "# M2 task suite report",
        "",
        "This is a debug suite, not a frozen research benchmark.",
        "",
        "## Run metadata",
        "",
        f"- world: `{metadata['world_version']}`",
        f"- fabline: `{metadata['fabline_version']}`",
        f"- factory config hash: `{metadata['factory_config_hash']}`",
        f"- machine: `{hardware['machine']}` / `{hardware['processor']}`",
        f"- python: `{hardware['python']}`",
        f"- total duration: {metadata['duration_seconds']:.2f} s",
        "",
        "## Tasks",
        "",
        "| task | kind | observation | episodes | samples | duration (s) |",
        "|---|---|---|---:|---:|---:|",
    ]
    for name, payload in tasks.items():
        lines.append(
            f"| {name} | {payload['kind']} | {payload['observation']} | "
            f"{payload['episodes']} | {payload['samples']} | "
            f"{payload['duration_seconds']:.2f} |"
        )
    lines.append("")

    for name, payload in tasks.items():
        if payload["kind"] != "supervised":
            continue
        lines.extend(
            [
                f"## {name}",
                "",
                "| method | val MAE | val RMSE | val R² | test MAE | test RMSE | test R² |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for method, result in payload["metrics"].items():
            if "skipped" in result:
                lines.append(f"| {method} | — | — | — | — | — | — |")
                continue
            val = result["val"]
            test = result["test"]
            lines.append(
                f"| {method} | {val['mae']:.4f} | {val['rmse']:.4f} | "
                f"{val['r2']:.4f} | {test['mae']:.4f} | {test['rmse']:.4f} | "
                f"{test['r2']:.4f} |"
            )
        lines.append("")

    for name, payload in tasks.items():
        if payload["kind"] != "self_supervised":
            continue
        lines.extend(
            [
                f"## {name}",
                "",
                "| method | val MSE | val cosine | test MSE | test cosine |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for method, result in payload["metrics"].items():
            val = result["val"]
            test = result["test"]
            lines.append(
                f"| {method} | {val['mse']:.6f} | {val['cosine']:.4f} | "
                f"{test['mse']:.6f} | {test['cosine']:.4f} |"
            )
        lines.append("")

    for name, payload in tasks.items():
        if payload["kind"] != "control":
            continue
        lines.extend(
            [
                f"## {name}",
                "",
                "| policy | mean score | success rate | mean reward | path complete |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for policy, result in payload["metrics"].items():
            lines.append(
                f"| {policy} | {result['mean_score']:.2f} | "
                f"{result['success_rate']:.2f} | {result['mean_reward']:.2f} | "
                f"{result['path_complete_rate']:.2f} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Caveats",
            "",
            "- This suite uses small debug budgets and a 16×8 world.",
            "- Baselines are not tuned; they prove the pipeline.",
            "- Tabular Q-learning is seed-sensitive; the control table pools seeds.",
            "- The graph observation is flattened for tabular baselines; a GNN is future work.",
            "- Do not compare these numbers to a frozen benchmark release.",
            "",
        ]
    )
    (out / "suite_report.md").write_text("\n".join(lines), encoding="utf-8")


def run_suite(
    out_dir: str | Path,
    suite: SuiteConfig | None = None,
    config: FactoryConfig | None = None,
) -> dict[str, Any]:
    """Run the five-task M2 debug suite and write a report."""

    suite = suite or SuiteConfig()
    config = config or _default_factory_config()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    results: dict[str, Any] = {
        "metadata": {
            "world_version": WORLD_VERSION,
            "fabline_version": __version__,
            "created_at": datetime.now(UTC).isoformat(),
            "factory_config": config.as_dict(),
            "factory_config_hash": config_hash(config),
            "suite_config": asdict(suite),
            "hardware": {
                "machine": platform.machine(),
                "processor": platform.processor() or "unknown",
                "python": platform.python_version(),
            },
        },
        "tasks": {},
    }

    for observation_name in ("vector", "grid", "entities"):
        results["tasks"][f"throughput-{observation_name}"] = _run_throughput_variant(
            out,
            config,
            suite,
            observation_name,
        )

    results["tasks"]["next-state"] = _run_next_state(out, config, suite)
    results["tasks"]["expand-control"] = _run_control(suite)
    results["metadata"]["duration_seconds"] = time.perf_counter() - started

    (out / "suite_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    _write_report(out, results)
    return results
