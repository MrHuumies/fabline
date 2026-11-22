"""Policies and evaluation for two-crew repair coordination."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.multi_crew import (
    CHOICES,
    ROLES,
    MultiCrewConfig,
    MultiCrewEnv,
)
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class MultiCrewPolicy(Protocol):
    name: str

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int: ...


class NoopPolicy:
    name = "noop"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return 0


class SingleEDFPolicy:
    name = "single_edf"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        available = [
            (info["roles"][role]["deadline"], index + 1)
            for index, role in enumerate(ROLES)
            if info["roles"][role]["outage"] > 0
            and info["roles"][role]["degraded"]
        ]
        first = min(available)[1] if available else 0
        return first * CHOICES


class ParallelNearestPolicy:
    name = "parallel_nearest"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        roles = [
            role
            for role in ROLES
            if info["roles"][role]["outage"] > 0
            and info["roles"][role]["degraded"]
        ]
        if not roles:
            return 0
        first = min(
            roles, key=lambda role: info["roles"][role]["distance_a"]
        )
        remaining = [role for role in roles if role != first]
        second = (
            min(
                remaining,
                key=lambda role: info["roles"][role]["distance_b"],
            )
            if remaining
            else "loop"
        )
        return (ROLES.index(first) + 1) * CHOICES + (
            ROLES.index(second) + 1 if second != "loop" else 0
        )


class ParallelGreedyPolicy:
    name = "parallel_greedy"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        roles = [
            role
            for role in ROLES
            if info["roles"][role]["outage"] > 0
            and info["roles"][role]["degraded"]
        ]
        best = (0.0, 0)
        for first in [0, *[ROLES.index(role) + 1 for role in roles]]:
            for second in [0, *[ROLES.index(role) + 1 for role in roles]]:
                if first > 0 and first == second:
                    continue
                action = first * CHOICES + second
                if not mask[action]:
                    continue
                value = 0.0
                if first > 0:
                    wire = info["roles"][ROLES[first - 1]]
                    value += wire["outage"] / max(1, wire["service_a"])
                if second > 0:
                    wire = info["roles"][ROLES[second - 1]]
                    value += wire["outage"] / max(1, wire["service_b"])
                if value > best[0]:
                    best = (value, action)
        return best[1]


class RandomPolicy:
    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        legal = np.flatnonzero(mask)
        return int(self.rng.choice(legal.tolist())) if len(legal) else 0


class TabularQPolicy:
    name = "tabular_q"

    def __init__(self) -> None:
        self.q: dict[tuple[int, ...], np.ndarray] = {}

    def _key(self, info: dict[str, Any]) -> tuple[int, ...]:
        def state(role: str) -> int:
            wire = info["roles"][role]
            if wire["failed"]:
                return 2
            return 1 if wire["degraded"] else 0

        small = info["roles"]["small"]
        large = info["roles"]["large"]
        return (
            min(4, int(info["tick"]) // 50),
            state("loop"),
            state("small"),
            state("large"),
            min(3, int(small["distance_a"]) // 5),
            min(3, int(small["distance_b"]) // 5),
            min(3, int(large["distance_a"]) // 5),
            min(3, int(large["distance_b"]) // 5),
        )

    def _values(self, key: tuple[int, ...]) -> np.ndarray:
        if key not in self.q:
            self.q[key] = np.zeros(16, dtype=np.float64)
        return self.q[key]

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        values = np.where(mask, self._values(self._key(info)), -np.inf)
        return int(np.argmax(values))

    def train(
        self,
        env: MultiCrewEnv,
        episodes: int = 500,
        seed: int = 0,
        train_seed_start: int = 25000,
        alpha: float = 0.2,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            try:
                observation, info = env.reset(
                    seed=train_seed_start + episode
                )
            except RuntimeError:
                continue
            done = False
            epsilon = 1.0 - 0.95 * episode / max(1, episodes - 1)
            while not done:
                mask = env.action_mask()
                key = self._key(info)
                if rng.random() < epsilon:
                    legal = np.flatnonzero(mask)
                    action = int(rng.choice(legal.tolist()))
                else:
                    action = self.act(observation, info, mask)
                observation, reward, terminated, truncated, info = env.step(
                    action
                )
                done = terminated or truncated
                if done:
                    target = reward
                else:
                    next_key = self._key(info)
                    next_mask = env.action_mask()
                    target = reward + float(
                        np.max(
                            np.where(
                                next_mask,
                                self._values(next_key),
                                -np.inf,
                            )
                        )
                    )
                values = self._values(key)
                values[action] += alpha * (target - values[action])


@dataclass
class MultiCrewMetrics:
    mean_score: float
    mean_reward: float
    mean_prevented: float
    mean_aborted: float
    mean_travel: float
    success_rate: float
    scores: list[float]
    rewards: list[float]


def evaluate_policy(
    env: MultiCrewEnv,
    policy: MultiCrewPolicy,
    episodes: int = 5,
    seed: int = 0,
) -> MultiCrewMetrics:
    scores: list[float] = []
    rewards: list[float] = []
    prevented: list[float] = []
    aborted: list[float] = []
    travel: list[float] = []
    successes: list[float] = []
    for episode in range(episodes):
        observation, info = env.reset(seed=seed + episode)
        done = False
        total_reward = 0.0
        while not done:
            action = policy.act(observation, info, env.action_mask())
            observation, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            done = terminated or truncated
        scores.append(float(info["score"]))
        rewards.append(total_reward)
        prevented.append(float(info["prevented"]))
        aborted.append(float(info["aborted"]))
        travel.append(float(info["travel_ticks"]))
        successes.append(1.0 if info["success"] else 0.0)
    return MultiCrewMetrics(
        mean_score=float(np.mean(scores)),
        mean_reward=float(np.mean(rewards)),
        mean_prevented=float(np.mean(prevented)),
        mean_aborted=float(np.mean(aborted)),
        mean_travel=float(np.mean(travel)),
        success_rate=float(np.mean(successes)),
        scores=scores,
        rewards=rewards,
    )


def _pool(metrics: list[MultiCrewMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    rewards = [value for item in metrics for value in item.rewards]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "mean_reward": float(np.mean(rewards)),
        "mean_prevented": float(np.mean([item.mean_prevented for item in metrics])),
        "mean_aborted": float(np.mean([item.mean_aborted for item in metrics])),
        "mean_travel": float(np.mean([item.mean_travel for item in metrics])),
        "success_rate": float(np.mean([item.success_rate for item in metrics])),
        "per_seed": [
            {
                "scores": item.scores,
                "success_rate": item.success_rate,
                "prevented": item.mean_prevented,
                "aborted": item.mean_aborted,
                "travel": item.mean_travel,
            }
            for item in metrics
        ],
    }


def _run_pair(env: MultiCrewEnv, seed: int, action: int) -> float:
    observation, info = env.reset(seed=seed)
    done = False
    while not done and not env.action_mask()[action]:
        observation, _, terminated, truncated, info = env.step(0)
        done = terminated or truncated
    if not done:
        observation, _, terminated, truncated, info = env.step(action)
        done = terminated or truncated
    return float(info["score"])


def _oracle_action(env: MultiCrewEnv, seed: int) -> int:
    return max(
        range(env.n_actions),
        key=lambda action: _run_pair(env, seed, action),
    )


def run_multi_crew(
    config: FactoryConfig,
    multi: MultiCrewConfig | None = None,
    *,
    episodes: int = 5,
    train_episodes: int = 500,
    seeds: tuple[int, ...] = (0, 1, 2),
    train_seed_start: int = 25000,
) -> dict[str, dict[str, Any]]:
    env = MultiCrewEnv(config, multi)
    results: dict[str, dict[str, Any]] = {}
    for name, baseline in (
        ("noop", NoopPolicy()),
        ("single_edf", SingleEDFPolicy()),
        ("parallel_nearest", ParallelNearestPolicy()),
        ("parallel_greedy", ParallelGreedyPolicy()),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, baseline, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    results["random"] = _pool(
        [
            evaluate_policy(
                env, RandomPolicy(seed=seed), episodes=1, seed=seed
            )
            for seed in seeds
        ]
    )
    oracle_metrics = []
    oracle_actions = {}
    for seed in seeds:
        action = _oracle_action(env, seed)
        oracle_actions[str(seed)] = action
        oracle_metrics.append(
            evaluate_policy(
                env,
                _FixedActionPolicy(action),
                episodes=1,
                seed=seed,
            )
        )
    results["oracle"] = _pool(oracle_metrics)
    results["oracle"]["actions"] = oracle_actions
    q_metrics = []
    for seed in seeds:
        policy = TabularQPolicy()
        policy.train(
            env,
            episodes=train_episodes,
            seed=seed,
            train_seed_start=train_seed_start + seed * 1000,
        )
        q_metrics.append(
            evaluate_policy(env, policy, episodes=1, seed=seed)
        )
    results["tabular_q"] = _pool(q_metrics)
    return results


class _FixedActionPolicy:
    name = "oracle"

    def __init__(self, action: int) -> None:
        self.action = action

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return self.action if mask[self.action] else 0


def _summarize_seed_scores(
    name: str,
    scores: dict[int, float],
    prevented: dict[int, float],
    aborted: dict[int, float],
    travel: dict[int, float],
    success: dict[int, bool],
    success_score: int = 150,
) -> dict[str, Any]:
    values = [scores[seed] for seed in sorted(scores)]
    success_values = [1.0 if success[seed] else 0.0 for seed in sorted(scores)]
    return {
        "name": name,
        "mean_score": float(np.mean(values)),
        "score_ci": list(bootstrap_mean_ci(values)),
        "min_score": float(np.min(values)),
        "max_score": float(np.max(values)),
        "mean_prevented": float(np.mean(list(prevented.values()))),
        "mean_aborted": float(np.mean(list(aborted.values()))),
        "mean_travel": float(np.mean(list(travel.values()))),
        "success_rate": float(np.mean(success_values)),
        "seeds_below_success": sum(
            1 for value in values if value < success_score
        ),
        "per_seed": {
            str(seed): {
                "score": scores[seed],
                "prevented": prevented[seed],
                "aborted": aborted[seed],
                "travel": travel[seed],
                "success": success[seed],
            }
            for seed in sorted(scores)
        },
    }


def _evaluate_seed(
    env: MultiCrewEnv,
    policy: MultiCrewPolicy,
    seed: int,
) -> MultiCrewMetrics:
    return evaluate_policy(env, policy, episodes=1, seed=seed)


def _policy_seed_data(
    env: MultiCrewEnv,
    policy: MultiCrewPolicy,
    seeds: tuple[int, ...],
) -> tuple[
    dict[int, float],
    dict[int, float],
    dict[int, float],
    dict[int, float],
    dict[int, bool],
]:
    scores: dict[int, float] = {}
    prevented: dict[int, float] = {}
    aborted: dict[int, float] = {}
    travel: dict[int, float] = {}
    success: dict[int, bool] = {}
    for seed in seeds:
        metrics = _evaluate_seed(env, policy, seed)
        scores[seed] = metrics.mean_score
        prevented[seed] = metrics.mean_prevented
        aborted[seed] = metrics.mean_aborted
        travel[seed] = metrics.mean_travel
        success[seed] = metrics.success_rate >= 1.0
    return scores, prevented, aborted, travel, success


def _paired_difference(
    first: dict[int, float],
    second: dict[int, float],
) -> dict[str, Any]:
    seeds = sorted(first)
    diffs = [first[seed] - second[seed] for seed in seeds]
    return {
        "mean": float(np.mean(diffs)),
        "ci": list(bootstrap_mean_ci(diffs)),
        "per_seed": {
            str(seed): first[seed] - second[seed] for seed in seeds
        },
    }


def run_crew_robustness(
    config: FactoryConfig,
    multi: MultiCrewConfig | None = None,
    *,
    seeds: tuple[int, ...] = (3000,),
    q_seeds: tuple[int, ...] = (0, 1, 2, 3, 4),
    train_episodes: int = 500,
    train_seed_start: int = 40000,
) -> dict[str, Any]:
    """Evaluate the two-crew task over a fixed seed block.

    Unlike ``run_multi_crew``, Q policies are trained on disjoint layout blocks
    and evaluated zero-shot on every evaluation seed.
    """

    if not seeds:
        raise ValueError("at least one evaluation seed is required")
    resolved_multi = multi or MultiCrewConfig()
    success_score = resolved_multi.success_score
    env = MultiCrewEnv(config, resolved_multi)
    policies: dict[str, dict[str, Any]] = {}

    scripted: tuple[tuple[str, MultiCrewPolicy], ...] = (
        ("noop", NoopPolicy()),
        ("single_edf", SingleEDFPolicy()),
        ("parallel_nearest", ParallelNearestPolicy()),
        ("parallel_greedy", ParallelGreedyPolicy()),
    )
    for name, policy in scripted:
        scores, prevented, aborted, travel, success = _policy_seed_data(
            env, policy, seeds
        )
        policies[name] = _summarize_seed_scores(
            name,
            scores,
            prevented,
            aborted,
            travel,
            success,
            success_score,
        )

    random_scores: dict[int, float] = {}
    random_prevented: dict[int, float] = {}
    random_aborted: dict[int, float] = {}
    random_travel: dict[int, float] = {}
    random_success: dict[int, bool] = {}
    for seed in seeds:
        metrics = _evaluate_seed(env, RandomPolicy(seed=seed), seed)
        random_scores[seed] = metrics.mean_score
        random_prevented[seed] = metrics.mean_prevented
        random_aborted[seed] = metrics.mean_aborted
        random_travel[seed] = metrics.mean_travel
        random_success[seed] = metrics.success_rate >= 1.0
    policies["random"] = _summarize_seed_scores(
        "random",
        random_scores,
        random_prevented,
        random_aborted,
        random_travel,
        random_success,
        success_score,
    )

    oracle_scores: dict[int, float] = {}
    oracle_prevented: dict[int, float] = {}
    oracle_aborted: dict[int, float] = {}
    oracle_travel: dict[int, float] = {}
    oracle_success: dict[int, bool] = {}
    oracle_actions: dict[str, int] = {}
    for seed in seeds:
        action = _oracle_action(env, seed)
        oracle_actions[str(seed)] = action
        metrics = _evaluate_seed(env, _FixedActionPolicy(action), seed)
        oracle_scores[seed] = metrics.mean_score
        oracle_prevented[seed] = metrics.mean_prevented
        oracle_aborted[seed] = metrics.mean_aborted
        oracle_travel[seed] = metrics.mean_travel
        oracle_success[seed] = metrics.success_rate >= 1.0
    policies["oracle"] = _summarize_seed_scores(
        "oracle",
        oracle_scores,
        oracle_prevented,
        oracle_aborted,
        oracle_travel,
        oracle_success,
        success_score,
    )
    policies["oracle"]["actions"] = oracle_actions

    q_summaries: dict[str, dict[str, Any]] = {}
    q_per_seed_scores: dict[int, list[float]] = {
        seed: [] for seed in seeds
    }
    q_pooled_scores: list[float] = []
    q_pooled_success: list[float] = []
    q_pooled_prevented: list[float] = []
    q_pooled_aborted: list[float] = []
    q_pooled_travel: list[float] = []
    for q_seed in q_seeds:
        policy = TabularQPolicy()
        policy.train(
            env,
            episodes=train_episodes,
            seed=q_seed,
            train_seed_start=train_seed_start + q_seed * 1000,
        )
        scores, prevented, aborted, travel, success = _policy_seed_data(
            env, policy, seeds
        )
        q_summaries[str(q_seed)] = _summarize_seed_scores(
            f"tabular_q_{q_seed}",
            scores,
            prevented,
            aborted,
            travel,
            success,
            success_score,
        )
        for seed in seeds:
            q_per_seed_scores[seed].append(scores[seed])
            q_pooled_scores.append(scores[seed])
            q_pooled_success.append(1.0 if success[seed] else 0.0)
            q_pooled_prevented.append(prevented[seed])
            q_pooled_aborted.append(aborted[seed])
            q_pooled_travel.append(travel[seed])

    q_mean_per_seed = (
        {
            str(seed): float(np.mean(values))
            for seed, values in q_per_seed_scores.items()
        }
        if q_seeds
        else {}
    )
    if q_pooled_scores:
        policies["tabular_q"] = {
            "name": "tabular_q",
            "mean_score": float(np.mean(q_pooled_scores)),
            "score_ci": list(bootstrap_mean_ci(q_pooled_scores)),
            "min_score": float(np.min(q_pooled_scores)),
            "max_score": float(np.max(q_pooled_scores)),
            "mean_prevented": float(np.mean(q_pooled_prevented)),
            "mean_aborted": float(np.mean(q_pooled_aborted)),
            "mean_travel": float(np.mean(q_pooled_travel)),
            "success_rate": float(np.mean(q_pooled_success)),
            "seeds_below_success": sum(
                1 for value in q_mean_per_seed.values()
                if value < success_score
            ),
            "runs_below_success": sum(
                1 for value in q_pooled_scores if value < success_score
            ),
            "mean_per_seed": q_mean_per_seed,
            "per_policy": q_summaries,
        }
    else:
        policies["tabular_q"] = {
            "name": "tabular_q",
            "mean_score": float("nan"),
            "score_ci": [float("nan"), float("nan")],
            "min_score": float("nan"),
            "max_score": float("nan"),
            "success_rate": float("nan"),
            "seeds_below_success": 0,
            "mean_per_seed": q_mean_per_seed,
            "per_policy": {},
        }

    return {
        "config": {
            "seeds": list(seeds),
            "q_seeds": list(q_seeds),
            "train_episodes": train_episodes,
            "train_seed_start": train_seed_start,
            "success_score": (multi or MultiCrewConfig()).success_score,
        },
        "policies": policies,
        "paired": {
            "parallel_nearest_minus_single_edf": _paired_difference(
                {
                    seed: policies["parallel_nearest"]["per_seed"][str(seed)][
                        "score"
                    ]
                    for seed in seeds
                },
                {
                    seed: policies["single_edf"]["per_seed"][str(seed)]["score"]
                    for seed in seeds
                },
            ),
            "oracle_minus_parallel_nearest": _paired_difference(
                {
                    seed: policies["oracle"]["per_seed"][str(seed)]["score"]
                    for seed in seeds
                },
                {
                    seed: policies["parallel_nearest"]["per_seed"][str(seed)][
                        "score"
                    ]
                    for seed in seeds
                },
            ),
        },
    }


def write_crew_robustness_report(
    out: str | Path,
    results: dict[str, Any],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "crew_robustness_results.json").write_text(
        json.dumps(
            {"config": config, "results": results},
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    policies = results["policies"]
    lines = [
        "# Two-crew coordination — seed robustness",
        "",
        f"Evaluation seeds {config['seeds'][0]}–{config['seeds'][-1]} "
        f"({len(config['seeds'])} seeds); one episode each.",
        f"Warning {config['warning_tick']}; failures "
        f"{config['loop_failure_tick']}/{config['small_failure_tick']}/"
        f"{config['large_failure_tick']}; success ≥ "
        f"{config['success_score']}.",
        "",
        "| policy | mean score | 95% CI | min | max | success | "
        "prevented | travel | below success |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in (
        "noop",
        "single_edf",
        "random",
        "parallel_nearest",
        "parallel_greedy",
        "tabular_q",
        "oracle",
    ):
        result = policies[name]
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['min_score']:.0f} | {result['max_score']:.0f} | "
            f"{result['success_rate']:.2f} | "
            f"{result.get('mean_prevented', float('nan')):.2f} | "
            f"{result.get('mean_travel', float('nan')):.1f} | "
            f"{result['seeds_below_success']} |"
        )
    lines.extend(
        [
            "",
            "## Paired differences",
            "",
            "| comparison | mean | 95% CI |",
            "|---|---:|---:|",
        ]
    )
    for name, result in results["paired"].items():
        lines.append(
            f"| {name} | {result['mean']:.2f} "
            f"[{result['ci'][0]:.2f}, {result['ci'][1]:.2f}] |"
        )
    lines.extend(
        [
            "",
            "## Q per training seed",
            "",
            "| Q seed | mean score | success | below success |",
            "|---|---:|---:|---:|",
        ]
    )
    for q_seed, result in policies["tabular_q"]["per_policy"].items():
        lines.append(
            f"| {q_seed} | {result['mean_score']:.2f} | "
            f"{result['success_rate']:.2f} | "
            f"{result['seeds_below_success']} |"
        )
    lines.extend(
        [
            "",
            "## Per-seed scores",
            "",
            "| seed | single | nearest | greedy | Q mean | oracle |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for seed in config["seeds"]:
        key = str(seed)
        q_mean = policies["tabular_q"]["mean_per_seed"].get(key)
        q_text = f"{q_mean:.1f}" if q_mean is not None else "—"
        lines.append(
            f"| {seed} | "
            f"{policies['single_edf']['per_seed'][key]['score']:.0f} | "
            f"{policies['parallel_nearest']['per_seed'][key]['score']:.0f} | "
            f"{policies['parallel_greedy']['per_seed'][key]['score']:.0f} | "
            f"{q_text} | "
            f"{policies['oracle']['per_seed'][key]['score']:.0f} |"
        )
    lines.extend(
        [
            "",
            "Oracle pair actions: "
            + ", ".join(
                f"{seed}:{action}"
                for seed, action in policies["oracle"]["actions"].items()
            ),
        ]
    )
    (out / "crew_robustness_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "crew_robustness_report.md"


def write_multi_crew_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "multi_crew_results.json").write_text(
        json.dumps(
            {"config": config, "results": results},
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Two-crew repair coordination",
        "",
        f"Warning {config['warning_tick']}; failures "
        f"{config['loop_failure_tick']}/{config['small_failure_tick']}/"
        f"{config['large_failure_tick']}.",
        "",
        "| policy | mean score | prevented | travel | success |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['mean_prevented']:.2f} | "
            f"{result['mean_travel']:.1f} | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            "Oracle pair actions: "
            + ", ".join(
                f"{seed}:{action}"
                for seed, action in results["oracle"].get(
                    "actions", {}
                ).items()
            ),
        ]
    )
    (out / "multi_crew_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "multi_crew_report.md"
