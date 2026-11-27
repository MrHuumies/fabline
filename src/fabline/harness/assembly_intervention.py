"""Counterfactual recipe-switch intervention on the assembly-edge cell.

Each sample is an assembly-cell state at a decision step. The treatment forces
the opposite recipe on the assembly assembler and holds it for the rest of the
episode. The control continues the behaviour policy from the same state. The
effect is the treatment terminal score minus the factual terminal score.

The factual episode is simulated once. Each treatment branch starts from a
clone of the state at the sample step. This is a public effect-estimation task,
not a new control policy.
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
from fabline.harness.baselines import (
    GradientBoostingBaseline,
    evaluate_baselines,
)
from fabline.harness.metrics import test_r2
from fabline.harness.stats import bootstrap_cluster_mean_ci
from fabline.tasks.splits import assign_split
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import EntityType
from fabline.worlds.factory.world import FactoryWorld

ASSEMBLY_INTERVENTION_TASK_ID = "factory.assembly.recipe_intervention.v1"
ASSEMBLY_INTERVENTION_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class AssemblyInterventionConfig:
    episodes: int = 200
    seed_start: int = 58000
    sample_steps: tuple[int, ...] = (10, 20, 30, 40)
    warmup_steps: int = 5
    random_action_prob: float = 0.3
    success_score: int = 100

    def __post_init__(self) -> None:
        if self.episodes <= 0:
            raise ValueError("episodes must be positive")
        if self.warmup_steps < 0:
            raise ValueError("warmup_steps must be non-negative")
        if not self.sample_steps:
            raise ValueError("sample_steps must be non-empty")
        if any(step <= self.warmup_steps for step in self.sample_steps):
            raise ValueError("sample steps must be after warmup")
        if not 0.0 <= self.random_action_prob < 1.0:
            raise ValueError("random_action_prob must be in [0, 1)")


@dataclass
class AssemblyInterventionDataset:
    X: np.ndarray
    effect: np.ndarray
    outcome_switch: np.ndarray
    outcome_continue: np.ndarray
    splits: np.ndarray
    episode_ids: np.ndarray


def _hold_score(
    world: FactoryWorld,
    action: int,
    *,
    ticks: int,
) -> float:
    clone = world.clone()
    assembler = next(
        entity
        for entity in clone.state.entities.values()
        if entity.type is EntityType.ASSEMBLER and entity.x == 7
    )
    assembler.recipe = 0 if action == 0 else 2
    clone.run_ticks(ticks)
    return float(clone.state.score)


def _behavior_action(
    policy: BatchPolicy,
    observation: np.ndarray,
    info: dict[str, Any],
    rng: random.Random,
    random_action_prob: float,
) -> int:
    action = policy.act(observation, info)
    if rng.random() < random_action_prob:
        return rng.randrange(2)
    return action


def generate_intervention_dataset(
    config: FactoryConfig,
    cfg: AssemblyInterventionConfig | None = None,
) -> AssemblyInterventionDataset:
    task = cfg or AssemblyInterventionConfig()
    total_steps = config.ticks_per_episode // config.decision_interval
    if max(task.sample_steps) >= total_steps:
        raise ValueError("sample steps must be inside the episode")
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
    effects: list[float] = []
    switch_outcomes: list[float] = []
    continue_outcomes: list[float] = []
    splits: list[str] = []
    episode_ids: list[int] = []
    for offset in range(task.episodes):
        seed = task.seed_start + offset
        split = assign_split(seed)
        rng = random.Random(seed * 104_729 + 71)
        observation, info = env.reset(seed=seed)
        pending: list[tuple[np.ndarray, float]] = []
        for sample_step in task.sample_steps:
            while env.steps < sample_step and not env.world.done:
                action = _behavior_action(
                    policy,
                    observation,
                    info,
                    rng,
                    task.random_action_prob,
                )
                observation, _, terminated, truncated, info = env.step(action)
                if terminated or truncated:
                    break
            if env.world.done or env.steps != sample_step:
                break
            ticks_left = config.ticks_per_episode - env.world.state.tick
            if ticks_left <= 0:
                break
            current_recipe = int(info["recipe"])
            switch_action = 0 if current_recipe == 2 else 1
            pending.append(
                (
                    observation.copy(),
                    _hold_score(env.world, switch_action, ticks=ticks_left),
                )
            )
        while not env.world.done:
            action = _behavior_action(
                policy,
                observation,
                info,
                rng,
                task.random_action_prob,
            )
            observation, _, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
        factual_score = float(env.world.state.score)
        for features, switch_score in pending:
            rows.append(features)
            effects.append(switch_score - factual_score)
            switch_outcomes.append(switch_score)
            continue_outcomes.append(factual_score)
            splits.append(split)
            episode_ids.append(seed)
    if not rows:
        raise RuntimeError("no intervention samples were generated")
    return AssemblyInterventionDataset(
        X=np.stack(rows),
        effect=np.asarray(effects, dtype=np.float32),
        outcome_switch=np.asarray(switch_outcomes, dtype=np.float32),
        outcome_continue=np.asarray(continue_outcomes, dtype=np.float32),
        splits=np.asarray(splits, dtype=object),
        episode_ids=np.asarray(episode_ids, dtype=np.int64),
    )


def _decision_metrics(
    dataset: AssemblyInterventionDataset,
    predictions: np.ndarray,
    mask: np.ndarray,
) -> dict[str, Any]:
    switch = dataset.outcome_switch[mask]
    cont = dataset.outcome_continue[mask]
    choose_switch = predictions > 0.0
    chosen = np.where(choose_switch, switch, cont)
    oracle = np.maximum(switch, cont)
    always_switch = float(np.mean(switch))
    always_continue = float(np.mean(cont))
    policy_value = float(np.mean(chosen))
    oracle_value = float(np.mean(oracle))
    baseline_value = max(always_switch, always_continue)
    oracle_gain = oracle_value - baseline_value
    model_gain = policy_value - baseline_value
    return {
        "policy_value": policy_value,
        "policy_value_ci": list(
            bootstrap_cluster_mean_ci(
                chosen.tolist(), dataset.episode_ids[mask].tolist()
            )
        ),
        "oracle_value": oracle_value,
        "always_switch": always_switch,
        "always_continue": always_continue,
        "regret": oracle_value - policy_value,
        "oracle_gain": oracle_gain,
        "model_gain": model_gain,
        "gain_fraction": model_gain / oracle_gain if oracle_gain > 0 else 0.0,
        "choose_switch_rate": float(np.mean(choose_switch)),
    }


def run_assembly_intervention(
    config: FactoryConfig,
    cfg: AssemblyInterventionConfig | None = None,
) -> dict[str, Any]:
    task = cfg or AssemblyInterventionConfig()
    dataset = generate_intervention_dataset(config, task)
    train = dataset.splits == "train"
    val = dataset.splits == "val"
    test = dataset.splits == "test"
    if not train.any() or not test.any():
        raise RuntimeError("intervention task needs train and test splits")
    metrics = evaluate_baselines(
        dataset.X[train],
        dataset.effect[train],
        dataset.X[val],
        dataset.effect[val],
        dataset.X[test],
        dataset.effect[test],
        ASSEMBLY_FEATURES,
        include_models=True,
        with_ci=True,
    )
    linear = test_r2(metrics, "linear")
    gbdt = test_r2(metrics, "gbdt")
    mlp = test_r2(metrics, "mlp")
    model = GradientBoostingBaseline()
    model.fit(dataset.X[train], dataset.effect[train])
    predictions = model.predict(dataset.X[test])
    decisions = _decision_metrics(dataset, predictions, test)
    gates = {
        "H1_skill": gbdt >= 0.30,
        "H2_nonlinear": gbdt >= linear + 0.05,
        "H3_not_saturated": gbdt < 0.98,
        "H4_decision": (
            decisions["model_gain"] >= 0.5 * decisions["oracle_gain"]
            and decisions["model_gain"] >= 0.5
        ),
        "H5_mlp_skill": mlp >= 0.20,
    }
    return {
        "task": {
            "id": ASSEMBLY_INTERVENTION_TASK_ID,
            "version": ASSEMBLY_INTERVENTION_TASK_VERSION,
            "kind": "causal-effect",
        },
        "config": asdict(task),
        "dataset": {
            "episodes": int(len(set(dataset.episode_ids.tolist()))),
            "samples": int(len(dataset.effect)),
            "splits": {
                split: int((dataset.splits == split).sum())
                for split in ("train", "val", "test")
            },
            "effect_mean": float(dataset.effect.mean()),
            "effect_std": float(dataset.effect.std()),
            "positive_effect_rate": float((dataset.effect > 0).mean()),
        },
        "metrics": metrics,
        "decisions": decisions,
        "gates": gates,
        "diagnostic": not all(gates.values()),
    }


def write_assembly_intervention_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "assembly_intervention_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    decisions = report["decisions"]
    lines = [
        "# Assembly recipe intervention",
        "",
        f"Task: `{report['task']['id']}` / `{report['task']['version']}`",
        "",
        f"- episodes: {report['dataset']['episodes']}",
        f"- samples: {report['dataset']['samples']}",
        f"- splits: {report['dataset']['splits']}",
        f"- mean effect: {report['dataset']['effect_mean']:+.2f}",
        f"- positive effect rate: "
        f"{report['dataset']['positive_effect_rate']:.2f}",
        "",
        "| model | test R² | test MAE |",
        "|---|---:|---:|",
    ]
    for name, row in report["metrics"].items():
        if "test" not in row:
            continue
        lines.append(
            f"| {name} | {row['test']['r2']:.4f} | {row['test']['mae']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Decision quality",
            "",
            "| policy | value | 95% CI |",
            "|---|---:|---:|",
            f"| oracle | {decisions['oracle_value']:.2f} | — |",
            f"| model (gbdt) | {decisions['policy_value']:.2f} | "
            f"[{decisions['policy_value_ci'][0]:.2f}, "
            f"{decisions['policy_value_ci'][1]:.2f}] |",
            f"| always switch | {decisions['always_switch']:.2f} | — |",
            f"| always continue | {decisions['always_continue']:.2f} | — |",
            "",
            f"Model switches on "
            f"{decisions['choose_switch_rate']:.2f} of test states; "
            f"gain {decisions['model_gain']:+.2f} of "
            f"{decisions['oracle_gain']:+.2f} oracle gain "
            f"({decisions['gain_fraction']:.2f}); "
            f"regret {decisions['regret']:.2f}.",
            "",
            "## Gates",
            "",
            "| Gate | Result |",
            "|---|---|",
        ]
    )
    for name, value in report["gates"].items():
        lines.append(f"| {name} | {value} |")
    lines.append("")
    (out / "assembly_intervention_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "assembly_intervention_report.md"
