"""BOM forecast on the assembly-edge production cell.

The task predicts future gear output over a short horizon from the current
assembly-cell state. Episodes are logged with an epsilon-random policy, so the
future decisions are not observable from the state at prediction time. This
gives the forecast irreducible decision uncertainty instead of a deterministic
one-step replay.

It is a public regression task for the component/assembly interface, not a new
control policy.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.assembly import (
    ASSEMBLY_FEATURES,
    AssemblyControlConfig,
    AssemblyControlEnv,
)
from fabline.harness.assembly_control import BatchPolicy
from fabline.harness.baselines import evaluate_baselines
from fabline.harness.metrics import test_r2
from fabline.worlds.factory.config import FactoryConfig

ASSEMBLY_BOM_TASK_ID = "factory.assembly.bom.v1"
ASSEMBLY_BOM_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class AssemblyBOMConfig:
    episodes: int = 50
    warmup_steps: int = 5
    horizon_steps: int = 5
    train_fraction: float = 0.6
    val_fraction: float = 0.2
    success_score: int = 100
    random_action_prob: float = 0.3

    def __post_init__(self) -> None:
        if self.episodes < 3:
            raise ValueError("episodes must allow train/val/test splits")
        if self.warmup_steps < 0:
            raise ValueError("warmup_steps must be non-negative")
        if self.horizon_steps <= 0:
            raise ValueError("horizon_steps must be positive")
        if not 0.0 < self.train_fraction < 1.0:
            raise ValueError("train_fraction must be in (0, 1)")
        if not 0.0 <= self.val_fraction < 1.0:
            raise ValueError("val_fraction must be in [0, 1)")
        if self.train_fraction + self.val_fraction >= 1.0:
            raise ValueError("train and val fractions must leave a test split")
        if not 0.0 <= self.random_action_prob < 1.0:
            raise ValueError("random_action_prob must be in [0, 1)")


@dataclass
class AssemblyBOMDataset:
    X: np.ndarray
    y: np.ndarray
    splits: np.ndarray
    episode_ids: np.ndarray


def _split_for_episode(
    position: int,
    total: int,
    cfg: AssemblyBOMConfig,
) -> str:
    train_end = max(1, int(total * cfg.train_fraction))
    val_end = max(train_end + 1, int(total * (cfg.train_fraction + cfg.val_fraction)))
    if position < train_end:
        return "train"
    if position < val_end:
        return "val"
    return "test"


def generate_bom_dataset(
    config: FactoryConfig,
    cfg: AssemblyBOMConfig | None = None,
) -> AssemblyBOMDataset:
    task = cfg or AssemblyBOMConfig()
    env = AssemblyControlEnv(
        config,
        AssemblyControlConfig(
            episode_ticks=config.ticks_per_episode,
            decision_interval=config.decision_interval,
            success_score=task.success_score,
        ),
    )
    policy = BatchPolicy(threshold=3)
    rows: list[np.ndarray] = []
    labels: list[float] = []
    splits: list[str] = []
    episode_ids: list[int] = []
    total_steps = env.assembly.episode_ticks // env.assembly.decision_interval
    for episode in range(task.episodes):
        seed = episode
        rng = random.Random(seed * 104_729 + 7)
        observation, info = env.reset(seed=seed)
        observations: list[np.ndarray] = []
        delivered: list[float] = []
        for step in range(total_steps):
            if step >= task.warmup_steps:
                observations.append(observation.copy())
                delivered.append(float(info["delivered_gear"]))
            action = policy.act(observation, info)
            if rng.random() < task.random_action_prob:
                action = rng.randrange(env.n_actions)
            observation, _, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
        for index in range(len(observations) - task.horizon_steps):
            rows.append(observations[index])
            labels.append(
                delivered[index + task.horizon_steps] - delivered[index]
            )
            splits.append(
                _split_for_episode(episode, task.episodes, task)
            )
            episode_ids.append(seed)
    if not rows:
        raise RuntimeError("no BOM samples were generated")
    return AssemblyBOMDataset(
        X=np.stack(rows),
        y=np.asarray(labels, dtype=np.float32),
        splits=np.asarray(splits, dtype=object),
        episode_ids=np.asarray(episode_ids, dtype=np.int64),
    )


def run_assembly_bom(
    config: FactoryConfig,
    cfg: AssemblyBOMConfig | None = None,
) -> dict[str, Any]:
    task = cfg or AssemblyBOMConfig()
    dataset = generate_bom_dataset(config, task)
    train = dataset.splits == "train"
    val = dataset.splits == "val"
    test = dataset.splits == "test"
    metrics = evaluate_baselines(
        dataset.X[train],
        dataset.y[train],
        dataset.X[val],
        dataset.y[val],
        dataset.X[test],
        dataset.y[test],
        ASSEMBLY_FEATURES,
        include_models=True,
        with_ci=True,
    )
    linear = test_r2(metrics, "linear")
    gbdt = test_r2(metrics, "gbdt")
    mlp = test_r2(metrics, "mlp")
    gates = {
        "H1_skill": gbdt >= 0.30,
        "H2_nonlinear": gbdt >= linear + 0.05,
        "H3_not_saturated": gbdt < 0.98,
        "H4_mlp_skill": mlp >= 0.20,
    }
    return {
        "task": {
            "id": ASSEMBLY_BOM_TASK_ID,
            "version": ASSEMBLY_BOM_TASK_VERSION,
            "kind": "regression",
        },
        "config": asdict(task),
        "dataset": {
            "episodes": int(len(set(dataset.episode_ids.tolist()))),
            "samples": int(len(dataset.y)),
            "splits": {
                split: int((dataset.splits == split).sum())
                for split in ("train", "val", "test")
            },
            "label_mean": float(dataset.y.mean()),
            "label_std": float(dataset.y.std()),
        },
        "metrics": metrics,
        "gates": gates,
        "diagnostic": not all(gates.values()),
    }


def write_assembly_bom_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "assembly_bom_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Assembly BOM forecast",
        "",
        f"Task: `{report['task']['id']}` / `{report['task']['version']}`",
        "",
        f"- episodes: {report['dataset']['episodes']}",
        f"- samples: {report['dataset']['samples']}",
        f"- splits: {report['dataset']['splits']}",
        "",
        "| model | test R² | test MAE |",
        "|---|---:|---:|",
    ]
    for name, row in report["metrics"].items():
        if "test" not in row:
            lines.append(f"| {name} | — | — |")
            continue
        lines.append(
            f"| {name} | {row['test']['r2']:.4f} | {row['test']['mae']:.4f} |"
        )
    lines.extend(["", "## Gates", "", "| Gate | Result |", "|---|---|"])
    for name, value in report["gates"].items():
        lines.append(f"| {name} | {value} |")
    lines.append("")
    (out / "assembly_bom_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "assembly_bom_report.md"
