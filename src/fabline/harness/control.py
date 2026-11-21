"""Control policies and evaluation for the line-building task."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from fabline.env.control import ControlConfig, ControlEnv, MacroAction
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class ControlPolicy(Protocol):
    name: str

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int: ...


class ScriptedControlPolicy:
    name = "scripted"

    _SEQUENCE = (
        MacroAction.BUILD_MINER,
        MacroAction.BUILD_BELT,
        MacroAction.BUILD_FURNACE,
        MacroAction.BUILD_BELT,
        MacroAction.BUILD_ASSEMBLER,
        MacroAction.BUILD_BELT,
    )

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        index = int(info["path_index"])
        if index < len(self._SEQUENCE):
            action = int(self._SEQUENCE[index])
            if mask[action]:
                return action
        legal = np.flatnonzero(mask)
        return int(legal[0]) if len(legal) else int(MacroAction.NOOP)


class RandomControlPolicy:
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
        if not len(legal):
            return int(MacroAction.NOOP)
        return int(self.rng.choice(legal.tolist()))


class TabularQPolicy:
    name = "tabular_q"

    def __init__(self) -> None:
        self.q: dict[tuple[int, tuple[int, ...]], np.ndarray] = {}

    def _key(self, info: dict[str, Any]) -> tuple[int, tuple[int, ...]]:
        return (int(info["path_index"]), tuple(int(value) for value in info["path_types"]))

    def _values(self, key: tuple[int, tuple[int, ...]]) -> np.ndarray:
        if key not in self.q:
            # Optimistic initialization for non-noop actions: the agent tries to
            # build before it learns that noop is the safe default.
            values = np.ones(len(MacroAction), dtype=np.float64)
            values[int(MacroAction.NOOP)] = 0.0
            self.q[key] = values
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
        env: ControlEnv,
        episodes: int = 100,
        seed: int = 0,
        alpha: float = 0.2,
        gamma: float = 0.95,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            observation, info = env.reset(seed=episode)
            done = False
            epsilon = epsilon_start + (epsilon_end - epsilon_start) * (
                episode / max(1, episodes - 1)
            )
            while not done:
                mask = env.action_mask()
                key = self._key(info)
                if rng.random() < epsilon:
                    legal = np.flatnonzero(mask)
                    action = int(rng.choice(legal.tolist()))
                else:
                    action = self.act(observation, info, mask)
                observation, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                next_key = self._key(info)
                target = reward
                if not done:
                    next_mask = env.action_mask()
                    target += gamma * float(
                        np.max(np.where(next_mask, self._values(next_key), -np.inf))
                    )
                values = self._values(key)
                values[action] += alpha * (target - values[action])


class BehaviorCloningPolicy:
    name = "behavior_cloning"

    def __init__(self, seed: int = 0) -> None:
        from sklearn.tree import DecisionTreeClassifier

        self.model = DecisionTreeClassifier(max_depth=8, random_state=seed)
        self.scripted = ScriptedControlPolicy()

    def fit(
        self,
        observations: np.ndarray,
        actions: np.ndarray,
    ) -> None:
        self.model.fit(
            np.asarray(observations),
            np.asarray(actions),
        )

    def collect(
        self,
        env: ControlEnv,
        episodes: int = 50,
        seed: int = 0,
        explore: float = 0.2,
    ) -> None:
        rng = random.Random(seed)
        observations: list[np.ndarray] = []
        actions: list[int] = []
        for episode in range(episodes):
            observation, info = env.reset(seed=episode)
            done = False
            while not done:
                mask = env.action_mask()
                expert = self.scripted.act(observation, info, mask)
                observations.append(observation)
                actions.append(expert)
                if rng.random() < explore:
                    legal = np.flatnonzero(mask)
                    action = int(rng.choice(legal.tolist()))
                else:
                    action = expert
                observation, _, terminated, truncated, info = env.step(action)
                done = terminated or truncated
        self.model.fit(np.stack(observations), np.asarray(actions))

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        predicted = int(self.model.predict(observation.reshape(1, -1))[0])
        if mask[predicted]:
            return predicted
        expert = self.scripted.act(observation, info, mask)
        if mask[expert]:
            return expert
        legal = np.flatnonzero(mask)
        return int(legal[0]) if len(legal) else int(MacroAction.NOOP)


@dataclass
class ControlMetrics:
    mean_score: float
    std_score: float
    success_rate: float
    mean_reward: float
    mean_steps: float
    path_complete_rate: float
    scores: list[float]
    rewards: list[float]
    successes: list[float]


def evaluate_policy(
    env: ControlEnv,
    policy: ControlPolicy,
    episodes: int = 5,
    seed: int = 0,
) -> ControlMetrics:
    scores: list[float] = []
    rewards: list[float] = []
    successes: list[float] = []
    steps: list[float] = []
    completed: list[float] = []
    for episode in range(episodes):
        observation, info = env.reset(seed=seed + episode)
        done = False
        total_reward = 0.0
        step_count = 0
        while not done:
            mask = env.action_mask()
            action = policy.act(observation, info, mask)
            observation, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            step_count += 1
            done = terminated or truncated
        scores.append(float(info["score"]))
        rewards.append(total_reward)
        successes.append(1.0 if info["success"] else 0.0)
        steps.append(float(step_count))
        completed.append(1.0 if info["path_complete"] else 0.0)
    return ControlMetrics(
        mean_score=float(np.mean(scores)),
        std_score=float(np.std(scores)),
        success_rate=float(np.mean(successes)),
        mean_reward=float(np.mean(rewards)),
        mean_steps=float(np.mean(steps)),
        path_complete_rate=float(np.mean(completed)),
        scores=scores,
        rewards=rewards,
        successes=successes,
    )


def _pool(metrics: list[ControlMetrics]) -> dict[str, object]:
    means = np.asarray([item.mean_score for item in metrics], dtype=np.float64)
    stds = np.asarray([item.std_score for item in metrics], dtype=np.float64)
    overall_mean = float(np.mean(means))
    overall_var = float(np.mean(stds * stds + (means - overall_mean) ** 2))
    scores = [value for item in metrics for value in item.scores]
    rewards = [value for item in metrics for value in item.rewards]
    successes = [value for item in metrics for value in item.successes]
    score_ci = bootstrap_mean_ci(scores)
    reward_ci = bootstrap_mean_ci(rewards)
    success_ci = bootstrap_mean_ci(successes)
    return {
        "mean_score": overall_mean,
        "std_score": float(np.sqrt(overall_var)),
        "success_rate": float(np.mean(successes)),
        "mean_reward": float(np.mean(rewards)),
        "mean_steps": float(np.mean([item.mean_steps for item in metrics])),
        "path_complete_rate": float(
            np.mean([item.path_complete_rate for item in metrics])
        ),
        "score_ci": list(score_ci),
        "reward_ci": list(reward_ci),
        "success_ci": list(success_ci),
    }


def evaluate_control_policies(
    config: FactoryConfig,
    control: ControlConfig,
    *,
    episodes: int = 5,
    train_episodes: int = 200,
    seeds: tuple[int, ...] = (0, 1, 2),
) -> dict[str, dict[str, object]]:
    env = ControlEnv(config, control)
    results: dict[str, dict[str, object]] = {}

    scripted_metrics = [
        evaluate_policy(env, ScriptedControlPolicy(), episodes=episodes, seed=seed)
        for seed in seeds
    ]
    results["scripted"] = _pool(scripted_metrics)

    random_metrics = [
        evaluate_policy(
            env,
            RandomControlPolicy(seed=seed),
            episodes=episodes,
            seed=seed,
        )
        for seed in seeds
    ]
    results["random"] = _pool(random_metrics)

    tabular_metrics = []
    for seed in seeds:
        tabular_policy = TabularQPolicy()
        tabular_policy.train(env, episodes=train_episodes, seed=seed)
        tabular_metrics.append(
            evaluate_policy(env, tabular_policy, episodes=episodes, seed=seed)
        )
    results["tabular_q"] = _pool(tabular_metrics)

    cloning_metrics = []
    for seed in seeds:
        cloning_policy = BehaviorCloningPolicy(seed=seed)
        cloning_policy.collect(
            env,
            episodes=max(20, train_episodes // 5),
            seed=seed,
        )
        cloning_metrics.append(
            evaluate_policy(env, cloning_policy, episodes=episodes, seed=seed)
        )
    results["behavior_cloning"] = _pool(cloning_metrics)
    return results
