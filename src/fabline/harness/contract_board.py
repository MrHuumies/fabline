"""Policies and evaluation for the gear-contract board."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.contract_board import ContractBoardEnv
from fabline.harness.recipe import BufferAwarePolicy
from fabline.harness.stats import bootstrap_mean_ci


class BoardPolicy(Protocol):
    name: str

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int: ...


class FixedContractPolicy:
    def __init__(self, index: int) -> None:
        self.index = index
        self.name = f"contract{index}"
        self.recipe = BufferAwarePolicy(2)

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "choose":
            return self.index
        return self.recipe.act(observation, info, mask)


class HighestRewardPolicy:
    name = "highest_reward"

    def __init__(self) -> None:
        self.recipe = BufferAwarePolicy(2)

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "choose":
            return max(
                range(3), key=lambda index: info["contracts"][index][2]
            )
        return self.recipe.act(observation, info, mask)


class BoardAwarePolicy:
    name = "board_aware"

    def __init__(self, ticks_per_gear: int = 16) -> None:
        self.ticks_per_gear = ticks_per_gear
        self.recipe = BufferAwarePolicy(2)

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "choose":
            feasible = [
                index
                for index, (target, deadline, _) in enumerate(
                    info["contracts"]
                )
                if target * self.ticks_per_gear <= deadline
            ]
            if feasible:
                return max(
                    feasible,
                    key=lambda index: info["contracts"][index][2],
                )
            return max(
                range(3), key=lambda index: info["contracts"][index][2]
            )
        return self.recipe.act(observation, info, mask)


class RandomContractPolicy:
    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)
        self.recipe = BufferAwarePolicy(2)

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "choose":
            return self.rng.randrange(3)
        return self.recipe.act(observation, info, mask)


@dataclass
class BoardMetrics:
    mean_reward: float
    success_rate: float
    selected: list[int]
    rewards: list[float]
    successes: list[float]


def evaluate_policy(
    env: ContractBoardEnv,
    policy: BoardPolicy,
    episodes: int = 5,
    seed: int = 0,
) -> BoardMetrics:
    rewards: list[float] = []
    successes: list[float] = []
    selected: list[int] = []
    for episode in range(episodes):
        observation, info = env.reset(seed=seed + episode)
        done = False
        total_reward = 0.0
        while not done:
            action = policy.act(observation, info, env.action_mask())
            observation, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            done = terminated or truncated
        rewards.append(total_reward)
        successes.append(1.0 if info["success"] else 0.0)
        selected.append(-1 if info["selected"] is None else info["selected"])
    return BoardMetrics(
        mean_reward=float(np.mean(rewards)),
        success_rate=float(np.mean(successes)),
        selected=selected,
        rewards=rewards,
        successes=successes,
    )


def _pool(metrics: list[BoardMetrics]) -> dict[str, Any]:
    rewards = [value for item in metrics for value in item.rewards]
    return {
        "mean_reward": float(np.mean(rewards)),
        "score_ci": list(bootstrap_mean_ci(rewards)),
        "success_rate": float(
            np.mean([item.success_rate for item in metrics])
        ),
        "selected": [
            value for item in metrics for value in item.selected
        ],
        "per_seed": [
            {
                "rewards": item.rewards,
                "successes": item.successes,
                "selected": item.selected,
            }
            for item in metrics
        ],
    }


def run_contract_board(
    env: ContractBoardEnv,
    *,
    seeds: tuple[int, ...] = (0, 1, 2),
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for name, policy in (
        ("contract0", FixedContractPolicy(0)),
        ("contract1", FixedContractPolicy(1)),
        ("contract2", FixedContractPolicy(2)),
        ("highest_reward", HighestRewardPolicy()),
        ("board_aware", BoardAwarePolicy()),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, policy, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    results["random"] = _pool(
        [
            evaluate_policy(
                env, RandomContractPolicy(seed=seed), episodes=1, seed=seed
            )
            for seed in seeds
        ]
    )
    oracle_metrics: list[BoardMetrics] = []
    oracle_selected: list[int] = []
    for seed in seeds:
        candidates = [
            evaluate_policy(
                env, FixedContractPolicy(index), episodes=1, seed=seed
            )
            for index in range(3)
        ]
        best_index = max(
            range(3), key=lambda index: candidates[index].mean_reward
        )
        oracle_metrics.append(candidates[best_index])
        oracle_selected.append(best_index)
    results["oracle"] = _pool(oracle_metrics)
    results["oracle"]["selected"] = oracle_selected
    return results


def write_board_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "contract_board_results.json").write_text(
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
        "# Contract board",
        "",
        f"Boards: {len(config['boards'])}; seeds {config['seeds']}.",
        "",
        "| policy | mean reward | 95% CI | success | selected |",
        "|---|---:|---:|---:|---|",
    ]
    for name, result in results.items():
        selected = ", ".join(str(value) for value in result["selected"])
        lines.append(
            f"| {name} | {result['mean_reward']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['success_rate']:.2f} | {selected} |"
        )
    (out / "contract_board_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "contract_board_report.md"
