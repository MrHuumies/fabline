"""Policies and evaluation for decentralized private-view triage."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.crew_decentralized import DecentralizedVisibilityEnv
from fabline.env.crew_replan import CrewReplanConfig, CrewReplanEnv
from fabline.env.multi_crew import ROLES
from fabline.harness.crew_replan import (
    FixedTwoPolicy,
    _oracle_pair,
    evaluate_policy,
)
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class CrewPolicy(Protocol):
    name: str

    def act(
        self,
        crew: str,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int: ...


def _positive(
    info: dict[str, Any],
    crew: str,
) -> list[str]:
    roles = info["crew_roles"][crew]
    if info["phase"] == "initial":
        return [
            role
            for role in ROLES
            if roles[role]["known"] and roles[role]["degraded"]
        ]
    return [
        role
        for role in ROLES
        if roles[role]["known"]
        and roles[role]["outage"] > 0
        and (roles[role]["degraded"] or roles[role]["failed"])
    ]


class LocalNearestPolicy:
    name = "local_nearest"

    def act(
        self,
        crew: str,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        roles = _positive(info, crew)
        if not roles:
            return 0
        key = "distance_a" if crew == "a" else "distance_b"
        role = min(roles, key=lambda item: info["crew_roles"][crew][item][key])
        action = ROLES.index(role) + 1
        return action if mask[action] else 0


class LocalGreedyPolicy:
    name = "local_greedy"

    def act(
        self,
        crew: str,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        roles = _positive(info, crew)
        if not roles:
            return 0
        key = "service_a" if crew == "a" else "service_b"
        role = max(
            roles,
            key=lambda item: info["crew_roles"][crew][item]["outage"]
            / max(1, info["crew_roles"][crew][item][key]),
        )
        action = ROLES.index(role) + 1
        return action if mask[action] else 0


class LocalAwarePolicy:
    name = "local_aware"

    def act(
        self,
        crew: str,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        roles = _positive(info, crew)
        if not roles:
            return 0
        if info["phase"] == "initial":
            role = min(
                roles,
                key=lambda item: info["crew_roles"][crew][item]["deadline"],
            )
        else:
            role = max(
                roles,
                key=lambda item: info["crew_roles"][crew][item]["outage"],
            )
        action = ROLES.index(role) + 1
        return action if mask[action] else 0


class IndependentQPolicy:
    """One tabular Q table per crew; shared reward, local state."""

    name = "private_q"

    def __init__(self) -> None:
        self.q: dict[str, dict[tuple[Any, ...], np.ndarray]] = {
            "a": {},
            "b": {},
        }

    def _key(self, crew: str, info: dict[str, Any]) -> tuple[Any, ...]:
        roles = info["crew_roles"][crew]
        values: list[Any] = [
            info["phase"],
            min(4, int(info["tick"]) // 100),
            1 if info["crew_b_available"] else 0,
            -1 if info["orphaned_role"] is None else ROLES.index(info["orphaned_role"]),
        ]
        key = "distance_a" if crew == "a" else "distance_b"
        for role in ROLES:
            data = roles[role]
            state = 2 if data["failed"] else 1 if data["degraded"] else 0
            values.extend(
                [
                    state if data["known"] else 3,
                    min(4, int(data["outage"]) // 3),
                    min(4, int(data[key]) // 5),
                ]
            )
        return tuple(values)

    def _values(
        self,
        crew: str,
        key: tuple[Any, ...],
    ) -> np.ndarray:
        if key not in self.q[crew]:
            self.q[crew][key] = np.zeros(4, dtype=np.float64)
        return self.q[crew][key]

    def act(
        self,
        crew: str,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        values = np.where(mask, self._values(crew, self._key(crew, info)), -np.inf)
        return int(np.argmax(values))

    def train(
        self,
        env: DecentralizedVisibilityEnv,
        episodes: int = 500,
        seed: int = 0,
        alpha: float = 0.2,
        gamma: float = 0.95,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            info = env.reset(seed=seed + episode)
            done = False
            epsilon = 1.0 - 0.95 * episode / max(1, episodes - 1)
            while not done:
                choices: dict[str, int] = {}
                keys: dict[str, tuple[Any, ...]] = {}
                masks: dict[str, np.ndarray] = {}
                for crew in ("a", "b"):
                    local = env.agent_info(crew, info)
                    mask = env.agent_mask(crew, info)
                    key = self._key(crew, local)
                    keys[crew] = key
                    masks[crew] = mask
                    if rng.random() < epsilon:
                        legal = np.flatnonzero(mask)
                        choices[crew] = int(rng.choice(legal.tolist()))
                    else:
                        choices[crew] = self.act(crew, local, mask)
                info, reward, terminated, truncated, _ = env.step(choices)
                done = terminated or truncated
                for crew in ("a", "b"):
                    target = reward
                    if not done:
                        local = env.agent_info(crew, info)
                        next_mask = env.agent_mask(crew, info)
                        target += gamma * float(
                            np.max(
                                np.where(
                                    next_mask,
                                    self._values(
                                        crew, self._key(crew, local)
                                    ),
                                    -np.inf,
                                )
                            )
                        )
                    values = self._values(crew, keys[crew])
                    values[choices[crew]] += alpha * (
                        target - values[choices[crew]]
                    )


@dataclass
class DecentralizedMetrics:
    mean_score: float
    success_rate: float
    scores: list[float]


def evaluate_crew_policy(
    env: DecentralizedVisibilityEnv,
    policy: CrewPolicy,
    seed: int,
) -> DecentralizedMetrics:
    info = env.reset(seed)
    done = False
    while not done:
        choices = {
            crew: policy.act(
                crew,
                env.agent_info(crew, info),
                env.agent_mask(crew, info),
            )
            for crew in ("a", "b")
        }
        info, _, terminated, truncated, _ = env.step(choices)
        done = terminated or truncated
    return DecentralizedMetrics(
        mean_score=float(info["score"]),
        success_rate=1.0 if info["success"] else 0.0,
        scores=[float(info["score"])],
    )


def _pool_decentralized(
    metrics: list[DecentralizedMetrics],
) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "success_rate": float(
            np.mean([item.success_rate for item in metrics])
        ),
        "scores": scores,
    }


def _global_oracle(
    config: FactoryConfig,
    replan: CrewReplanConfig,
    seeds: tuple[int, ...],
) -> dict[str, Any]:
    env = CrewReplanEnv(config, replan)
    scores: list[float] = []
    successes: list[float] = []
    for seed in seeds:
        initial, replan_action = _oracle_pair(env, seed)
        metrics = evaluate_policy(
            env,
            FixedTwoPolicy(initial, replan_action),
            episodes=1,
            seed=seed,
        )
        scores.append(float(metrics.mean_score))
        successes.append(float(metrics.success_rate))
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "success_rate": float(np.mean(successes)),
        "scores": scores,
    }


def run_decentralized(
    config: FactoryConfig,
    replan: CrewReplanConfig,
    *,
    seeds: tuple[int, ...] = (0, 1, 2),
    q_seeds: tuple[int, ...] = (0, 1, 2),
    train_episodes: int = 500,
) -> dict[str, dict[str, Any]]:
    env = DecentralizedVisibilityEnv(config, replan, radius=16)
    results: dict[str, dict[str, Any]] = {}
    for name, local_policy in (
        ("local_nearest", LocalNearestPolicy()),
        ("local_greedy", LocalGreedyPolicy()),
        ("local_aware", LocalAwarePolicy()),
    ):
        results[name] = _pool_decentralized(
            [evaluate_crew_policy(env, local_policy, seed) for seed in seeds]
        )
    for q_seed in q_seeds:
        q_policy = IndependentQPolicy()
        q_policy.train(env, episodes=train_episodes, seed=q_seed)
        metrics = [evaluate_crew_policy(env, q_policy, seed) for seed in seeds]
        results.setdefault("private_q", {"scores": [], "metrics": []})
        results["private_q"]["metrics"].extend(metrics)
    if "private_q" in results:
        pooled = _pool_decentralized(results["private_q"]["metrics"])
        results["private_q"] = pooled
    results["global_oracle"] = _global_oracle(config, replan, seeds)
    return results


def write_decentralized_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "decentralized_results.json").write_text(
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
        "# Decentralized private-view triage",
        "",
        f"Radius {config['radius']}; success ≥ {config['success_score']}.",
        "",
        "| policy | mean score | 95% CI | success |",
        "|---|---:|---:|---:|",
    ]
    for name, row in results.items():
        lines.append(
            f"| {name} | {row['mean_score']:.2f} "
            f"[{row['score_ci'][0]:.2f}, {row['score_ci'][1]:.2f}] | "
            f"{row['success_rate']:.2f} |"
        )
    (out / "decentralized_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "decentralized_report.md"
