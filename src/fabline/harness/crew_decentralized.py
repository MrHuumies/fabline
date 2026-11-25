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
        train_seed_start: int = 0,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            info = env.reset(seed=train_seed_start + seed + episode)
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


def _slack_bucket(
    data: dict[str, Any],
    service: int,
    tick: int,
) -> int:
    if not data.get("known", True) or not data["degraded"]:
        return 3
    remaining = int(data["deadline"]) - tick - service
    if remaining < 0:
        return 0
    if remaining < 20:
        return 1
    if remaining < 40:
        return 2
    return 3


def compact_private_key(crew: str, info: dict[str, Any]) -> tuple[Any, ...]:
    """Private key shared by the compact Q baseline and CTDE actors."""

    roles = info["crew_roles"][crew]
    tick = int(info["tick"])
    phase = 1 if info["phase"] == "replan" else 0
    phase_tick = tick if phase == 0 else max(0, tick - 100)
    values: list[Any] = [
        phase,
        1 if info["crew_b_available"] else 0,
        -1 if info["orphaned_role"] is None else ROLES.index(info["orphaned_role"]),
        min(3, phase_tick // 25),
    ]
    service_key = "service_a" if crew == "a" else "service_b"
    for role in ROLES:
        data = roles[role]
        if not data["known"]:
            status = 3
            outage_bucket = 0
            service_bucket = 0
            slack_bucket = 3
        else:
            if data["failed"]:
                status = 2
            elif data["degraded"]:
                status = 1
            else:
                status = 0
            outage_bucket = min(2, int(data["outage"]) // 4)
            service = int(data[service_key])
            service_bucket = min(3, service // 30)
            slack_bucket = _slack_bucket(data, service, tick)
        values.extend([status, outage_bucket, service_bucket, slack_bucket])
    return tuple(values)


class CompactIndependentQPolicy(IndependentQPolicy):
    """Per-crew Q over phase-relative time, service, and deadline slack.

    The old state encoded absolute tick/distance buckets. This state keeps the
    decision variables that determine feasibility: own service time and the
    slack before a degraded role fails.
    """

    name = "compact_q"

    def _key(self, crew: str, info: dict[str, Any]) -> tuple[Any, ...]:
        return compact_private_key(crew, info)


class IndependentQEnsemblePolicy:
    """Mean action value across several independent per-crew Q policies."""

    name = "compact_ensemble"

    def __init__(self, policies: list[IndependentQPolicy]) -> None:
        if not policies:
            raise ValueError("an ensemble needs at least one policy")
        self.policies = policies

    def act(
        self,
        crew: str,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        values = np.mean(
            [
                np.where(
                    mask,
                    policy._values(crew, policy._key(crew, info)),
                    -np.inf,
                )
                for policy in self.policies
            ],
            axis=0,
        )
        return int(np.argmax(values))


class CTDEActor:
    """Tabular per-crew policy over the compact private key."""

    def __init__(self) -> None:
        self.counts: dict[tuple[Any, ...], np.ndarray] = {}

    def _values(self, key: tuple[Any, ...]) -> np.ndarray:
        if key not in self.counts:
            self.counts[key] = np.zeros(4, dtype=np.float64)
        return self.counts[key]

    def probabilities(
        self,
        key: tuple[Any, ...],
        mask: np.ndarray,
    ) -> np.ndarray:
        values = np.zeros(4, dtype=np.float64)
        values[mask] = self._values(key)[mask] + 1.0
        total = float(values.sum())
        if total <= 0.0:
            values[mask] = 1.0 / max(1, int(mask.sum()))
            return values
        values /= total
        return values

    def act(self, key: tuple[Any, ...], mask: np.ndarray) -> int:
        values = np.where(mask, self._values(key), -np.inf)
        return int(np.argmax(values))

    def update(self, key: tuple[Any, ...], action: int) -> None:
        values = self._values(key)
        values *= 0.999
        values[action] += 1.0


class CTDEPolicy:
    """Decentralized execution from two CTDE actors."""

    name = "ctde"

    def __init__(self, actors: dict[str, CTDEActor]) -> None:
        self.actors = actors

    def act(
        self,
        crew: str,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return self.actors[crew].act(compact_private_key(crew, info), mask)


def central_global_key(info: dict[str, Any]) -> tuple[Any, ...]:
    """Compact full-state key used by the centralized critic."""

    roles = info["roles"]
    tick = int(info["tick"])
    phase = 1 if info["phase"] == "replan" else 0
    phase_tick = tick if phase == 0 else max(0, tick - 100)
    values: list[Any] = [
        phase,
        1 if info["crew_b_available"] else 0,
        -1 if info["orphaned_role"] is None else ROLES.index(info["orphaned_role"]),
        min(3, phase_tick // 25),
    ]
    for role in ROLES:
        data = roles[role]
        status = 2 if data["failed"] else 1 if data["degraded"] else 0
        values.extend(
            [
                status,
                min(2, int(data["outage"]) // 4),
                min(3, int(data["service_a"]) // 30),
                min(3, int(data["service_b"]) // 30),
                _slack_bucket(data, int(data["service_a"]), tick),
                _slack_bucket(data, int(data["service_b"]), tick),
            ]
        )
    return tuple(values)


def _joint_index(crew: str, own_action: int, other_action: int) -> int:
    if crew == "a":
        return own_action * 4 + other_action
    return other_action * 4 + own_action


def train_ctde_actors(
    env: DecentralizedVisibilityEnv,
    *,
    episodes: int = 1000,
    seed: int = 0,
    train_seed_start: int = 60000,
    warmup_episodes: int = 50,
    alpha: float = 0.2,
    gamma: float = 0.95,
) -> tuple[CTDEPolicy, dict[tuple[Any, ...], np.ndarray]]:
    """Train a centralized tabular critic and two decentralized actors."""

    if episodes <= 0:
        raise ValueError("episodes must be positive")
    if warmup_episodes < 0:
        raise ValueError("warmup episodes must be non-negative")
    rng = random.Random(seed)
    actors = {"a": CTDEActor(), "b": CTDEActor()}
    critic: dict[tuple[Any, ...], np.ndarray] = {}
    for episode in range(episodes):
        info = env.reset(seed=train_seed_start + seed + episode)
        global_info = env.base._info()
        epsilon = 1.0 - 0.95 * episode / max(1, episodes - 1)
        done = False
        while not done:
            keys = {
                crew: compact_private_key(crew, env.agent_info(crew, info))
                for crew in ("a", "b")
            }
            masks = {
                crew: env.agent_mask(crew, info) for crew in ("a", "b")
            }
            choices: dict[str, int] = {}
            for crew in ("a", "b"):
                if rng.random() < epsilon:
                    legal = np.flatnonzero(masks[crew])
                    choices[crew] = int(rng.choice(legal.tolist()))
                else:
                    choices[crew] = actors[crew].act(
                        keys[crew], masks[crew]
                    )
            state_key = central_global_key(global_info)
            values = critic.setdefault(
                state_key, np.zeros(16, dtype=np.float64)
            )
            joint = _joint_index("a", choices["a"], choices["b"])
            info, reward, terminated, truncated, _ = env.step(choices)
            done = terminated or truncated
            next_global = env.base._info()
            target = float(reward)
            if not done:
                next_key = central_global_key(next_global)
                next_values = critic.setdefault(
                    next_key, np.zeros(16, dtype=np.float64)
                )
                next_mask = env.base.action_mask()
                target += gamma * float(
                    np.max(np.where(next_mask, next_values, -np.inf))
                )
            values[joint] += alpha * (target - values[joint])

            if episode >= warmup_episodes:
                for crew, other in (("a", "b"), ("b", "a")):
                    own_mask = masks[crew]
                    other_probs = actors[other].probabilities(
                        keys[other], masks[other]
                    )
                    marginals = np.zeros(4, dtype=np.float64)
                    for own_action in np.flatnonzero(own_mask):
                        total = 0.0
                        for other_action in np.flatnonzero(masks[other]):
                            total += float(
                                other_probs[other_action]
                                * values[
                                    _joint_index(
                                        crew,
                                        int(own_action),
                                        int(other_action),
                                    )
                                ]
                            )
                        marginals[own_action] = total
                    best = int(
                        np.argmax(np.where(own_mask, marginals, -np.inf))
                    )
                    actors[crew].update(keys[crew], best)
    return CTDEPolicy(actors), critic


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


def run_decentralized_compact(
    config: FactoryConfig,
    replan: CrewReplanConfig,
    *,
    seeds: tuple[int, ...] = (56000, 56001, 56002, 56003, 56004),
    q_seeds: tuple[int, ...] = (0, 1, 2),
    train_episodes: int = 1000,
    train_seed_start: int = 60000,
    radius: int = 16,
) -> dict[str, dict[str, Any]]:
    """Compare old and compact per-crew Q at equal training budget."""

    if not seeds:
        raise ValueError("evaluation seeds must not be empty")
    if not q_seeds:
        raise ValueError("Q seeds must not be empty")
    if train_episodes <= 0:
        raise ValueError("training episodes must be positive")

    env = DecentralizedVisibilityEnv(config, replan, radius=radius)
    results: dict[str, dict[str, Any]] = {}
    for name, local_policy in (
        ("local_nearest", LocalNearestPolicy()),
        ("local_greedy", LocalGreedyPolicy()),
        ("local_aware", LocalAwarePolicy()),
    ):
        results[name] = _pool_decentralized(
            [evaluate_crew_policy(env, local_policy, seed) for seed in seeds]
        )

    old_metrics: list[DecentralizedMetrics] = []
    for q_seed in q_seeds:
        old_policy = IndependentQPolicy()
        old_policy.train(
            env,
            episodes=train_episodes,
            seed=q_seed,
            train_seed_start=train_seed_start + q_seed * 1000,
        )
        old_metrics.extend(
            evaluate_crew_policy(env, old_policy, seed) for seed in seeds
        )
    results["private_q_1000"] = _pool_decentralized(old_metrics)

    compact_policies: list[IndependentQPolicy] = []
    compact_metrics: list[DecentralizedMetrics] = []
    compact_per_policy: dict[str, dict[str, Any]] = {}
    for q_seed in q_seeds:
        compact_policy = CompactIndependentQPolicy()
        compact_policy.train(
            env,
            episodes=train_episodes,
            seed=q_seed,
            train_seed_start=train_seed_start + q_seed * 1000,
        )
        compact_policies.append(compact_policy)
        metrics = [
            evaluate_crew_policy(env, compact_policy, seed) for seed in seeds
        ]
        compact_metrics.extend(metrics)
        compact_per_policy[str(q_seed)] = _pool_decentralized(metrics)
    results["compact_q"] = _pool_decentralized(compact_metrics)
    results["compact_q"]["per_policy"] = compact_per_policy

    ensemble = IndependentQEnsemblePolicy(compact_policies)
    results["compact_ensemble"] = _pool_decentralized(
        [evaluate_crew_policy(env, ensemble, seed) for seed in seeds]
    )
    results["global_oracle"] = _global_oracle(config, replan, seeds)
    return results


def _best_local(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return max(
        (results[name] for name in ("local_nearest", "local_greedy", "local_aware")),
        key=lambda row: float(row["mean_score"]),
    )


def run_decentralized_ctde(
    config: FactoryConfig,
    replan: CrewReplanConfig,
    *,
    seeds: tuple[int, ...] = (56000, 56001, 56002, 56003, 56004),
    q_seeds: tuple[int, ...] = (0, 1, 2),
    train_episodes: int = 1000,
    train_seed_start: int = 60000,
    warmup_episodes: int = 50,
    radius: int = 16,
) -> dict[str, dict[str, Any]]:
    """Train a centralized critic with decentralized actors on triage."""

    if not seeds:
        raise ValueError("evaluation seeds must not be empty")
    if not q_seeds:
        raise ValueError("Q seeds must not be empty")

    env = DecentralizedVisibilityEnv(config, replan, radius=radius)
    results: dict[str, dict[str, Any]] = {}
    for name, local_policy in (
        ("local_nearest", LocalNearestPolicy()),
        ("local_greedy", LocalGreedyPolicy()),
        ("local_aware", LocalAwarePolicy()),
    ):
        results[name] = _pool_decentralized(
            [evaluate_crew_policy(env, local_policy, seed) for seed in seeds]
        )

    ctde_metrics: list[DecentralizedMetrics] = []
    ctde_per_policy: dict[str, dict[str, Any]] = {}
    for q_seed in q_seeds:
        policy, _ = train_ctde_actors(
            env,
            episodes=train_episodes,
            seed=q_seed,
            train_seed_start=train_seed_start + q_seed * 1000,
            warmup_episodes=warmup_episodes,
        )
        metrics = [
            evaluate_crew_policy(env, policy, seed) for seed in seeds
        ]
        ctde_metrics.extend(metrics)
        ctde_per_policy[str(q_seed)] = _pool_decentralized(metrics)
    results["ctde"] = _pool_decentralized(ctde_metrics)
    results["ctde"]["per_policy"] = ctde_per_policy
    results["global_oracle"] = _global_oracle(config, replan, seeds)
    return results


def write_decentralized_ctde_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "decentralized_ctde_results.json").write_text(
        json.dumps(
            {"config": config, "results": results},
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    local = _best_local(results)
    oracle = results["global_oracle"]
    ctde = results["ctde"]
    lines = [
        "# Decentralized private-view triage — CTDE",
        "",
        f"Radius {config['radius']}; success ≥ {config['success_score']}; "
        f"Q seeds {config['q_seeds']}; {config['train_episodes']} training "
        "episodes per seed; centralized critic, decentralized actors.",
        "",
        "| policy | mean score | 95% CI | success |",
        "|---|---:|---:|---:|",
    ]
    for name in (
        "local_nearest",
        "local_greedy",
        "local_aware",
        "ctde",
        "global_oracle",
    ):
        result = results[name]
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            f"- local/global gap: {oracle['mean_score'] - local['mean_score']:.2f}",
            f"- CTDE gain over best local: "
            f"{ctde['mean_score'] - local['mean_score']:.2f}",
            f"- CTDE gap to oracle: "
            f"{oracle['mean_score'] - ctde['mean_score']:.2f}",
            "",
            "## CTDE per policy",
            "",
            "| Q seed | mean score | success |",
            "|---|---:|---:|",
        ]
    )
    for q_seed, result in ctde["per_policy"].items():
        lines.append(
            f"| {q_seed} | {result['mean_score']:.2f} | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            "0081 reference: private Q and compact Q both scored 616/0.40; "
            "the compact ensemble was 616/0.40.",
        ]
    )
    (out / "decentralized_ctde_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "decentralized_ctde_report.md"


def write_decentralized_compact_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "decentralized_compact_results.json").write_text(
        json.dumps(
            {"config": config, "results": results},
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    local = _best_local(results)
    oracle = results["global_oracle"]
    compact = results["compact_q"]
    ensemble = results["compact_ensemble"]
    lines = [
        "# Decentralized private-view triage — compact Q",
        "",
        f"Radius {config['radius']}; success ≥ {config['success_score']}; "
        f"Q seeds {config['q_seeds']}; {config['train_episodes']} training "
        "episodes per seed.",
        "",
        "| policy | mean score | 95% CI | success |",
        "|---|---:|---:|---:|",
    ]
    for name in (
        "local_nearest",
        "local_greedy",
        "local_aware",
        "private_q_1000",
        "compact_q",
        "compact_ensemble",
        "global_oracle",
    ):
        result = results[name]
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            f"- local/global gap: {oracle['mean_score'] - local['mean_score']:.2f}",
            f"- compact gain over best local: "
            f"{compact['mean_score'] - local['mean_score']:.2f}",
            f"- ensemble gain over compact: "
            f"{ensemble['mean_score'] - compact['mean_score']:.2f}",
            f"- compact gap to oracle: "
            f"{oracle['mean_score'] - compact['mean_score']:.2f}",
            "",
            "## Compact Q per policy",
            "",
            "| Q seed | mean score | success |",
            "|---|---:|---:|",
        ]
    )
    for q_seed, result in compact["per_policy"].items():
        lines.append(
            f"| {q_seed} | {result['mean_score']:.2f} | "
            f"{result['success_rate']:.2f} |"
        )
    (out / "decentralized_compact_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "decentralized_compact_report.md"


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
