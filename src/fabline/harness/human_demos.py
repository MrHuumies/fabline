"""Scripted demos and behavior cloning from demonstration datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.control import ControlConfig, ControlEnv
from fabline.harness.control import (
    BehaviorCloningPolicy,
    ScriptedControlPolicy,
    evaluate_policy,
)
from fabline.record.human import HumanDemo, load_human_demos
from fabline.worlds.factory.config import FactoryConfig


def make_scripted_demos(
    config: FactoryConfig,
    control: ControlConfig,
    *,
    episodes: int = 10,
    seed: int = 0,
) -> list[HumanDemo]:
    """Generate a reproducible demonstration dataset with the scripted policy."""

    env = ControlEnv(config, control)
    policy = ScriptedControlPolicy()
    demos: list[HumanDemo] = []
    for episode in range(episodes):
        episode_seed = seed + episode
        observation, info = env.reset(episode_seed)
        observations: list[np.ndarray] = []
        actions: list[int] = []
        rewards: list[float] = []
        hashes: list[str] = []
        done = False
        while not done:
            mask = env.action_mask()
            action = policy.act(observation, info, mask)
            observations.append(observation)
            actions.append(action)
            observation, reward, terminated, truncated, info = env.step(action)
            rewards.append(reward)
            hashes.append(env.world.state_hash())
            done = terminated or truncated
        demos.append(
            HumanDemo(
                demo_id=f"scripted_{episode_seed:04d}",
                seed=episode_seed,
                observations=np.stack(observations),
                actions=np.asarray(actions, dtype=np.int64),
                rewards=np.asarray(rewards, dtype=np.float32),
                state_hashes=hashes,
                final_score=int(info["score"]),
                success=bool(info["success"]),
                source="scripted",
                meta={"episode_steps": len(actions)},
            )
        )
    return demos


def train_human_bc(
    dataset_path: str | Path,
    config: FactoryConfig,
    control: ControlConfig,
    *,
    episodes: int = 5,
    seed: int = 0,
) -> dict[str, Any]:
    dataset = load_human_demos(dataset_path)
    policy = BehaviorCloningPolicy(seed=seed)
    policy.fit(dataset.X, dataset.actions)
    env = ControlEnv(config, control)
    metrics = evaluate_policy(env, policy, episodes=episodes, seed=seed)
    return {
        "dataset": str(dataset_path),
        "demos": int(len(dataset.demo_ids)),
        "transitions": int(len(dataset.X)),
        "sources": dataset.manifest.get("sources", {}),
        "metrics": {
            "mean_score": metrics.mean_score,
            "std_score": metrics.std_score,
            "success_rate": metrics.success_rate,
            "mean_reward": metrics.mean_reward,
            "mean_steps": metrics.mean_steps,
            "path_complete_rate": metrics.path_complete_rate,
        },
    }


def write_human_bc_report(
    out_dir: str | Path,
    results: dict[str, Any],
) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    metrics = results["metrics"]
    lines = [
        "# Human demonstration behavior-cloning report",
        "",
        f"- dataset: `{results['dataset']}`",
        f"- demos: {results['demos']}",
        f"- transitions: {results['transitions']}",
        f"- sources: {results['sources']}",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| mean score | {metrics['mean_score']:.2f} |",
        f"| std score | {metrics['std_score']:.2f} |",
        f"| success rate | {metrics['success_rate']:.2f} |",
        f"| mean reward | {metrics['mean_reward']:.2f} |",
        f"| path complete | {metrics['path_complete_rate']:.2f} |",
        "",
        "## Caveats",
        "",
        "- A decision-tree clone is a sanity check, not a strong imitation method.",
        "- Scripted demos solve the task; human demos may be noisier and weaker.",
        "- Report the evaluation seeds and demo count with any claim.",
        "",
    ]
    path = out / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
