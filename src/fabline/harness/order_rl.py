"""Optional Torch baselines for order control: BC and PPO."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.orders import OrderControlConfig, OrderControlEnv
from fabline.harness.order_control import (
    EDFPolicy,
    OrderMetrics,
    OrderPolicy,
    RandomPolicy,
    TabularQPolicy,
    ValuePolicy,
    _pool,
    evaluate_order_policy,
)
from fabline.worlds.factory.config import FactoryConfig


@dataclass(frozen=True)
class OrderRLConfig:
    train_seed_start: int = 75000
    eval_seeds: tuple[int, ...] = (76000, 76001, 76002, 76003, 76004)
    bc_episodes: int = 100
    ppo_seeds: tuple[int, ...] = (0, 1, 2)
    ppo_steps: int = 10_000
    ppo_rollout: int = 2_048
    ppo_epochs: int = 4
    hidden: int = 64
    bc_epochs: int = 60
    success_value: int = 160

    def __post_init__(self) -> None:
        if self.bc_episodes <= 0 or not self.ppo_seeds:
            raise ValueError("BC episodes and PPO seeds must be positive")
        if self.ppo_steps <= 0 or self.ppo_rollout <= 0:
            raise ValueError("PPO budgets must be positive")
        if self.ppo_epochs <= 0 or self.hidden <= 0 or self.bc_epochs <= 0:
            raise ValueError("model budgets must be positive")


@lru_cache(maxsize=1)
def _torch() -> Any:
    try:
        import torch

        torch.set_num_threads(1)
        return torch
    except ImportError as exc:  # pragma: no cover - optional path
        raise RuntimeError(
            "order-rl requires the optional train extra: "
            ".tools/uv pip install --python .venv/bin/python -e '.[train]'"
        ) from exc


class TorchPolicy:
    def __init__(
        self,
        model: Any,
        mean: np.ndarray,
        scale: np.ndarray,
        *,
        name: str = "torch",
    ) -> None:
        self.model = model
        self.mean = mean
        self.scale = scale
        self.name = name

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        torch = _torch()
        x = (np.asarray(observation, dtype=np.float32) - self.mean) / self.scale
        with torch.no_grad():
            output = self.model(torch.as_tensor(x).unsqueeze(0))
        logits = output[0] if isinstance(output, tuple) else output
        return int(torch.argmax(logits, dim=-1).item())


def collect_demonstrations(
    env: OrderControlEnv,
    policy: OrderPolicy,
    *,
    seeds: tuple[int, ...],
    episodes_per_seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    states: list[np.ndarray] = []
    actions: list[int] = []
    for seed in seeds:
        for episode in range(episodes_per_seed):
            observation, info = env.reset(seed=seed + episode)
            done = False
            while not done:
                action = policy.act(observation, info)
                states.append(observation.copy())
                actions.append(action)
                observation, _, terminated, truncated, info = env.step(action)
                done = terminated or truncated
    return np.stack(states), np.asarray(actions, dtype=np.int64)


def train_bc(
    env: OrderControlEnv,
    cfg: OrderRLConfig,
) -> tuple[TorchPolicy, dict[str, Any]]:
    torch = _torch()
    train_seeds = tuple(
        cfg.train_seed_start + index for index in range(5)
    )
    states, actions = collect_demonstrations(
        env,
        ValuePolicy(),
        seeds=train_seeds,
        episodes_per_seed=max(1, cfg.bc_episodes // len(train_seeds)),
    )
    mean = states.mean(axis=0)
    scale = states.std(axis=0)
    scale[scale < 1e-6] = 1.0
    x = torch.as_tensor(
        ((states - mean) / scale), dtype=torch.float32
    )
    y = torch.as_tensor(actions, dtype=torch.long)
    model = torch.nn.Sequential(
        torch.nn.Linear(states.shape[1], cfg.hidden),
        torch.nn.ReLU(),
        torch.nn.Linear(cfg.hidden, 2),
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    start = time.perf_counter()
    for _ in range(cfg.bc_epochs):
        permutation = torch.randperm(len(x))
        for offset in range(0, len(x), 64):
            batch = permutation[offset : offset + 64]
            logits = model(x[batch])
            loss = torch.nn.functional.cross_entropy(logits, y[batch])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    seconds = time.perf_counter() - start
    parameters = sum(p.numel() for p in model.parameters())
    return TorchPolicy(model, mean, scale, name="bc"), {
        "train_seconds": seconds,
        "parameters": parameters,
        "samples": int(len(x)),
    }


def train_ppo(
    env: OrderControlEnv,
    cfg: OrderRLConfig,
    seed: int,
) -> tuple[TorchPolicy, dict[str, Any]]:
    torch = _torch()
    from torch import nn

    class ActorCritic(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.body = nn.Sequential(
                nn.Linear(16, cfg.hidden),
                nn.Tanh(),
            )
            self.actor = nn.Linear(cfg.hidden, 2)
            self.critic = nn.Linear(cfg.hidden, 1)

        def forward(self, x: Any) -> tuple[Any, Any]:
            features = self.body(x)
            return self.actor(features), self.critic(features).squeeze(-1)

    model = ActorCritic()
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    start = time.perf_counter()
    steps = 0
    update = 0
    while steps < cfg.ppo_steps:
        obs_buf: list[Any] = []
        act_buf: list[Any] = []
        logp_buf: list[Any] = []
        rew_buf: list[float] = []
        done_buf: list[bool] = []
        val_buf: list[float] = []
        observation, _ = env.reset(
            seed=cfg.train_seed_start + seed * 1000 + update
        )
        for _ in range(min(cfg.ppo_rollout, cfg.ppo_steps - steps)):
            x = torch.as_tensor(observation, dtype=torch.float32)
            logits, value = model(x)
            dist = torch.distributions.Categorical(logits=logits)
            action = dist.sample()
            observation, reward, terminated, truncated, _ = env.step(
                int(action.item())
            )
            done = terminated or truncated
            obs_buf.append(x)
            act_buf.append(action)
            logp_buf.append(dist.log_prob(action).detach())
            rew_buf.append(float(reward))
            done_buf.append(done)
            val_buf.append(float(value.item()))
            steps += 1
            if done:
                observation, _ = env.reset(
                    seed=cfg.train_seed_start
                    + seed * 1000
                    + update
                    + steps
                )
        values = torch.as_tensor(val_buf, dtype=torch.float32)
        rewards = torch.as_tensor(rew_buf, dtype=torch.float32)
        dones = torch.as_tensor(done_buf, dtype=torch.float32)
        advantages = torch.zeros_like(rewards)
        last = 0.0
        for index in range(len(rewards) - 1, -1, -1):
            next_value = values[index + 1] if index + 1 < len(values) else 0.0
            delta = (
                rewards[index]
                + 0.99 * next_value * (1.0 - dones[index])
                - values[index]
            )
            last = (
                delta
                + 0.99 * 0.95 * (1.0 - dones[index]) * last
            )
            advantages[index] = last
        returns = advantages + values
        advantages = (advantages - advantages.mean()) / (
            advantages.std() + 1e-8
        )
        old_logp = torch.stack(logp_buf)
        old_actions = torch.stack(act_buf)
        old_obs = torch.stack(obs_buf)
        for _ in range(cfg.ppo_epochs):
            permutation = torch.randperm(len(old_obs))
            for offset in range(0, len(old_obs), 64):
                batch = permutation[offset : offset + 64]
                logits, value = model(old_obs[batch])
                dist = torch.distributions.Categorical(logits=logits)
                logp = dist.log_prob(old_actions[batch])
                ratio = torch.exp(logp - old_logp[batch])
                clipped = torch.clamp(ratio, 0.8, 1.2)
                actor_loss = -torch.min(
                    ratio * advantages[batch],
                    clipped * advantages[batch],
                ).mean()
                critic_loss = torch.nn.functional.mse_loss(
                    value, returns[batch]
                )
                entropy = dist.entropy().mean()
                loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        update += 1
    seconds = time.perf_counter() - start
    parameters = sum(p.numel() for p in model.parameters())
    mean = np.zeros(16, dtype=np.float32)
    scale = np.ones(16, dtype=np.float32)
    return TorchPolicy(model, mean, scale, name="bc"), {
        "train_seconds": seconds,
        "parameters": parameters,
        "samples": steps,
    }


def run_order_rl(
    config: FactoryConfig,
    orders: OrderControlConfig | None = None,
    cfg: OrderRLConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or OrderRLConfig()
    env = OrderControlEnv(config, orders=orders)
    results: dict[str, dict[str, Any]] = {}
    for name, policy in (
        ("edf", EDFPolicy()),
        ("value", ValuePolicy()),
        ("random", RandomPolicy(0)),
    ):
        results[name] = _pool(
            [
                evaluate_order_policy(
                    env, policy, episodes=5, seed=seed
                )
                for seed in cfg.eval_seeds
            ]
        )
    q = TabularQPolicy()
    results["tabular_q"] = _pool(
        [
            evaluate_order_policy(
                env,
                q,
                episodes=5,
                seed=seed,
                train_episodes=100,
            )
            for seed in cfg.eval_seeds
        ]
    )
    bc, bc_meta = train_bc(env, cfg)
    results["bc"] = _pool(
        [
            evaluate_order_policy(env, bc, episodes=5, seed=seed)
            for seed in cfg.eval_seeds
        ]
    )
    results["bc"]["model"] = bc_meta
    ppo_metrics: list[OrderMetrics] = []
    ppo_meta = []
    for ppo_seed in cfg.ppo_seeds:
        ppo_policy, meta = train_ppo(env, cfg, ppo_seed)
        ppo_meta.append(meta)
        ppo_metrics.extend(
            evaluate_order_policy(
                env, ppo_policy, episodes=5, seed=seed
            )
            for seed in cfg.eval_seeds
        )
    results["ppo"] = _pool(ppo_metrics)
    results["ppo"]["model"] = {
        "train_seconds": float(
            np.mean([item["train_seconds"] for item in ppo_meta])
        ),
        "parameters": int(ppo_meta[0]["parameters"]),
        "samples": int(np.mean([item["samples"] for item in ppo_meta])),
    }
    return {
        "task": "factory.orders.control.v1",
        "config": {
            "train_seed_start": cfg.train_seed_start,
            "eval_seeds": list(cfg.eval_seeds),
            "ppo_seeds": list(cfg.ppo_seeds),
            "ppo_steps": cfg.ppo_steps,
            "bc_episodes": cfg.bc_episodes,
        },
        "results": results,
    }


def write_order_rl_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "order_rl_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Order-control RL baselines",
        "",
        "| policy | value | success | train s | parameters |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in report["results"].items():
        model = row.get("model", {})
        lines.append(
            f"| {name} | {row['mean_value']:.2f} | "
            f"{row['success_rate']:.2f} | "
            f"{model.get('train_seconds', 0.0):.2f} | "
            f"{model.get('parameters', '-')} |"
        )
    (out / "order_rl_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "order_rl_report.md"
