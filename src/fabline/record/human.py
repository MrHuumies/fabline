"""Human and scripted control demonstrations."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from fabline import __version__
from fabline.env.control import ControlConfig, ControlEnv
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.config import FactoryConfig


@dataclass
class HumanDemo:
    demo_id: str
    seed: int
    observations: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    state_hashes: list[str]
    final_score: int
    success: bool
    source: str
    meta: dict[str, Any]


@dataclass
class HumanDemoDataset:
    X: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    demo_ids: np.ndarray
    sources: np.ndarray
    final_scores: np.ndarray
    successes: np.ndarray
    manifest: dict[str, Any]


def validate_control_replay(env: ControlEnv, replay: dict[str, Any]) -> None:
    """Re-run a control demo and compare state hashes after every action."""

    env.reset(int(replay["seed"]))
    hashes = list(replay["state_hashes"])
    actions = [int(action) for action in replay["actions"]]
    if len(hashes) != len(actions):
        raise ValueError("actions and state_hashes must have the same length")
    for index, action in enumerate(actions):
        env.step(action)
        actual = env.world.state_hash()
        if actual != hashes[index]:
            raise RuntimeError(
                f"control replay mismatch at step {index}: "
                f"expected {hashes[index]}, got {actual}"
            )


def write_human_demos(
    root: str | Path,
    name: str,
    demos: list[HumanDemo],
    config: FactoryConfig,
    control: ControlConfig,
) -> dict[str, Any]:
    if not demos:
        raise ValueError("cannot write an empty demo dataset")

    root = Path(root)
    demos_dir = root / "demos"
    demos_dir.mkdir(parents=True, exist_ok=True)

    for demo in demos:
        demo_dir = demos_dir / demo.demo_id
        demo_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            demo_dir / "data.npz",
            observations=demo.observations,
            actions=demo.actions,
            rewards=demo.rewards,
        )
        meta = {
            **demo.meta,
            "demo_id": demo.demo_id,
            "seed": demo.seed,
            "source": demo.source,
            "final_score": demo.final_score,
            "success": demo.success,
            "actions": [int(action) for action in demo.actions.tolist()],
            "control": {
                "episode_ticks": control.episode_ticks,
                "decision_interval": control.decision_interval,
                "build_penalty": control.build_penalty,
                "success_score": control.success_score,
            },
            "fabline_version": __version__,
            "world_version": WORLD_VERSION,
        }
        (demo_dir / "meta.json").write_text(
            json.dumps(meta, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        replay = {
            "seed": demo.seed,
            "actions": [int(action) for action in demo.actions.tolist()],
            "state_hashes": demo.state_hashes,
            "control": meta["control"],
            "world_version": WORLD_VERSION,
        }
        (demo_dir / "replay.json").write_text(
            json.dumps(replay, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    entries: list[dict[str, Any]] = []
    for meta_path in sorted(demos_dir.glob("*/meta.json")):
        entries.append(json.loads(meta_path.read_text(encoding="utf-8")))
    actions = [int(action) for entry in entries for action in entry.get("actions", [])]
    scores = np.asarray([float(entry["final_score"]) for entry in entries], dtype=np.float64)
    successes = np.asarray([bool(entry["success"]) for entry in entries], dtype=np.float64)
    sources = Counter(str(entry["source"]) for entry in entries)
    action_counts = Counter(actions)
    manifest = {
        "name": name,
        "version": "0.1.0",
        "created_at": datetime.now(UTC).isoformat(),
        "fabline_version": __version__,
        "world_version": WORLD_VERSION,
        "config": {
            "factory": config.as_dict(),
            "control": {
                "episode_ticks": control.episode_ticks,
                "decision_interval": control.decision_interval,
                "build_penalty": control.build_penalty,
                "success_score": control.success_score,
            },
        },
        "demos": len(entries),
        "transitions": len(actions),
        "sources": dict(sorted(sources.items())),
        "success_rate": float(np.mean(successes)),
        "mean_final_score": float(np.mean(scores)),
        "std_final_score": float(np.std(scores)),
        "action_counts": dict(sorted(action_counts.items())),
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    card = [
        f"# Dataset card — {name}",
        "",
        "- **Status:** M4 demonstration dataset",
        f"- **Source:** {dict(sources)}",
        f"- **Demos:** {manifest['demos']}",
        f"- **Transitions:** {manifest['transitions']}",
        f"- **Success rate:** {manifest['success_rate']:.2f}",
        f"- **Mean final score:** {manifest['mean_final_score']:.2f}",
        "",
        "## Action counts",
        "",
        "| action | count |",
        "|---|---:|",
        *[f"| {action} | {count} |" for action, count in sorted(action_counts.items())],
        "",
        "## Caveats",
        "",
        "- Scripted demos are a pipeline check; human demos come from `fabline play`.",
        "- The control task is a fixed six-tile construction puzzle.",
        "- Small demo sets overfit easily; report evaluation seeds and budgets.",
        "",
    ]
    (root / "dataset_card.md").write_text("\n".join(card), encoding="utf-8")
    return manifest


def load_human_demos(root: str | Path) -> HumanDemoDataset:
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    demo_dirs = sorted((root / "demos").iterdir())
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    rewards: list[np.ndarray] = []
    demo_ids: list[str] = []
    sources: list[str] = []
    final_scores: list[float] = []
    successes: list[bool] = []
    for demo_dir in demo_dirs:
        if not demo_dir.is_dir():
            continue
        meta = json.loads((demo_dir / "meta.json").read_text(encoding="utf-8"))
        with np.load(demo_dir / "data.npz") as data:
            observations.append(data["observations"])
            actions.append(data["actions"])
            rewards.append(data["rewards"])
        demo_ids.append(meta["demo_id"])
        sources.append(meta["source"])
        final_scores.append(float(meta["final_score"]))
        successes.append(bool(meta["success"]))
    if not observations:
        raise ValueError(f"no demos under {root}")
    return HumanDemoDataset(
        X=np.concatenate(observations),
        actions=np.concatenate(actions),
        rewards=np.concatenate(rewards),
        demo_ids=np.asarray(demo_ids),
        sources=np.asarray(sources),
        final_scores=np.asarray(final_scores),
        successes=np.asarray(successes),
        manifest=manifest,
    )
