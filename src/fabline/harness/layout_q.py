"""Compact layout-aware tabular Q for the crew assignment tasks."""

from __future__ import annotations

import random
from collections import Counter
from typing import Any, Protocol

import numpy as np

from fabline.env.multi_crew import CHOICES, ROLES


class LayoutQEnv(Protocol):
    n_actions: int

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]: ...

    def step(
        self, action: int
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]: ...

    def action_mask(self) -> np.ndarray: ...


class CompactQPolicy:
    """Tabular Q over relative geometry and reachability bins.

    The key encodes which crew is closer to the two positive bridges and
    whether each crew can finish before the relevant deadline or recall. This
    avoids the fragmented absolute-distance/tick state of the earlier tabular
    baseline.
    """

    name = "compact_q"

    def __init__(self) -> None:
        self.q: dict[tuple[int, ...], np.ndarray] = {}

    def _key(self, info: dict[str, Any]) -> tuple[int, ...]:
        orphan = info.get("orphaned_role")
        if info.get("phase") == "replan":
            return (
                1,
                -1 if orphan is None else ROLES.index(orphan),
            )

        def closer(role: str) -> int:
            wire = info["roles"][role]
            if wire["distance_a"] < wire["distance_b"]:
                return 0
            if wire["distance_a"] > wire["distance_b"]:
                return 2
            return 1

        def can(crew: str, role: str) -> int:
            wire = info["roles"][role]
            service = wire[f"service_{crew}"]
            if info.get("phase") == "initial" and info.get("recall_tick"):
                limit = max(0, int(info["recall_tick"]) - int(info["tick"]))
            else:
                limit = max(
                    0,
                    int(wire["deadline"]) - int(info["tick"]),
                )
            return 1 if service <= limit else 0

        return (
            0,
            closer("small"),
            closer("large"),
            can("a", "small"),
            can("a", "large"),
            can("b", "small"),
            can("b", "large"),
        )

    def _values(self, key: tuple[int, ...]) -> np.ndarray:
        if key not in self.q:
            self.q[key] = np.zeros(CHOICES * CHOICES, dtype=np.float64)
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
        env: LayoutQEnv,
        *,
        episodes: int = 1000,
        seed: int = 0,
        train_seed_start: int = 80000,
        alpha: float = 0.2,
        gamma: float = 0.9,
        reward_scale: float = 500.0,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            try:
                observation, info = env.reset(
                    seed=train_seed_start + episode
                )
            except RuntimeError:
                continue
            epsilon = 1.0 - 0.95 * episode / max(1, episodes - 1)
            done = False
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
                target = reward / reward_scale
                if not done:
                    next_key = self._key(info)
                    next_mask = env.action_mask()
                    target += gamma * float(
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


class EnsembleQPolicy:
    """Combine several compact-Q policies by mean value or majority vote."""

    name = "ensemble_q"

    def __init__(
        self,
        policies: list[CompactQPolicy],
        *,
        mode: str = "mean",
    ) -> None:
        if not policies:
            raise ValueError("an ensemble needs at least one policy")
        if mode not in {"mean", "vote"}:
            raise ValueError("ensemble mode must be 'mean' or 'vote'")
        self.policies = policies
        self.mode = mode

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if self.mode == "vote":
            actions = [
                policy.act(observation, info, mask)
                for policy in self.policies
            ]
            counts = Counter(actions)
            best = max(counts.values())
            for action in actions:
                if counts[action] == best:
                    return action
            return actions[0]
        values = np.mean(
            [
                np.where(
                    mask,
                    policy._values(policy._key(info)),
                    -np.inf,
                )
                for policy in self.policies
            ],
            axis=0,
        )
        return int(np.argmax(values))
