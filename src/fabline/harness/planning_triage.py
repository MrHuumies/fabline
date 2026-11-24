"""Planning and learned-model baselines on three-bridge triage."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.crew_replan import CREW_REPLAN_FEATURES, CrewReplanConfig, CrewReplanEnv
from fabline.harness.crew_replan import (
    ParallelGreedyPolicy,
    RecallAwarePolicy,
    evaluate_policy,
)
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig

INITIAL_ACTIONS = tuple(range(16))
REPLAN_ACTIONS = (0, 4, 8, 12)


@dataclass(frozen=True)
class TriagePlanningConfig:
    population: int = 32
    elites: int = 8
    iterations: int = 6
    random_samples: int = 128
    model_seeds: int = 8
    model_sequences: int = 300

    def __post_init__(self) -> None:
        if self.population <= 0 or self.elites <= 0:
            raise ValueError("population and elites must be positive")
        if self.elites > self.population:
            raise ValueError("elites cannot exceed population")
        if self.iterations <= 0 or self.random_samples <= 0:
            raise ValueError("iterations and random samples must be positive")
        if self.model_seeds <= 0:
            raise ValueError("model seeds must be positive")
        if self.model_sequences <= 0:
            raise ValueError("model sequences must be positive")


def _factory_config() -> FactoryConfig:
    return FactoryConfig(
        width=32,
        height=16,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )


def _replan_config() -> CrewReplanConfig:
    return CrewReplanConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=90,
        small_failure_tick=110,
        large_failure_tick=130,
        recall_tick=100,
        job_failure_tick=100,
        replan_jobs=2,
        role_mode="three_positive",
        replan_mode="all_positive",
        success_score=300,
        randomize_crew_b=True,
        crew_b_min_distance=8,
        scenario="random_gear",
        power=PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=24,
            generator_radius=8,
            wire_redundancy=2,
        ),
    )


def _run_sequence(
    env: CrewReplanEnv,
    sequence: tuple[int, int, int],
    seed: int,
) -> tuple[float, np.ndarray]:
    observation, _ = env.reset(seed)
    initial = observation.copy()
    terminated = False
    truncated = False
    info: dict[str, Any] = {}
    while not (terminated or truncated) and info.get("tick", 0) < env.replan.warning_tick:
        observation, _, terminated, truncated, info = env.step(0)
    if not (terminated or truncated):
        action = sequence[0] if env.action_mask()[sequence[0]] else 0
        observation, _, terminated, truncated, info = env.step(action)
    if not (terminated or truncated) and info["phase"] == "replan":
        action = sequence[1] if env.action_mask()[sequence[1]] else 0
        observation, _, terminated, truncated, info = env.step(action)
    if not (terminated or truncated) and info["phase"] == "replan":
        action = sequence[2] if env.action_mask()[sequence[2]] else 0
        observation, _, terminated, truncated, info = env.step(action)
    while not (terminated or truncated):
        observation, _, terminated, truncated, info = env.step(0)
    return float(info["score"]), initial


def _random_sequence(rng: random.Random) -> tuple[int, int, int]:
    return (
        rng.choice(INITIAL_ACTIONS),
        rng.choice(REPLAN_ACTIONS),
        rng.choice(REPLAN_ACTIONS),
    )


def _encode(initial: np.ndarray, sequence: tuple[int, int, int]) -> np.ndarray:
    vector = np.zeros(16 + 4 + 4, dtype=np.float64)
    vector[sequence[0]] = 1.0
    vector[16 + REPLAN_ACTIONS.index(sequence[1])] = 1.0
    vector[20 + REPLAN_ACTIONS.index(sequence[2])] = 1.0
    return np.concatenate([initial, vector])


class RidgeModel:
    def __init__(self, ridge: float = 1.0) -> None:
        self.ridge = ridge
        self.mean: np.ndarray | None = None
        self.scale: np.ndarray | None = None
        self.weights: np.ndarray | None = None

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        self.mean = x.mean(axis=0)
        self.scale = x.std(axis=0)
        self.scale[self.scale < 1e-6] = 1.0
        design = (x - self.mean) / self.scale
        design = np.concatenate([design, np.ones((len(design), 1))], axis=1)
        gram = design.T @ design + self.ridge * np.eye(design.shape[1])
        self.weights = np.linalg.solve(gram, design.T @ y)

    def predict(self, x: np.ndarray) -> np.ndarray:
        if self.mean is None or self.scale is None or self.weights is None:
            raise RuntimeError("model is not fitted")
        design = (x - self.mean) / self.scale
        design = np.concatenate([design, np.ones((len(design), 1))], axis=1)
        return np.asarray(design @ self.weights)


def _collect_model_data(
    env: CrewReplanEnv,
    cfg: TriagePlanningConfig,
    seed_start: int,
) -> tuple[np.ndarray, np.ndarray]:
    x_rows: list[np.ndarray] = []
    y_rows: list[float] = []
    for offset in range(cfg.model_seeds):
        seed = seed_start + offset
        for initial_action in INITIAL_ACTIONS:
            for first in REPLAN_ACTIONS:
                for second in REPLAN_ACTIONS:
                    sequence = (initial_action, first, second)
                    score, initial = _run_sequence(env, sequence, seed)
                    x_rows.append(_encode(initial, sequence))
                    y_rows.append(score)
    return np.stack(x_rows), np.asarray(y_rows, dtype=np.float64)


def _sample_sequence(
    rng: random.Random,
    probabilities: list[np.ndarray],
) -> tuple[int, int, int]:
    initial = int(rng.choices(range(16), weights=probabilities[0].tolist())[0])
    first = int(rng.choices(range(4), weights=probabilities[1].tolist())[0])
    second = int(rng.choices(range(4), weights=probabilities[2].tolist())[0])
    return initial, REPLAN_ACTIONS[first], REPLAN_ACTIONS[second]


def _cem(
    env: CrewReplanEnv,
    seed: int,
    cfg: TriagePlanningConfig,
    rng: random.Random,
    model: RidgeModel | None,
    initial_observation: np.ndarray | None = None,
) -> tuple[float, tuple[int, int, int], float]:
    probabilities = [
        np.ones(16) / 16.0,
        np.ones(4) / 4.0,
        np.ones(4) / 4.0,
    ]
    best_score = -1.0
    best_sequence = (0, 0, 0)
    start = time.perf_counter()
    for _ in range(cfg.iterations):
        population: list[tuple[float, tuple[int, int, int]]] = []
        for _ in range(cfg.population):
            sequence = _sample_sequence(rng, probabilities)
            if model is None:
                score, _ = _run_sequence(env, sequence, seed)
            else:
                if initial_observation is None:
                    raise RuntimeError("model planning needs an initial observation")
                score = float(
                    model.predict(
                        _encode(initial_observation, sequence).reshape(1, -1)
                    )[0]
                )
            population.append((score, sequence))
            if score > best_score:
                best_score = score
                best_sequence = sequence
        population.sort(reverse=True, key=lambda item: item[0])
        elites = population[: cfg.elites]
        for variable, size in enumerate((16, 4, 4)):
            counts = np.ones(size, dtype=np.float64)
            for _, sequence in elites:
                if variable == 0:
                    choice = sequence[0]
                elif variable == 1:
                    choice = REPLAN_ACTIONS.index(sequence[1])
                else:
                    choice = REPLAN_ACTIONS.index(sequence[2])
                counts[choice] += 1.0
            probabilities[variable] = counts / counts.sum()
    if model is not None:
        true_score, _ = _run_sequence(env, best_sequence, seed)
    else:
        true_score = best_score
    return true_score, best_sequence, time.perf_counter() - start


def _random_shooting(
    env: CrewReplanEnv,
    seed: int,
    cfg: TriagePlanningConfig,
    rng: random.Random,
) -> tuple[float, tuple[int, int, int], float]:
    best_score = -1.0
    best_sequence = (0, 0, 0)
    start = time.perf_counter()
    for _ in range(cfg.random_samples):
        sequence = _random_sequence(rng)
        score, _ = _run_sequence(env, sequence, seed)
        if score > best_score:
            best_score = score
            best_sequence = sequence
    return best_score, best_sequence, time.perf_counter() - start


def run_triage_planning(
    cfg: TriagePlanningConfig | None = None,
    *,
    seeds: tuple[int, ...] = (0, 1, 2),
    model_seed_start: int = 50000,
) -> dict[str, Any]:
    cfg = cfg or TriagePlanningConfig()
    env = CrewReplanEnv(_factory_config(), _replan_config())
    rng = random.Random(20261124)

    train_x, train_y = _collect_model_data(env, cfg, model_seed_start)
    model = RidgeModel()
    model.fit(train_x, train_y)
    eval_x, eval_y = _collect_model_data(env, cfg, model_seed_start + 1000)
    model_mse = float(np.mean((model.predict(eval_x) - eval_y) ** 2))

    results: dict[str, dict[str, Any]] = {
        "scripted_greedy": {"scores": [], "sequences": [], "seconds": []},
        "scripted_aware": {"scores": [], "sequences": [], "seconds": []},
        "random": {"scores": [], "sequences": [], "seconds": []},
        "random_shooting_true": {
            "scores": [],
            "sequences": [],
            "seconds": [],
        },
        "cem_true": {"scores": [], "sequences": [], "seconds": []},
        "cem_learned": {"scores": [], "sequences": [], "seconds": []},
        "oracle": {"scores": [], "sequences": [], "seconds": []},
    }
    for seed in seeds:
        for name, policy in (
            ("scripted_greedy", ParallelGreedyPolicy()),
            ("scripted_aware", RecallAwarePolicy()),
        ):
            start = time.perf_counter()
            metrics = evaluate_policy(env, policy, episodes=1, seed=seed)
            results[name]["scores"].append(metrics.mean_score)
            results[name]["sequences"].append([])
            results[name]["seconds"].append(time.perf_counter() - start)

        sequence = _random_sequence(rng)
        start = time.perf_counter()
        score, _ = _run_sequence(env, sequence, seed)
        results["random"]["scores"].append(score)
        results["random"]["sequences"].append(list(sequence))
        results["random"]["seconds"].append(time.perf_counter() - start)

        score, sequence, seconds = _random_shooting(env, seed, cfg, rng)
        results["random_shooting_true"]["scores"].append(score)
        results["random_shooting_true"]["sequences"].append(list(sequence))
        results["random_shooting_true"]["seconds"].append(seconds)

        score, sequence, seconds = _cem(env, seed, cfg, rng, None)
        results["cem_true"]["scores"].append(score)
        results["cem_true"]["sequences"].append(list(sequence))
        results["cem_true"]["seconds"].append(seconds)

        observation, _ = env.reset(seed)
        score, sequence, seconds = _cem(
            env,
            seed,
            cfg,
            rng,
            model,
            observation,
        )
        results["cem_learned"]["scores"].append(score)
        results["cem_learned"]["sequences"].append(list(sequence))
        results["cem_learned"]["seconds"].append(seconds)

        start = time.perf_counter()
        best_score = -1.0
        best_sequence = (0, 0, 0)
        for initial in INITIAL_ACTIONS:
            for first in REPLAN_ACTIONS:
                for second in REPLAN_ACTIONS:
                    sequence = (initial, first, second)
                    score, _ = _run_sequence(env, sequence, seed)
                    if score > best_score:
                        best_score = score
                        best_sequence = sequence
        results["oracle"]["scores"].append(best_score)
        results["oracle"]["sequences"].append(list(best_sequence))
        results["oracle"]["seconds"].append(time.perf_counter() - start)

    summary: dict[str, dict[str, Any]] = {}
    for name, payload in results.items():
        scores = [float(value) for value in payload["scores"]]
        summary[name] = {
            "mean_score": float(np.mean(scores)),
            "score_ci": list(bootstrap_mean_ci(scores)),
            "success_rate": float(
                np.mean([1.0 if value >= 300 else 0.0 for value in scores])
            ),
            "mean_seconds": float(np.mean(payload["seconds"])),
            "scores": scores,
            "sequences": payload["sequences"],
        }
    return {
        "task": "factory.planning.triage.v1",
        "config": {
            "population": cfg.population,
            "elites": cfg.elites,
            "iterations": cfg.iterations,
            "random_samples": cfg.random_samples,
            "model_seeds": cfg.model_seeds,
            "model_sequences": cfg.model_sequences,
        },
        "seeds": list(seeds),
        "model_mse": model_mse,
        "observation_features": len(CREW_REPLAN_FEATURES),
        "results": summary,
    }


def write_triage_planning_report(report: dict[str, Any], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "planning_triage_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Triage planning",
        "",
        f"Model MSE {report['model_mse']:.2f}; "
        f"observation {report['observation_features']} features.",
        "",
        "| policy | mean score | 95% CI | success | seconds |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in report["results"].items():
        lines.append(
            f"| {name} | {row['mean_score']:.2f} "
            f"[{row['score_ci'][0]:.2f}, {row['score_ci'][1]:.2f}] | "
            f"{row['success_rate']:.2f} | {row['mean_seconds']:.2f} |"
        )
    (out / "planning_triage_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
