"""Counterfactual entity-removal intervention task."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.harness.baselines import (
    GradientBoostingBaseline,
    LinearBaseline,
    MeanBaseline,
    MLPBaseline,
)
from fabline.harness.metrics import regression_metrics
from fabline.obs.vector import VectorObservation
from fabline.tasks.splits import assign_split
from fabline.worlds.factory.actions import Action, ActionOp
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.state import EntityType
from fabline.worlds.factory.world import FactoryWorld

CAUSAL_TASK_ID = "factory.causal.remove.v1"
CAUSAL_TASK_VERSION = "0.1.0"

TYPE_INDEX = {
    EntityType.MINER: 0,
    EntityType.BELT: 1,
    EntityType.FURNACE: 2,
    EntityType.ASSEMBLER: 3,
}


@dataclass(frozen=True)
class CausalConfig:
    episodes: int = 40
    seed_start: int = 57000
    warmup_ticks: int = 100
    episode_ticks: int = 500
    sample_ticks: tuple[int, ...] = (150, 250, 350)
    horizon: int = 100

    def __post_init__(self) -> None:
        if self.episodes <= 0:
            raise ValueError("episodes must be positive")
        if not self.sample_ticks or any(tick <= 0 for tick in self.sample_ticks):
            raise ValueError("sample ticks must be positive")
        if self.horizon <= 0:
            raise ValueError("horizon must be positive")


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )


def _target_features(entity: Any, state: Any) -> np.ndarray:
    type_one_hot = np.zeros(4, dtype=np.float32)
    type_one_hot[TYPE_INDEX.get(entity.type, 1)] = 1.0
    return np.concatenate(
        [
            type_one_hot,
            np.asarray(
                [
                    entity.x / max(1, state.width - 1),
                    entity.y / max(1, state.height - 1),
                    entity.total_input() / 10.0,
                    entity.total_output() / 10.0,
                ],
                dtype=np.float32,
            ),
        ]
    )


def generate_causal(
    cfg: CausalConfig,
) -> dict[str, np.ndarray]:
    config = _config()
    vector = VectorObservation(config)
    state_features: list[np.ndarray] = []
    type_features: list[np.ndarray] = []
    target_a_features: list[np.ndarray] = []
    target_b_features: list[np.ndarray] = []
    labels: list[float] = []
    splits: list[str] = []
    for offset in range(cfg.episodes):
        seed = cfg.seed_start + offset
        split = assign_split(seed)
        rng = random.Random(seed * 104729 + 61)
        world = FactoryWorld(config)
        world.reset(seed, SCENARIOS["gear"])
        world.run_ticks(cfg.warmup_ticks)
        for tick in cfg.sample_ticks:
            if tick <= world.state.tick:
                continue
            world.run_ticks(tick - world.state.tick)
            groups: dict[EntityType, list[Any]] = {}
            for entity in sorted(
                world.state.entities.values(), key=lambda item: item.id
            ):
                if entity.type is EntityType.DEPOT:
                    continue
                groups.setdefault(entity.type, []).append(entity)
            candidates = [
                entities for entities in groups.values() if len(entities) >= 2
            ]
            if not candidates:
                continue
            pair = rng.choice(candidates)
            first, second = rng.sample(pair, 2)
            base_score = world.state.score
            first_clone = world.clone()
            first_clone.apply_action(
                Action(ActionOp.REMOVE, x=first.x, y=first.y)
            )
            first_clone.run_ticks(cfg.horizon)
            second_clone = world.clone()
            second_clone.apply_action(
                Action(ActionOp.REMOVE, x=second.x, y=second.y)
            )
            second_clone.run_ticks(cfg.horizon)
            first_delta = float(first_clone.state.score - base_score)
            second_delta = float(second_clone.state.score - base_score)
            state = world.state
            state_features.append(vector.observe(state))
            type_features.append(_target_features(first, state)[:4])
            target_a_features.append(_target_features(first, state))
            target_b_features.append(_target_features(second, state))
            labels.append(first_delta - second_delta)
            splits.append(split)
    return {
        "state": np.stack(state_features),
        "type": np.stack(type_features),
        "target_a": np.stack(target_a_features),
        "target_b": np.stack(target_b_features),
        "label": np.asarray(labels, dtype=np.float32),
        "split": np.asarray(splits),
    }


class _Protocol(Protocol):
    name: str

    def fit(self, x: np.ndarray, y: np.ndarray) -> None: ...
    def predict(self, x: np.ndarray) -> np.ndarray: ...


def _evaluate(
    data: dict[str, np.ndarray],
    features: np.ndarray,
) -> dict[str, Any]:
    train = data["split"] == "train"
    test = data["split"] == "test"
    if not train.any() or not test.any():
        raise ValueError("causal task needs train and test splits")
    results: dict[str, Any] = {}
    for baseline in (
        MeanBaseline(),
        LinearBaseline(),
        GradientBoostingBaseline(),
        MLPBaseline(),
    ):
        baseline.fit(features[train], data["label"][train])
        pred = baseline.predict(features[test])
        results[baseline.name] = regression_metrics(
            data["label"][test], pred
        )
    return results


def run_causal(cfg: CausalConfig | None = None) -> dict[str, Any]:
    cfg = cfg or CausalConfig()
    data = generate_causal(cfg)
    type_only = np.concatenate([data["state"], data["type"]], axis=1)
    full = np.concatenate(
        [data["state"], data["target_a"], data["target_b"]], axis=1
    )
    return {
        "task": CAUSAL_TASK_ID,
        "config": {
            "episodes": cfg.episodes,
            "seed_start": cfg.seed_start,
            "sample_ticks": list(cfg.sample_ticks),
            "horizon": cfg.horizon,
        },
        "rows": int(len(data["label"])),
        "label_mean": float(np.mean(data["label"])),
        "views": {
            "type_only": _evaluate(data, type_only),
            "target": _evaluate(data, full),
        },
    }


def write_causal_report(out: str | Path, report: dict[str, Any]) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "causal_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Counterfactual removal",
        "",
        f"Rows {report['rows']}; mean delta {report['label_mean']:+.2f}.",
        "",
        "| view | method | R2 | MAE |",
        "|---|---|---:|---:|",
    ]
    for view, methods in report["views"].items():
        for method, metrics in methods.items():
            lines.append(
                f"| {view} | {method} | {metrics['r2']:.4f} | "
                f"{metrics['mae']:.4f} |"
            )
    (out / "causal_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "causal_report.md"
