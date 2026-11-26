"""Public reliability-contract selection under stochastic power.

This is the reproducible harness for `factory.power.contract.v1`. The task is
offline target selection: the agent commits to a delivery target before an
episode and is paid on the realized stochastic production score. A fixed
scripted operating policy keeps the comparison about the risk preference, not
about a second controller.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.power_allocation import PowerAllocationConfig, PowerAllocationEnv
from fabline.harness.power_allocation import AlternatePolicy
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig

RELIABILITY_CONTRACT_TASK_ID = "factory.power.contract.v1"
RELIABILITY_CONTRACT_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class ReliabilityContractConfig:
    train_blocks: tuple[int, ...] = tuple(range(600, 1000, 2))
    test_blocks: tuple[int, ...] = tuple(range(601, 1000, 2))
    episodes_per_block: int = 10
    tiers: tuple[int, ...] = tuple(range(80, 151, 5))
    hit_offset: int = 100
    miss_penalty: int = 40
    cvar_alpha: float = 0.2
    bootstrap_samples: int = 2_000
    bootstrap_seed: int = 0
    episode_ticks: int = 500
    decision_interval: int = 10
    generator_capacity: int = 5
    generator_radius: int = 8
    load_jitter: int = 60
    capacity_jitter: int = 40
    variation_period: int = 20
    power: PowerConfig = field(
        default_factory=lambda: PowerConfig(
            enabled=True,
            generator_count=1,
            generator_capacity=5,
            generator_radius=8,
            load_jitter=60,
            capacity_jitter=40,
            variation_period=20,
        )
    )

    def __post_init__(self) -> None:
        if not self.train_blocks or not self.test_blocks:
            raise ValueError("train and test blocks must not be empty")
        if set(self.train_blocks) & set(self.test_blocks):
            raise ValueError("train and test blocks must be disjoint")
        if self.episodes_per_block <= 0:
            raise ValueError("episodes_per_block must be positive")
        if not self.tiers:
            raise ValueError("tiers must not be empty")
        if any(tier <= 0 for tier in self.tiers):
            raise ValueError("tiers must be positive")
        if not 0.0 < self.cvar_alpha <= 1.0:
            raise ValueError("cvar_alpha must be in (0, 1]")
        if self.bootstrap_samples <= 0:
            raise ValueError("bootstrap_samples must be positive")
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode ticks and decision interval must be positive")


def _factory_config(cfg: ReliabilityContractConfig) -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=cfg.episode_ticks,
        decision_interval=cfg.decision_interval,
        entity_budget=32,
        rock_density=0.0,
        starter_line=True,
    )


def _allocation_config(cfg: ReliabilityContractConfig) -> PowerAllocationConfig:
    return PowerAllocationConfig(
        episode_ticks=cfg.episode_ticks,
        decision_interval=cfg.decision_interval,
        success_score=0,
        power=cfg.power,
    )


def collect_scores(cfg: ReliabilityContractConfig) -> tuple[np.ndarray, np.ndarray]:
    """Run the fixed operating policy and return scores plus block ids."""

    env = PowerAllocationEnv(_factory_config(cfg), _allocation_config(cfg))
    policy = AlternatePolicy()
    scores: list[float] = []
    blocks: list[int] = []
    for block in (*cfg.train_blocks, *cfg.test_blocks):
        for episode in range(cfg.episodes_per_block):
            seed = block * cfg.episodes_per_block + episode
            observation, info = env.reset(seed=seed)
            done = False
            while not done:
                action = policy.act(observation, info, env.action_mask())
                observation, _, terminated, truncated, info = env.step(action)
                done = terminated or truncated
            scores.append(float(info["score"]))
            blocks.append(block)
    return np.asarray(scores, dtype=np.float64), np.asarray(blocks, dtype=np.int64)


def _payoffs(scores: np.ndarray, tier: int, cfg: ReliabilityContractConfig) -> np.ndarray:
    hit = scores >= tier
    return np.where(
        hit,
        scores + float(tier - cfg.hit_offset),
        scores - float(cfg.miss_penalty),
    )


def _cvar(values: np.ndarray, alpha: float) -> float:
    if len(values) == 0:
        return 0.0
    ordered = np.sort(np.asarray(values, dtype=np.float64))
    count = max(1, int(np.ceil(alpha * len(ordered))))
    return float(ordered[:count].mean())


def _tier_metrics(
    scores: np.ndarray,
    cfg: ReliabilityContractConfig,
) -> dict[int, dict[str, float]]:
    metrics: dict[int, dict[str, float]] = {}
    for tier in cfg.tiers:
        payoff = _payoffs(scores, tier, cfg)
        metrics[tier] = {
            "mean": float(payoff.mean()),
            "cvar": _cvar(payoff, cfg.cvar_alpha),
            "worst": float(payoff.min()),
            "hit_rate": float((scores >= tier).mean()),
        }
    return metrics


def _select(metrics: dict[int, dict[str, float]], key: str) -> int:
    return max(
        metrics,
        key=lambda tier: (metrics[tier][key], -tier),
    )


def _block_bootstrap_gain(
    scores: np.ndarray,
    blocks: np.ndarray,
    mean_tier: int,
    cvar_tier: int,
    cfg: ReliabilityContractConfig,
) -> list[float]:
    rng = np.random.default_rng(cfg.bootstrap_seed)
    by_block = {
        block: scores[blocks == block] for block in sorted(set(blocks.tolist()))
    }
    unique = np.asarray(sorted(by_block), dtype=np.int64)
    gains: list[float] = []
    for _ in range(cfg.bootstrap_samples):
        sampled = rng.choice(unique, size=len(unique), replace=True)
        resampled = np.concatenate([by_block[int(block)] for block in sampled])
        mean_payoff = _payoffs(resampled, mean_tier, cfg)
        cvar_payoff = _payoffs(resampled, cvar_tier, cfg)
        gains.append(_cvar(cvar_payoff, cfg.cvar_alpha) - _cvar(mean_payoff, cfg.cvar_alpha))
    return [float(np.percentile(gains, 2.5)), float(np.percentile(gains, 97.5))]


def run_reliability_contract(
    cfg: ReliabilityContractConfig | None = None,
) -> dict[str, Any]:
    """Run the contract-selection task and return the compact report."""

    config = cfg or ReliabilityContractConfig()
    scores, blocks = collect_scores(config)
    train_mask = np.isin(blocks, np.asarray(config.train_blocks))
    test_mask = np.isin(blocks, np.asarray(config.test_blocks))
    train_scores = scores[train_mask]
    test_scores = scores[test_mask]
    train = _tier_metrics(train_scores, config)
    test = _tier_metrics(test_scores, config)
    mean_tier = _select(train, "mean")
    cvar_tier = _select(train, "cvar")
    test_mean_tier = _select(test, "mean")
    test_cvar_tier = _select(test, "cvar")
    gain = _block_bootstrap_gain(
        test_scores,
        blocks[test_mask],
        mean_tier,
        cvar_tier,
        config,
    )
    mean_metrics = test[mean_tier]
    cvar_metrics = test[cvar_tier]
    gates = {
        "H1_tradeoff": mean_tier > cvar_tier,
        "H2_mean_cost": mean_metrics["mean"] >= cvar_metrics["mean"] - 5.0,
        "H3_tail_gain": cvar_metrics["cvar"] >= mean_metrics["cvar"] + 10.0,
        "H4_direction": mean_tier > cvar_tier and test_mean_tier > test_cvar_tier,
        "H5_no_free_lunch": (
            mean_metrics["mean"] > cvar_metrics["mean"]
            and cvar_metrics["cvar"] > mean_metrics["cvar"]
        ),
    }
    return {
        "task": {
            "id": RELIABILITY_CONTRACT_TASK_ID,
            "version": RELIABILITY_CONTRACT_TASK_VERSION,
            "kind": "risk_select",
        },
        "config": asdict(config),
        "summary": {
            "train_episodes": int(len(train_scores)),
            "test_episodes": int(len(test_scores)),
            "train_mean": float(train_scores.mean()),
            "test_mean": float(test_scores.mean()),
            "train_zero_rate": float((train_scores == 0).mean()),
            "test_zero_rate": float((test_scores == 0).mean()),
        },
        "tiers": {
            "train": {str(tier): row for tier, row in train.items()},
            "test": {str(tier): row for tier, row in test.items()},
        },
        "selected": {
            "mean_tier": mean_tier,
            "cvar_tier": cvar_tier,
            "test_mean_tier": test_mean_tier,
            "test_cvar_tier": test_cvar_tier,
        },
        "test_policy": {
            "mean": mean_metrics,
            "cvar": cvar_metrics,
            "cvar_gain": cvar_metrics["cvar"] - mean_metrics["cvar"],
            "mean_premium": mean_metrics["mean"] - cvar_metrics["mean"],
            "cvar_gain_ci": gain,
        },
        "gates": gates,
    }


def write_reliability_contract_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "reliability_contract_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    selected = report["selected"]
    test = report["test_policy"]
    lines = [
        "# Reliability contract",
        "",
        f"Task: `{report['task']['id']}` / `{report['task']['version']}`",
        "",
        f"- mean-optimal target: {selected['mean_tier']}",
        f"- CVaR-optimal target: {selected['cvar_tier']}",
        f"- test mean (mean policy): {test['mean']['mean']:.2f}",
        f"- test mean (CVaR policy): {test['cvar']['mean']:.2f}",
        f"- test CVaR (mean policy): {test['mean']['cvar']:.2f}",
        f"- test CVaR (CVaR policy): {test['cvar']['cvar']:.2f}",
        f"- test CVaR gain: {test['cvar_gain']:.2f} "
        f"[{test['cvar_gain_ci'][0]:.2f}, {test['cvar_gain_ci'][1]:.2f}]",
        f"- mean premium: {test['mean_premium']:.2f}",
        "",
        "## Gates",
        "",
        "| Gate | Result |",
        "|---|---|",
    ]
    for name, passed in report["gates"].items():
        lines.append(f"| {name} | {'pass' if passed else 'fail'} |")
    lines.append("")
    (out / "reliability_contract_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "reliability_contract_report.md"
