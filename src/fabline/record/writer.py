"""Write a debug dataset to disk."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from fabline.tasks.base import EpisodeData


def _json_dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stats(episodes: list[EpisodeData]) -> dict[str, Any]:
    labels = np.concatenate([episode.labels for episode in episodes])
    observations = episodes[0].observations
    return {
        "episodes": len(episodes),
        "samples": int(labels.size),
        "labels": {
            "mean": float(np.mean(labels)),
            "std": float(np.std(labels)),
            "min": float(np.min(labels)),
            "max": float(np.max(labels)),
        },
        "observation_shape": list(observations.shape[1:]),
    }


def _dataset_card(
    name: str,
    manifest: dict[str, Any],
    split_counts: Counter[str],
) -> str:
    observation = manifest["observation"]
    stats = manifest["stats"]
    label_stats = stats["labels"]
    lines = [
        f"# Dataset card — {name}",
        "",
        "- **Status:** debug / M1 vertical slice",
        f"- **World version:** `{manifest['world_version']}`",
        f"- **Task:** `{manifest['task_id']}`",
        f"- **Observation:** `{observation['name']}` "
        f"(`{observation['version']}`), shape `{observation['shape']}`",
        f"- **Target:** `{manifest.get('target_name', 'unknown')}`",
        f"- **Episodes:** {manifest['episodes']}",
        f"- **Samples:** {stats['samples']}",
        "",
        "## Splits",
        "",
        "| split | episodes |",
        "|---|---:|",
        *[f"| {split} | {count} |" for split, count in sorted(split_counts.items())],
        "",
        "## Targets",
        "",
        f"Target: `{manifest.get('target_name', 'unknown')}`.",
        "",
        "| statistic | value |",
        "|---|---:|",
        f"| mean | {label_stats['mean']:.4f} |",
        f"| std | {label_stats['std']:.4f} |",
        f"| min | {label_stats['min']:.4f} |",
        f"| max | {label_stats['max']:.4f} |",
        "",
        "## Caveats",
        "",
        "- This is a debug dataset, not a frozen benchmark release.",
        "- It contains one task, one world configuration, and a small seed range.",
        "- Splits are assigned by seed bucket; they are disjoint by episode but not",
        "  yet audited for layout near-duplicates.",
        "- Do not compare results across dataset versions without checking the",
        "  manifest and config hash.",
        "",
    ]
    return "\n".join(lines)


def write_dataset(
    root: str | Path,
    name: str,
    episodes: list[EpisodeData],
    manifest_meta: dict[str, Any],
) -> dict[str, Any]:
    """Write episodes, replays, a manifest, stats, and a dataset card."""

    if not episodes:
        raise ValueError("cannot write an empty dataset")

    root = Path(root)
    episodes_dir = root / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)

    split_counts: Counter[str] = Counter()
    for episode in episodes:
        episode_dir = episodes_dir / episode.episode_id
        episode_dir.mkdir(parents=True, exist_ok=True)

        np.savez_compressed(
            episode_dir / "steps.npz",
            observations=episode.observations,
            labels=episode.labels,
            ticks=np.asarray(episode.sample_ticks, dtype=np.int64),
        )
        meta = {
            **episode.meta,
            "episode_id": episode.episode_id,
            "seed": episode.seed,
            "split": episode.split,
        }
        _json_dump(episode_dir / "meta.json", meta)
        replay = {
            "seed": episode.seed,
            "sample_ticks": episode.sample_ticks,
            "state_hashes": episode.state_hashes,
            "actions": [],
            "world_version": manifest_meta["world_version"],
            "config_hash": manifest_meta["config_hash"],
        }
        if "faults" in manifest_meta:
            replay["faults"] = manifest_meta["faults"]
        if "power" in manifest_meta:
            replay["power"] = manifest_meta["power"]
        if "scenario" in manifest_meta:
            replay["scenario"] = manifest_meta["scenario"]
        _json_dump(episode_dir / "replay.json", replay)

        if episode.events:
            with (episode_dir / "events.jsonl").open("w", encoding="utf-8") as handle:
                for event in episode.events:
                    handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")

        split_counts[episode.split] += 1

    stats = _stats(episodes)
    manifest = {
        "name": name,
        "version": "0.1.0",
        "created_at": datetime.now(UTC).isoformat(),
        "world_version": manifest_meta["world_version"],
        "config_hash": manifest_meta["config_hash"],
        "task_id": manifest_meta["task_id"],
        "task_version": manifest_meta["task_version"],
        "target_name": manifest_meta.get("target_name", "unknown"),
        "observation": manifest_meta["observation"],
        "episodes": len(episodes),
        "splits": dict(sorted(split_counts.items())),
        "seed_start": min(episode.seed for episode in episodes),
        "seed_end": max(episode.seed for episode in episodes),
        "stats": stats,
    }
    if "faults" in manifest_meta:
        manifest["faults"] = manifest_meta["faults"]
    if "power" in manifest_meta:
        manifest["power"] = manifest_meta["power"]
    if "scenario" in manifest_meta:
        manifest["scenario"] = manifest_meta["scenario"]
    _json_dump(root / "manifest.json", manifest)
    _json_dump(root / "stats.json", stats)
    (root / "dataset_card.md").write_text(
        _dataset_card(name, manifest, split_counts),
        encoding="utf-8",
    )
    return manifest
