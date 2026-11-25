"""Transition-model planning on the three-bridge triage task."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.crew_replan import (
    CREW_REPLAN_FEATURES,
    CrewReplanEnv,
)
from fabline.harness.crew_replan import (
    ParallelGreedyPolicy,
    RecallAwarePolicy,
    evaluate_policy,
)
from fabline.harness.planning_triage import (
    INITIAL_ACTIONS,
    REPLAN_ACTIONS,
    TriagePlanningConfig,
    _cem,
    _factory_config,
    _random_shooting,
    _replan_config,
    _run_sequence,
)
from fabline.harness.stats import bootstrap_mean_ci

STATE_DIM = len(CREW_REPLAN_FEATURES)
PHASE_DIM = 3
ACTION_DIM = 20
TRANSITION_DIM = STATE_DIM + PHASE_DIM + ACTION_DIM
SCORE_INDEX = 1


@dataclass(frozen=True)
class TransitionPlanningConfig:
    population: int = 32
    elites: int = 8
    iterations: int = 6
    random_samples: int = 128
    train_seeds: int = 8
    eval_seeds: int = 2
    ridge: float = 1.0
    max_sequences: int = 256
    train_seed_start: int = 52000
    eval_seed_start: int = 53000
    planning_seeds: tuple[int, ...] = (49000, 49001, 49002, 49003, 49004)

    def __post_init__(self) -> None:
        if self.population <= 0 or self.elites <= 0:
            raise ValueError("population and elites must be positive")
        if self.elites > self.population:
            raise ValueError("elites cannot exceed population")
        if self.iterations <= 0 or self.random_samples <= 0:
            raise ValueError("iterations and random samples must be positive")
        if self.train_seeds <= 0 or self.eval_seeds <= 0:
            raise ValueError("train/eval seeds must be positive")
        if self.ridge < 0.0:
            raise ValueError("ridge must be non-negative")
        if not 0 < self.max_sequences <= 256:
            raise ValueError("max_sequences must be in 1..256")
        if not self.planning_seeds:
            raise ValueError("planning seeds must not be empty")

    def triage(self) -> TriagePlanningConfig:
        return TriagePlanningConfig(
            population=self.population,
            elites=self.elites,
            iterations=self.iterations,
            random_samples=self.random_samples,
        )


def _action_index(phase: int, action: int) -> int:
    if phase == 0:
        return action
    return 16 + REPLAN_ACTIONS.index(action)


def _encode(state: np.ndarray, phase: int, action: int) -> np.ndarray:
    encoded = np.zeros(TRANSITION_DIM, dtype=np.float64)
    encoded[:STATE_DIM] = state
    encoded[STATE_DIM + phase] = 1.0
    encoded[STATE_DIM + PHASE_DIM + _action_index(phase, action)] = 1.0
    return encoded


def _advance_to_warning(
    env: CrewReplanEnv,
    seed: int,
) -> tuple[np.ndarray, dict[str, Any], bool]:
    observation, info = env.reset(seed)
    terminated = False
    truncated = False
    while (
        not (terminated or truncated)
        and info.get("tick", 0) < env.replan.warning_tick
    ):
        observation, _, terminated, truncated, info = env.step(0)
    return observation, info, terminated or truncated


def _trace_sequence(
    env: CrewReplanEnv,
    sequence: tuple[int, int, int],
    seed: int,
) -> tuple[float, list[np.ndarray], list[int], list[np.ndarray], list[bool]]:
    """Return score, decision states, actions, next states, and done flags."""

    observation, info, done = _advance_to_warning(env, seed)
    terminated = False
    truncated = False
    states: list[np.ndarray] = []
    actions: list[int] = []
    next_states: list[np.ndarray] = []
    dones: list[bool] = []
    for phase in range(3):
        if done:
            break
        states.append(observation.copy())
        action = sequence[phase]
        if not env.action_mask()[action]:
            action = 0
        actions.append(action)
        observation, _, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        if phase == 2:
            while not done:
                observation, _, terminated, truncated, info = env.step(0)
                done = terminated or truncated
        next_states.append(observation.copy())
        dones.append(done)
        if done:
            break
    return float(info["score"]), states, actions, next_states, dones

def _sequence(initial: int, first: int, second: int) -> tuple[int, int, int]:
    return initial, first, second


def _all_sequences() -> list[tuple[int, int, int]]:
    return [
        _sequence(initial, first, second)
        for initial in INITIAL_ACTIONS
        for first in REPLAN_ACTIONS
        for second in REPLAN_ACTIONS
    ]


def _collect_data(
    env: CrewReplanEnv,
    *,
    seed_start: int,
    episodes: int,
    max_sequences: int = 256,
) -> tuple[np.ndarray, np.ndarray, list[tuple[np.ndarray, list[int], float]]]:
    x_rows: list[np.ndarray] = []
    y_rows: list[np.ndarray] = []
    rollouts: list[tuple[np.ndarray, list[int], float]] = []
    sequences = _all_sequences()[:max_sequences]
    for offset in range(episodes):
        seed = seed_start + offset
        for sequence in sequences:
            score, states, actions, next_states, dones = _trace_sequence(
                env, sequence, seed
            )
            if not states:
                continue
            for phase, (state, action, next_state, done) in enumerate(
                zip(states, actions, next_states, dones, strict=True)
            ):
                delta = next_state - state
                target = np.concatenate(
                    [delta, np.asarray([1.0 if done else 0.0])]
                )
                x_rows.append(_encode(state, phase, action))
                y_rows.append(target)
            rollouts.append((states[0].copy(), list(actions), score))
    return (
        np.stack(x_rows),
        np.stack(y_rows),
        rollouts,
    )

class DeltaTransitionModel:
    """Ridge model of the next decision state."""

    def __init__(self, ridge: float = 1.0) -> None:
        self.ridge = ridge
        self.mean_x: np.ndarray | None = None
        self.scale_x: np.ndarray | None = None
        self.mean_y: np.ndarray | None = None
        self.scale_y: np.ndarray | None = None
        self.weights: np.ndarray | None = None

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        self.mean_x = x.mean(axis=0)
        self.scale_x = x.std(axis=0)
        self.scale_x[self.scale_x < 1e-8] = 1.0
        self.mean_y = y.mean(axis=0)
        self.scale_y = y.std(axis=0)
        self.scale_y[self.scale_y < 1e-8] = 1.0
        design = (x - self.mean_x) / self.scale_x
        design = np.concatenate(
            [design, np.ones((len(design), 1))], axis=1
        )
        target = (y - self.mean_y) / self.scale_y
        gram = design.T @ design + self.ridge * np.eye(design.shape[1])
        self.weights = np.linalg.solve(gram, design.T @ target)

    def predict_delta(self, x: np.ndarray) -> np.ndarray:
        if self.mean_x is None or self.scale_x is None:
            raise RuntimeError("transition model is not fitted")
        if self.mean_y is None or self.scale_y is None:
            raise RuntimeError("transition model is not fitted")
        if self.weights is None:
            raise RuntimeError("transition model is not fitted")
        design = (x - self.mean_x) / self.scale_x
        design = np.concatenate(
            [design, np.ones((len(design), 1))], axis=1
        )
        return np.asarray(design @ self.weights * self.scale_y + self.mean_y)

    def predict_step(
        self,
        state: np.ndarray,
        phase: int,
        action: int,
    ) -> tuple[np.ndarray, bool]:
        encoded = _encode(state, phase, action).reshape(1, -1)
        prediction = self.predict_delta(encoded)[0]
        predicted = state + prediction[:STATE_DIM]
        next_state = np.asarray(
            np.clip(predicted, 0.0, 1.0), dtype=np.float64
        )
        return next_state, bool(prediction[-1] > 0.5)

    def score(self, state: np.ndarray, actions: list[int]) -> float:
        current = state
        for phase, action in enumerate(actions):
            current, done = self.predict_step(current, phase, action)
            if done:
                break
        return float(current[SCORE_INDEX] * 500.0)


def _transition_mse(
    model: DeltaTransitionModel,
    x: np.ndarray,
    y: np.ndarray,
) -> float:
    predicted = model.predict_delta(x)[:, :STATE_DIM]
    return float(np.mean((predicted - y[:, :STATE_DIM]) ** 2))


def _copy_mse(x: np.ndarray, y: np.ndarray) -> float:
    del x
    return float(np.mean(y[:, :STATE_DIM] ** 2))


def _done_accuracy(
    model: DeltaTransitionModel,
    x: np.ndarray,
    y: np.ndarray,
) -> float:
    predicted = model.predict_delta(x)[:, -1] > 0.5
    actual = y[:, -1] > 0.5
    return float(np.mean(predicted == actual))


@dataclass(frozen=True)
class TransitionEnsembleConfig(TransitionPlanningConfig):
    members: int = 8
    beta: float = 1.0
    ensemble_seed: int = 20261125

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.members <= 0:
            raise ValueError("members must be positive")
        if self.beta < 0.0:
            raise ValueError("beta must be non-negative")


class EnsembleTransitionModel:
    """Bootstrap ensemble of ridge delta transition models."""

    def __init__(self, models: list[DeltaTransitionModel]) -> None:
        if not models:
            raise ValueError("an ensemble needs at least one model")
        self.models = models

    @classmethod
    def fit(
        cls,
        x: np.ndarray,
        y: np.ndarray,
        *,
        members: int,
        ridge: float,
        seed: int,
    ) -> EnsembleTransitionModel:
        rng = np.random.default_rng(seed)
        models: list[DeltaTransitionModel] = []
        for _ in range(members):
            indices = rng.integers(0, len(x), len(x))
            model = DeltaTransitionModel(ridge=ridge)
            model.fit(x[indices], y[indices])
            models.append(model)
        return cls(models)

    def score_stats(
        self,
        state: np.ndarray,
        actions: list[int],
    ) -> tuple[float, float]:
        scores = [model.score(state, actions) for model in self.models]
        return float(np.mean(scores)), float(np.std(scores))

    def mean_mse(self, x: np.ndarray, y: np.ndarray) -> float:
        return float(
            np.mean(
                [
                    np.mean(
                        (
                            model.predict_delta(x)[:, :STATE_DIM]
                            - y[:, :STATE_DIM]
                        )
                        ** 2
                    )
                    for model in self.models
                ]
            )
        )

    def mean_done_accuracy(self, x: np.ndarray, y: np.ndarray) -> float:
        return float(
            np.mean(
                [
                    _done_accuracy(model, x, y)
                    for model in self.models
                ]
            )
        )


def _spearman(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0

    def ranks(values: list[float]) -> np.ndarray:
        order = np.argsort(np.argsort(np.asarray(values)))
        return np.asarray(order, dtype=np.float64)

    a = ranks(left)
    b = ranks(right)
    a -= a.mean()
    b -= b.mean()
    denominator = float(np.sqrt(np.sum(a**2) * np.sum(b**2)))
    if denominator <= 0.0:
        return 0.0
    return float(np.sum(a * b) / denominator)


def _ensemble_cem(
    env: CrewReplanEnv,
    seed: int,
    cfg: TriagePlanningConfig,
    rng: random.Random,
    model: EnsembleTransitionModel,
    beta: float,
) -> tuple[float, tuple[int, int, int], float]:
    observation, _, _ = _advance_to_warning(env, seed)
    start_state = observation.copy()
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
            initial = int(
                rng.choices(range(16), weights=probabilities[0].tolist())[0]
            )
            first = int(
                rng.choices(range(4), weights=probabilities[1].tolist())[0]
            )
            second = int(
                rng.choices(range(4), weights=probabilities[2].tolist())[0]
            )
            sequence = (initial, REPLAN_ACTIONS[first], REPLAN_ACTIONS[second])
            actions = [sequence[0], sequence[1], sequence[2]]
            mean, std = model.score_stats(start_state, actions)
            objective = mean - beta * std
            population.append((objective, sequence))
            if objective > best_score:
                best_score = objective
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
    true_score, _ = _run_sequence(env, best_sequence, seed)
    return true_score, best_sequence, time.perf_counter() - start


def _transition_cem(
    env: CrewReplanEnv,
    seed: int,
    cfg: TriagePlanningConfig,
    rng: random.Random,
    model: DeltaTransitionModel,
) -> tuple[float, tuple[int, int, int], float]:
    observation, _, _ = _advance_to_warning(env, seed)
    start_state = observation.copy()
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
            initial = int(
                rng.choices(range(16), weights=probabilities[0].tolist())[0]
            )
            first = int(
                rng.choices(range(4), weights=probabilities[1].tolist())[0]
            )
            second = int(
                rng.choices(range(4), weights=probabilities[2].tolist())[0]
            )
            sequence = (initial, REPLAN_ACTIONS[first], REPLAN_ACTIONS[second])
            predicted = model.score(
                start_state, [sequence[0], sequence[1], sequence[2]]
            )
            population.append((predicted, sequence))
            if predicted > best_score:
                best_score = predicted
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
    true_score, _ = _run_sequence(env, best_sequence, seed)
    return true_score, best_sequence, time.perf_counter() - start


def _oracle(
    env: CrewReplanEnv,
    seed: int,
) -> tuple[float, tuple[int, int, int]]:
    best_score = -1.0
    best_sequence = (0, 0, 0)
    for sequence in _all_sequences():
        score, _ = _run_sequence(env, sequence, seed)
        if score > best_score:
            best_score = score
            best_sequence = sequence
    return best_score, best_sequence


def _summary(scores: list[float]) -> dict[str, Any]:
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "success_rate": float(np.mean([1.0 if score >= 300 else 0.0 for score in scores])),
        "scores": scores,
    }


def run_transition_planning(
    cfg: TransitionPlanningConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or TransitionPlanningConfig()
    triage = cfg.triage()
    env = CrewReplanEnv(_factory_config(), _replan_config())
    train_x, train_y, _ = _collect_data(
        env,
        seed_start=cfg.train_seed_start,
        episodes=cfg.train_seeds,
        max_sequences=cfg.max_sequences,
    )
    model = DeltaTransitionModel(cfg.ridge)
    model.fit(train_x, train_y)
    eval_x, eval_y, eval_rollouts = _collect_data(
        env,
        seed_start=cfg.eval_seed_start,
        episodes=cfg.eval_seeds,
        max_sequences=cfg.max_sequences,
    )
    one_step_mse = _transition_mse(model, eval_x, eval_y)
    copy_mse = _copy_mse(eval_x, eval_y)
    done_accuracy = _done_accuracy(model, eval_x, eval_y)
    rollout_mse = float(
        np.mean(
            [
                (model.score(state, actions) - score) ** 2
                for state, actions, score in eval_rollouts
            ]
        )
    )

    results: dict[str, dict[str, Any]] = {
        "scripted_greedy": {"scores": [], "sequences": [], "seconds": []},
        "scripted_aware": {"scores": [], "sequences": [], "seconds": []},
        "random_shooting_true": {
            "scores": [],
            "sequences": [],
            "seconds": [],
        },
        "cem_true": {"scores": [], "sequences": [], "seconds": []},
        "cem_transition": {"scores": [], "sequences": [], "seconds": []},
        "oracle": {"scores": [], "sequences": [], "seconds": []},
    }
    rng = random.Random(20261125)
    for seed in cfg.planning_seeds:
        for name, policy in (
            ("scripted_greedy", ParallelGreedyPolicy()),
            ("scripted_aware", RecallAwarePolicy()),
        ):
            start = time.perf_counter()
            metrics = evaluate_policy(env, policy, episodes=1, seed=seed)
            results[name]["scores"].append(metrics.mean_score)
            results[name]["sequences"].append([])
            results[name]["seconds"].append(time.perf_counter() - start)

        score, sequence, seconds = _random_shooting(env, seed, triage, rng)
        results["random_shooting_true"]["scores"].append(score)
        results["random_shooting_true"]["sequences"].append(list(sequence))
        results["random_shooting_true"]["seconds"].append(seconds)

        score, sequence, seconds = _cem(env, seed, triage, rng, None)
        results["cem_true"]["scores"].append(score)
        results["cem_true"]["sequences"].append(list(sequence))
        results["cem_true"]["seconds"].append(seconds)

        score, sequence, seconds = _transition_cem(
            env, seed, triage, rng, model
        )
        results["cem_transition"]["scores"].append(score)
        results["cem_transition"]["sequences"].append(list(sequence))
        results["cem_transition"]["seconds"].append(seconds)

        start = time.perf_counter()
        score, sequence = _oracle(env, seed)
        results["oracle"]["scores"].append(score)
        results["oracle"]["sequences"].append(list(sequence))
        results["oracle"]["seconds"].append(time.perf_counter() - start)

    summary = {
        name: _summary([float(value) for value in payload["scores"]])
        for name, payload in results.items()
    }
    for name, payload in results.items():
        summary[name]["sequences"] = payload["sequences"]
        summary[name]["mean_seconds"] = float(np.mean(payload["seconds"]))
    return {
        "task": "factory.planning.triage.v1",
        "model": {
            "type": "ridge_delta",
            "ridge": cfg.ridge,
            "train_transitions": int(len(train_x)),
            "eval_transitions": int(len(eval_x)),
            "one_step_mse": one_step_mse,
            "copy_mse": copy_mse,
            "done_accuracy": done_accuracy,
            "rollout_mse": rollout_mse,
            "observation_features": STATE_DIM,
        },
        "config": {
            "population": cfg.population,
            "elites": cfg.elites,
            "iterations": cfg.iterations,
            "random_samples": cfg.random_samples,
            "train_seeds": cfg.train_seeds,
            "eval_seeds": cfg.eval_seeds,
            "train_seed_start": cfg.train_seed_start,
            "eval_seed_start": cfg.eval_seed_start,
            "max_sequences": cfg.max_sequences,
            "planning_seeds": list(cfg.planning_seeds),
        },
        "results": summary,
    }


def run_transition_ensemble(
    cfg: TransitionEnsembleConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or TransitionEnsembleConfig()
    triage = cfg.triage()
    env = CrewReplanEnv(_factory_config(), _replan_config())
    train_x, train_y, _ = _collect_data(
        env,
        seed_start=cfg.train_seed_start,
        episodes=cfg.train_seeds,
        max_sequences=cfg.max_sequences,
    )
    single = DeltaTransitionModel(cfg.ridge)
    single.fit(train_x, train_y)
    ensemble = EnsembleTransitionModel.fit(
        train_x,
        train_y,
        members=cfg.members,
        ridge=cfg.ridge,
        seed=cfg.ensemble_seed,
    )
    eval_x, eval_y, eval_rollouts = _collect_data(
        env,
        seed_start=cfg.eval_seed_start,
        episodes=cfg.eval_seeds,
        max_sequences=cfg.max_sequences,
    )
    one_step_mse = ensemble.mean_mse(eval_x, eval_y)
    copy_mse = _copy_mse(eval_x, eval_y)
    done_accuracy = ensemble.mean_done_accuracy(eval_x, eval_y)
    ensemble_means: list[float] = []
    ensemble_stds: list[float] = []
    absolute_errors: list[float] = []
    for state, actions, score in eval_rollouts:
        mean, std = ensemble.score_stats(state, actions)
        ensemble_means.append(mean)
        ensemble_stds.append(std)
        absolute_errors.append(abs(mean - score))
    rollout_mse = float(
        np.mean(
            [
                (mean - score) ** 2
                for mean, (_, _, score) in zip(
                    ensemble_means, eval_rollouts, strict=True
                )
            ]
        )
    )
    uncertainty_spearman = _spearman(ensemble_stds, absolute_errors)

    results: dict[str, dict[str, Any]] = {
        "scripted_greedy": {"scores": [], "sequences": [], "seconds": []},
        "scripted_aware": {"scores": [], "sequences": [], "seconds": []},
        "random_shooting_true": {
            "scores": [],
            "sequences": [],
            "seconds": [],
        },
        "cem_true": {"scores": [], "sequences": [], "seconds": []},
        "cem_single": {"scores": [], "sequences": [], "seconds": []},
        "cem_ensemble": {"scores": [], "sequences": [], "seconds": []},
        "oracle": {"scores": [], "sequences": [], "seconds": []},
    }
    rng = random.Random(20261125)
    for seed in cfg.planning_seeds:
        for name, policy in (
            ("scripted_greedy", ParallelGreedyPolicy()),
            ("scripted_aware", RecallAwarePolicy()),
        ):
            start = time.perf_counter()
            metrics = evaluate_policy(env, policy, episodes=1, seed=seed)
            results[name]["scores"].append(metrics.mean_score)
            results[name]["sequences"].append([])
            results[name]["seconds"].append(time.perf_counter() - start)

        score, sequence, seconds = _random_shooting(env, seed, triage, rng)
        results["random_shooting_true"]["scores"].append(score)
        results["random_shooting_true"]["sequences"].append(list(sequence))
        results["random_shooting_true"]["seconds"].append(seconds)

        score, sequence, seconds = _cem(env, seed, triage, rng, None)
        results["cem_true"]["scores"].append(score)
        results["cem_true"]["sequences"].append(list(sequence))
        results["cem_true"]["seconds"].append(seconds)

        score, sequence, seconds = _transition_cem(
            env, seed, triage, rng, single
        )
        results["cem_single"]["scores"].append(score)
        results["cem_single"]["sequences"].append(list(sequence))
        results["cem_single"]["seconds"].append(seconds)

        score, sequence, seconds = _ensemble_cem(
            env, seed, triage, rng, ensemble, cfg.beta
        )
        results["cem_ensemble"]["scores"].append(score)
        results["cem_ensemble"]["sequences"].append(list(sequence))
        results["cem_ensemble"]["seconds"].append(seconds)

        start = time.perf_counter()
        score, sequence = _oracle(env, seed)
        results["oracle"]["scores"].append(score)
        results["oracle"]["sequences"].append(list(sequence))
        results["oracle"]["seconds"].append(time.perf_counter() - start)

    summary = {
        name: _summary([float(value) for value in payload["scores"]])
        for name, payload in results.items()
    }
    for name, payload in results.items():
        summary[name]["sequences"] = payload["sequences"]
        summary[name]["mean_seconds"] = float(np.mean(payload["seconds"]))
    return {
        "task": "factory.planning.triage.v1",
        "model": {
            "type": "ridge_delta_ensemble",
            "ridge": cfg.ridge,
            "members": cfg.members,
            "beta": cfg.beta,
            "ensemble_seed": cfg.ensemble_seed,
            "train_transitions": int(len(train_x)),
            "eval_transitions": int(len(eval_x)),
            "one_step_mse": one_step_mse,
            "copy_mse": copy_mse,
            "done_accuracy": done_accuracy,
            "rollout_mse": rollout_mse,
            "uncertainty_spearman": uncertainty_spearman,
            "observation_features": STATE_DIM,
        },
        "config": {
            "population": cfg.population,
            "elites": cfg.elites,
            "iterations": cfg.iterations,
            "random_samples": cfg.random_samples,
            "train_seeds": cfg.train_seeds,
            "eval_seeds": cfg.eval_seeds,
            "train_seed_start": cfg.train_seed_start,
            "eval_seed_start": cfg.eval_seed_start,
            "max_sequences": cfg.max_sequences,
            "planning_seeds": list(cfg.planning_seeds),
        },
        "results": summary,
    }


def write_transition_ensemble_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "transition_ensemble_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    model = report["model"]
    lines = [
        "# Transition ensemble — three-bridge triage",
        "",
        f"Members {model['members']}; beta {model['beta']}; one-step MSE "
        f"{model['one_step_mse']:.6f}; copy MSE {model['copy_mse']:.6f}; "
        f"done accuracy {model['done_accuracy']:.3f}; rollout MSE "
        f"{model['rollout_mse']:.2f}; uncertainty Spearman "
        f"{model['uncertainty_spearman']:.3f}.",
        "",
        "| policy | mean score | 95% CI | success | seconds |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in report["results"].items():
        lines.append(
            f"| {name} | {row['mean_score']:.2f} "
            f"[{row['score_ci'][0]:.2f}, {row['score_ci'][1]:.2f}] | "
            f"{row['success_rate']:.2f} | {row['mean_seconds']:.3f} |"
        )
    lines.extend(
        [
            "",
            "CEM ensemble sequences: "
            + ", ".join(
                str(sequence)
                for sequence in report["results"]["cem_ensemble"]["sequences"]
            ),
        ]
    )
    (out / "transition_ensemble_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "transition_ensemble_report.md"


def write_transition_planning_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "transition_planning_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    model = report["model"]
    lines = [
        "# Transition-model planning — three-bridge triage",
        "",
        f"One-step MSE {model['one_step_mse']:.6f}; copy MSE "
        f"{model['copy_mse']:.6f}; done accuracy "
        f"{model['done_accuracy']:.3f}; rollout MSE "
        f"{model['rollout_mse']:.2f}.",
        "",
        "| policy | mean score | 95% CI | success | seconds |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in report["results"].items():
        lines.append(
            f"| {name} | {row['mean_score']:.2f} "
            f"[{row['score_ci'][0]:.2f}, {row['score_ci'][1]:.2f}] | "
            f"{row['success_rate']:.2f} | {row['mean_seconds']:.3f} |"
        )
    lines.extend(
        [
            "",
            "CEM transition sequences: "
            + ", ".join(
                str(sequence)
                for sequence in report["results"]["cem_transition"]["sequences"]
            ),
        ]
    )
    (out / "transition_planning_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "transition_planning_report.md"
