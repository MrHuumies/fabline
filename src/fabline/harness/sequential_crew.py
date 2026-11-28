"""Policies and evaluation for sequential two-crew repair control."""

from __future__ import annotations

import itertools
import json
import random
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.sequential_crew import (
    N_CREW_ACTIONS,
    N_CREWS,
    SequentialCrewConfig,
    SequentialCrewEnv,
)
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import TileType


class SequentialCrewPolicy(Protocol):
    name: str

    def act(self, env: SequentialCrewEnv) -> tuple[int, int]: ...


def _walkable(env: SequentialCrewEnv, cell: tuple[int, int]) -> bool:
    x, y = cell
    if not 0 <= x < env.world.state.width:
        return False
    if not 0 <= y < env.world.state.height:
        return False
    return (
        env.world.state.tiles[y * env.world.state.width + x]
        is not TileType.ROCK
    )


def _bfs_action(
    env: SequentialCrewEnv,
    crew_index: int,
    goals: set[tuple[int, int]],
) -> int | None:
    start = env.positions[crew_index]
    other = env.positions[1 - crew_index]
    if start in goals:
        return None
    deltas = ((0, -1), (1, 0), (0, 1), (-1, 0))
    queue: deque[tuple[tuple[int, int], int | None]] = deque(
        [(start, None)]
    )
    seen = {start}
    while queue:
        cell, first = queue.popleft()
        for action, (dx, dy) in enumerate(deltas):
            nxt = (cell[0] + dx, cell[1] + dy)
            if nxt in seen or nxt == other or not _walkable(env, nxt):
                continue
            seen.add(nxt)
            step = action if first is None else first
            if nxt in goals:
                return step
            queue.append((nxt, step))
    return None


def _pursue(
    env: SequentialCrewEnv,
    crew_index: int,
    target_index: int,
) -> int:
    if env.adjacent(crew_index, target_index):
        return 5
    target = env.targets[target_index]
    goals = {(target.ax, target.ay), (target.bx, target.by)}
    action = _bfs_action(env, crew_index, goals)
    return 4 if action is None else action


def _nearest_target(
    env: SequentialCrewEnv,
    crew_index: int,
    candidates: list[int],
) -> int | None:
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda index: (
            env.distance(env.positions[crew_index], env.targets[index]),
            index,
        ),
    )


def _distinct_pair(
    env: SequentialCrewEnv,
    failed: list[int],
) -> tuple[int | None, int | None]:
    if not failed:
        return None, None
    if len(failed) == 1:
        return failed[0], failed[0]
    best: tuple[int, int, int] | None = None
    for first in failed:
        for second in failed:
            if first == second:
                continue
            cost = env.distance(env.positions[0], env.targets[first]) + env.distance(
                env.positions[1], env.targets[second]
            )
            if best is None or cost < best[0]:
                best = (cost, first, second)
    assert best is not None
    return best[1], best[2]


class RandomCrewPolicy:
    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    def act(self, env: SequentialCrewEnv) -> tuple[int, int]:
        mask = env.joint_mask()
        indices = np.flatnonzero(mask)
        index = int(self.rng.choice(indices.tolist()))
        return divmod(index, N_CREW_ACTIONS)


class GreedyCrewPolicy:
    name = "greedy"

    def act(self, env: SequentialCrewEnv) -> tuple[int, int]:
        failed = [
            index for index, target in enumerate(env.targets) if target.failed
        ]
        actions: list[int] = []
        for crew_index in range(N_CREWS):
            target_index = _nearest_target(env, crew_index, failed)
            actions.append(
                4 if target_index is None else _pursue(env, crew_index, target_index)
            )
        return actions[0], actions[1]


class AssignedCrewPolicy:
    name = "assigned"

    def act(self, env: SequentialCrewEnv) -> tuple[int, int]:
        failed = [
            index for index, target in enumerate(env.targets) if target.failed
        ]
        first, second = _distinct_pair(env, failed)
        actions = [4, 4]
        if first is not None:
            actions[0] = _pursue(env, 0, first)
        if second is not None:
            actions[1] = _pursue(env, 1, second)
        return actions[0], actions[1]


class SingleCrewPolicy:
    name = "single_crew"

    def act(self, env: SequentialCrewEnv) -> tuple[int, int]:
        failed = [
            index for index, target in enumerate(env.targets) if target.failed
        ]
        target_index = _nearest_target(env, 0, failed)
        action = 4 if target_index is None else _pursue(env, 0, target_index)
        return action, 4


class QueueCrewPolicy:
    name = "queue"

    def __init__(self, queues: tuple[tuple[int, ...], ...]) -> None:
        self.queues = queues

    def act(self, env: SequentialCrewEnv) -> tuple[int, int]:
        actions = [4, 4]
        for crew_index in range(N_CREWS):
            queue = [
                index
                for index in self.queues[crew_index]
                if env.targets[index].failed
            ]
            if not queue:
                continue
            actions[crew_index] = _pursue(env, crew_index, queue[0])
        return actions[0], actions[1]


def _simulate_queues(
    env: SequentialCrewEnv,
    queues: tuple[tuple[int, ...], ...],
) -> float:
    branch = env.clone()
    policy = QueueCrewPolicy(queues)
    done = False
    while not done:
        action = policy.act(branch)
        _, _, terminated, truncated, _ = branch.step(action)
        done = terminated or truncated
    return float(branch.world.state.score)


class QueueOraclePolicy:
    """Best queue assignment/order over the scripted movement policy.

    This is a centralized queue-plan upper bound, not a full joint-action
    oracle: the joint action space is ``6^2`` per step over a 50-step horizon.
    """

    name = "queue_oracle"

    def __init__(self) -> None:
        self.plans: dict[int, tuple[tuple[int, ...], ...]] = {}

    def _plan(
        self, env: SequentialCrewEnv
    ) -> tuple[tuple[int, ...], ...]:
        if env.seed in self.plans:
            return self.plans[env.seed]
        indices = tuple(range(len(env.targets)))
        best_score = float("-inf")
        best: tuple[tuple[int, ...], ...] = ((), ())
        for assignment in itertools.product((0, 1), repeat=len(indices)):
            first = tuple(
                index
                for index, crew in zip(indices, assignment, strict=False)
                if crew == 0
            )
            second = tuple(
                index
                for index, crew in zip(indices, assignment, strict=False)
                if crew == 1
            )
            for first_order in itertools.permutations(first):
                for second_order in itertools.permutations(second):
                    queues = (first_order, second_order)
                    score = _simulate_queues(env, queues)
                    if score > best_score:
                        best_score = score
                        best = queues
        self.plans[env.seed] = best
        return best

    def act(self, env: SequentialCrewEnv) -> tuple[int, int]:
        return QueueCrewPolicy(self._plan(env)).act(env)


def _crew_key(env: SequentialCrewEnv, crew_index: int) -> tuple[int, ...]:
    state = env.world.state
    failed_mask = sum(
        1 << index
        for index, target in enumerate(env.targets)
        if target.failed
    )
    failed_indices = [
        index for index, target in enumerate(env.targets) if target.failed
    ]
    if failed_indices:
        nearest_index = min(
            failed_indices,
            key=lambda index: env.distance(
                env.positions[crew_index], env.targets[index]
            ),
        )
        target = env.targets[nearest_index]
        endpoints = ((target.ax, target.ay), (target.bx, target.by))
        ex, ey = min(
            endpoints,
            key=lambda cell: abs(cell[0] - env.positions[crew_index][0])
            + abs(cell[1] - env.positions[crew_index][1]),
        )
        dx = (ex > env.positions[crew_index][0]) - (
            ex < env.positions[crew_index][0]
        )
        dy = (ey > env.positions[crew_index][1]) - (
            ey < env.positions[crew_index][1]
        )
        nearest = env.distance(env.positions[crew_index], target)
    else:
        dx = dy = 0
        nearest = 0
    adjacent = int(
        any(env.adjacent(crew_index, index) for index in failed_indices)
    )
    return (
        dx,
        dy,
        failed_mask,
        min(4, nearest),
        adjacent,
        env.repairs,
        min(4, state.tick // 100),
    )


class IndependentQPolicy:
    name = "independent_q"

    def __init__(self) -> None:
        self.q: list[dict[tuple[int, ...], np.ndarray]] = [
            {} for _ in range(N_CREWS)
        ]

    def _values(self, crew_index: int, key: tuple[int, ...]) -> np.ndarray:
        table = self.q[crew_index]
        if key not in table:
            table[key] = np.zeros(N_CREW_ACTIONS, dtype=np.float64)
        return table[key]

    def _act_one(
        self,
        env: SequentialCrewEnv,
        crew_index: int,
        rng: random.Random | None = None,
        epsilon: float = 0.0,
    ) -> int:
        mask = env.action_mask(crew_index)
        values = self._values(crew_index, _crew_key(env, crew_index))
        legal = np.flatnonzero(mask)
        if rng is not None and rng.random() < epsilon:
            return int(rng.choice(legal.tolist()))
        best = float(np.max(values[legal]))
        choices = [int(action) for action in legal if values[action] == best]
        return int(choices[0])

    def act(self, env: SequentialCrewEnv) -> tuple[int, int]:
        return (
            self._act_one(env, 0),
            self._act_one(env, 1),
        )

    def train(
        self,
        env: SequentialCrewEnv,
        episodes: int = 500,
        seed: int = 90_000,
        alpha: float = 0.2,
        gamma: float = 0.95,
    ) -> None:
        rng = random.Random(seed)
        episode = 0
        attempt = 0
        while episode < episodes:
            try:
                env.reset(seed=seed + attempt)
            except RuntimeError:
                attempt += 1
                if attempt > episodes * 10:
                    raise RuntimeError(
                        "too many invalid crew layouts"
                    ) from None
                continue
            done = False
            epsilon = max(0.05, 1.0 - 0.95 * episode / max(1, episodes - 1))
            while not done:
                keys = [
                    _crew_key(env, crew_index)
                    for crew_index in range(N_CREWS)
                ]
                actions = [
                    self._act_one(env, crew_index, rng, epsilon)
                    for crew_index in range(N_CREWS)
                ]
                _, reward, terminated, truncated, _ = env.step(
                    (actions[0], actions[1])
                )
                done = terminated or truncated
                next_keys = [
                    _crew_key(env, crew_index)
                    for crew_index in range(N_CREWS)
                ]
                for crew_index, action in enumerate(actions):
                    target = reward / 10.0
                    if not done:
                        target += gamma * float(
                            np.max(
                                self._values(
                                    crew_index, next_keys[crew_index]
                                )
                            )
                        )
                    values = self._values(crew_index, keys[crew_index])
                    values[action] += alpha * (target - values[action])
            episode += 1
            attempt += 1


class BehaviorClonedPolicy:
    """Imitate the assigned scripted policy with one classifier per crew."""

    name = "bc"

    def __init__(self) -> None:
        self.models: list[Any] = [None, None]

    def _fit_models(
        self,
        features: list[np.ndarray],
        labels: list[list[int]],
    ) -> None:
        from sklearn.ensemble import HistGradientBoostingClassifier

        X = np.stack(features)
        for crew_index in range(N_CREWS):
            model = HistGradientBoostingClassifier(
                max_iter=200,
                random_state=0,
            )
            model.fit(X, np.asarray(labels[crew_index]))
            self.models[crew_index] = model

    def _collect(
        self,
        env: SequentialCrewEnv,
        *,
        episodes: int,
        seed: int,
        student: bool,
        features: list[np.ndarray],
        labels: list[list[int]],
    ) -> None:
        teacher = AssignedCrewPolicy()
        episode = 0
        attempt = 0
        while episode < episodes:
            try:
                env.reset(seed=seed + attempt)
            except RuntimeError:
                attempt += 1
                if attempt > episodes * 10:
                    raise RuntimeError(
                        "too many invalid crew layouts"
                    ) from None
                continue
            done = False
            while not done:
                observation = env.observe()
                expert = teacher.act(env)
                features.append(observation)
                labels[0].append(expert[0])
                labels[1].append(expert[1])
                action = self.act(env) if student else expert
                _, _, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
            episode += 1
            attempt += 1

    def fit(
        self,
        env: SequentialCrewEnv,
        episodes: int = 20,
        seed: int = 20_000,
        dagger_iterations: int = 3,
    ) -> None:
        features: list[np.ndarray] = []
        labels: list[list[int]] = [[], []]
        self._collect(
            env,
            episodes=episodes,
            seed=seed,
            student=False,
            features=features,
            labels=labels,
        )
        self._fit_models(features, labels)
        for iteration in range(dagger_iterations):
            self._collect(
                env,
                episodes=max(1, episodes // 2),
                seed=seed + 10_000 + iteration * 1_000,
                student=True,
                features=features,
                labels=labels,
            )
            self._fit_models(features, labels)

    def act(self, env: SequentialCrewEnv) -> tuple[int, int]:
        observation = env.observe().reshape(1, -1)
        actions: list[int] = []
        for crew_index in range(N_CREWS):
            model = self.models[crew_index]
            if model is None:
                raise RuntimeError("behavior-cloned policy is not fitted")
            probabilities = np.zeros(N_CREW_ACTIONS, dtype=np.float64)
            for label, probability in zip(
                model.classes_,
                model.predict_proba(observation)[0],
                strict=False,
            ):
                probabilities[int(label)] = float(probability)
            mask = env.action_mask(crew_index)
            legal = np.flatnonzero(mask)
            actions.append(int(legal[int(np.argmax(probabilities[legal]))]))
        return actions[0], actions[1]


@dataclass
class SequentialCrewMetrics:
    mean_score: float
    success_rate: float
    mean_repairs: float
    mean_steps: float
    scores: list[float]
    successes: list[float]
    repairs: list[float]
    steps: list[float]


def evaluate_policy(
    env: SequentialCrewEnv,
    policy: SequentialCrewPolicy,
    *,
    episodes: int = 5,
    seed: int = 0,
) -> SequentialCrewMetrics:
    scores: list[float] = []
    successes: list[float] = []
    repairs: list[float] = []
    steps: list[float] = []
    for episode in range(episodes):
        env.reset(seed=seed + episode)
        done = False
        while not done:
            _, _, terminated, truncated, info = env.step(policy.act(env))
            done = terminated or truncated
        scores.append(float(info["score"]))
        successes.append(1.0 if info["success"] else 0.0)
        repairs.append(float(info["repairs"]))
        steps.append(float(info["steps"]))
    return SequentialCrewMetrics(
        mean_score=float(np.mean(scores)),
        success_rate=float(np.mean(successes)),
        mean_repairs=float(np.mean(repairs)),
        mean_steps=float(np.mean(steps)),
        scores=scores,
        successes=successes,
        repairs=repairs,
        steps=steps,
    )


def _pool(metrics: list[SequentialCrewMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    successes = [value for item in metrics for value in item.successes]
    repairs = [value for item in metrics for value in item.repairs]
    steps = [value for item in metrics for value in item.steps]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "success_rate": float(np.mean(successes)),
        "success_ci": list(bootstrap_mean_ci(successes)),
        "mean_repairs": float(np.mean(repairs)),
        "mean_steps": float(np.mean(steps)),
        "per_seed": [item.mean_score for item in metrics],
    }


def validate_seeds(
    env: SequentialCrewEnv, seeds: tuple[int, ...]
) -> None:
    """Fail loudly if a formal seed cannot build a valid crew layout."""
    for seed in seeds:
        try:
            env.reset(seed=seed)
        except RuntimeError as exc:
            raise RuntimeError(
                f"invalid sequential-crew seed {seed}: {exc}"
            ) from exc


def run_sequential_crew(
    config: FactoryConfig,
    crew: SequentialCrewConfig,
    *,
    seeds: tuple[int, ...] = (1000, 1001, 1002, 1003, 1004),
    episodes: int = 5,
    q_episodes: int = 500,
    bc_episodes: int = 50,
) -> dict[str, dict[str, Any]]:
    env = SequentialCrewEnv(config, crew)
    validate_seeds(
        env,
        tuple(
            seed + episode
            for seed in seeds
            for episode in range(episodes)
        ),
    )
    results: dict[str, dict[str, Any]] = {}
    for name, factory in (
        ("single_crew", SingleCrewPolicy),
        ("greedy", GreedyCrewPolicy),
        ("assigned", AssignedCrewPolicy),
        ("queue_oracle", QueueOraclePolicy),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, factory(), episodes=episodes, seed=seed)
                for seed in seeds
            ]
        )
    results["random"] = _pool(
        [
            evaluate_policy(
                env, RandomCrewPolicy(seed), episodes=episodes, seed=seed
            )
            for seed in seeds
        ]
    )
    q = IndependentQPolicy()
    q_start = time.perf_counter()
    q.train(env, episodes=q_episodes, seed=90_000)
    q_seconds = time.perf_counter() - q_start
    results["independent_q"] = _pool(
        [
            evaluate_policy(env, q, episodes=episodes, seed=seed)
            for seed in seeds
        ]
    )
    results["independent_q"]["model"] = {
        "table_entries": int(sum(len(table) for table in q.q)),
        "train_seconds": float(q_seconds),
        "messages": 0,
    }
    bc = BehaviorClonedPolicy()
    bc_start = time.perf_counter()
    bc.fit(env, episodes=bc_episodes, seed=20_000)
    bc_seconds = time.perf_counter() - bc_start
    results["bc"] = _pool(
        [
            evaluate_policy(env, bc, episodes=episodes, seed=seed)
            for seed in seeds
        ]
    )
    results["bc"]["model"] = {
        "models": N_CREWS,
        "max_iter": 200,
        "train_seconds": float(bc_seconds),
        "messages": 0,
    }
    return results


def sequential_gates(
    results: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    single = float(results["single_crew"]["mean_score"])
    scripted = max(
        ("greedy", "assigned"),
        key=lambda name: float(results[name]["mean_score"]),
    )
    best_scripted = float(results[scripted]["mean_score"])
    random_score = float(results["random"]["mean_score"])
    learned = max(
        ("independent_q", "bc"),
        key=lambda name: float(results[name]["mean_score"]),
    )
    best_learned = float(results[learned]["mean_score"])
    h1 = best_scripted >= single + 10.0
    h2 = float(results[scripted]["success_rate"]) >= 0.60
    h3 = best_learned >= random_score + 10.0
    h4 = float(results[learned]["success_rate"]) >= 0.60
    h5 = all(
        "model" in results[name] for name in ("independent_q", "bc")
    )
    return {
        "H1_coordination": h1,
        "H2_scripted_success": h2,
        "H3_learned_gap": h3,
        "H4_learned_success": h4,
        "H5_cost_reported": h5,
        "challenge": bool(h1 and h2 and not (h3 and h4)),
    }


def build_expected_summary(
    results: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Build the compact factory-v0.6 expected summary.

    Timing fields are intentionally excluded so the check is machine-independent.
    """
    gates = sequential_gates(results)
    scripted = max(
        ("greedy", "assigned"),
        key=lambda name: float(results[name]["mean_score"]),
    )
    oracle_gap = float(results["queue_oracle"]["mean_score"]) - float(
        results[scripted]["mean_score"]
    )
    tasks: dict[str, Any] = {}
    for name, row in results.items():
        entry = {
            "mean_score": row["mean_score"],
            "score_ci": row["score_ci"],
            "success_rate": row["success_rate"],
            "mean_repairs": row["mean_repairs"],
            "mean_steps": row["mean_steps"],
            "per_seed": row["per_seed"],
        }
        if "model" in row:
            entry["model"] = {
                key: row["model"].get(key)
                for key in ("table_entries", "models", "messages")
            }
        tasks[name] = entry
    return {
        "benchmark": "factory-v0.6",
        "version": "0.6.0",
        "status": "challenge",
        "plan": "sequential-v0.6",
        "date": "2026-11-28",
        "tolerance": {"rtol": 0.03, "atol": 0.02},
        "config": config,
        "tasks": {
            "crew-sequential": {
                "results": tasks,
                "gates": gates,
                "oracle_gap": oracle_gap,
            }
        },
    }


def write_sequential_crew_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    gates = sequential_gates(results)
    scripted = max(
        ("greedy", "assigned"),
        key=lambda name: float(results[name]["mean_score"]),
    )
    oracle_gap = float(results["queue_oracle"]["mean_score"]) - float(
        results[scripted]["mean_score"]
    )
    (out / "sequential_crew_results.json").write_text(
        json.dumps(
            {
                "config": config,
                "results": results,
                "gates": gates,
                "oracle_gap": oracle_gap,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Sequential crew repair",
        "",
        f"- target wires: {config['target_count']}",
        f"- repair ticks: {config['repair_ticks']}",
        f"- seeds: {config['seeds']}",
        "",
        "| policy | score | success | repairs | steps |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in results.items():
        lines.append(
            f"| {name} | {row['mean_score']:.2f} "
            f"[{row['score_ci'][0]:.2f}, {row['score_ci'][1]:.2f}] | "
            f"{row['success_rate']:.2f} | {row['mean_repairs']:.2f} | "
            f"{row['mean_steps']:.1f} |"
        )
    lines.extend(
        [
            "",
            f"- oracle gap (queue oracle - best scripted): {oracle_gap:.2f}",
            f"- challenge tier: {'yes' if gates['challenge'] else 'no'}",
            "",
            "## Gates",
            "",
            "| Gate | Result |",
            "|---|---|",
        ]
    )
    for name, passed in gates.items():
        if name == "challenge":
            result = "yes" if passed else "no"
        else:
            result = "pass" if passed else "fail"
        lines.append(f"| {name} | {result} |")
    lines.append("")
    (out / "sequential_crew_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "sequential_crew_report.md"
