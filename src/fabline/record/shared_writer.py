"""Write shared episodes: one recording, many views and targets."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from fabline import __version__
from fabline.tasks.shared import SharedEpisode


def _json_dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stats(episodes: list[SharedEpisode]) -> dict[str, Any]:
    future = np.concatenate([episode.targets["future_score"] for episode in episodes])
    bottleneck = np.concatenate([episode.targets["bottleneck"] for episode in episodes])
    splits = Counter(episode.split for episode in episodes)
    scenarios = Counter(episode.scenario for episode in episodes)
    samples_by_split: Counter[str] = Counter()
    for episode in episodes:
        samples_by_split[episode.split] += len(episode.targets["future_score"])
    return {
        "episodes": len(episodes),
        "samples": int(future.size),
        "splits": dict(sorted(splits.items())),
        "samples_by_split": dict(sorted(samples_by_split.items())),
        "scenarios": dict(sorted(scenarios.items())),
        "future_score": {
            "mean": float(np.mean(future)),
            "std": float(np.std(future)),
            "min": float(np.min(future)),
            "max": float(np.max(future)),
        },
        "bottleneck": dict(sorted(Counter(bottleneck.tolist()).items())),
        "views": {
            key: list(value.shape[1:]) for key, value in episodes[0].views.items()
        },
        "targets": {
            key: list(value.shape[1:]) for key, value in episodes[0].targets.items()
        },
    }


def _dataset_card(name: str, manifest: dict[str, Any]) -> str:
    stats = manifest["stats"]
    lines = [
        f"# Dataset card — {name}",
        "",
        "- **Status:** shared-episode debug dataset / M3 benchmark candidate",
        f"- **World version:** `{manifest['world_version']}`",
        f"- **FABLINE version:** `{manifest['fabline_version']}`",
        f"- **Config hash:** `{manifest['config_hash']}`",
        f"- **Split plan:** `{manifest.get('plan_name', 'unknown')}`",
        f"- **Episodes:** {stats['episodes']}",
        f"- **Samples:** {stats['samples']}",
        "",
        "## Splits",
        "",
        "| split | episodes | samples |",
        "|---|---:|---:|",
    ]
    for split, count in stats["splits"].items():
        lines.append(f"| {split} | {count} | {stats['samples_by_split'][split]} |")
    lines.extend(
        [
            "",
            "## Scenarios",
            "",
            "| scenario | episodes |",
            "|---|---:|",
        ]
    )
    for scenario, count in stats["scenarios"].items():
        lines.append(f"| {scenario} | {count} |")
    lines.extend(
        [
            "",
            "## Views",
            "",
            "| view | shape per sample |",
            "|---|---|",
        ]
    )
    for view, shape in stats["views"].items():
        lines.append(f"| {view} | `{shape}` |")
    lines.extend(
        [
            "",
            "## Targets",
            "",
            "| target | shape per sample |",
            "|---|---|",
        ]
    )
    for target, shape in stats["targets"].items():
        lines.append(f"| {target} | `{shape}` |")
    lines.extend(
        [
            "",
            "### Future score",
            "",
            f"- mean: {stats['future_score']['mean']:.4f}",
            f"- std: {stats['future_score']['std']:.4f}",
            f"- min: {stats['future_score']['min']:.4f}",
            f"- max: {stats['future_score']['max']:.4f}",
            "",
            "### Bottleneck classes",
            "",
            "| class | count |",
            "|---|---:|",
        ]
    )
    for label, count in stats["bottleneck"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(
        [
            "",
            "## Caveats",
            "",
            "- This is a debug benchmark candidate, not a frozen release yet.",
            "- Scenario splits are a compositional/shift proxy, not a formal",
            "  causal composition test.",
            "- Bottleneck labels are counterfactual removals at a fixed horizon.",
            "- The test and shift splits are small; inspect confidence intervals.",
            "",
        ]
    )
    return "\n".join(lines)


def write_shared_dataset(
    root: str | Path,
    name: str,
    episodes: list[SharedEpisode],
    manifest_meta: dict[str, Any],
) -> dict[str, Any]:
    if not episodes:
        raise ValueError("cannot write an empty shared dataset")

    root = Path(root)
    episodes_dir = root / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)

    for episode in episodes:
        episode_dir = episodes_dir / episode.episode_id
        episode_dir.mkdir(parents=True, exist_ok=True)
        payload = {**episode.views, **episode.targets}
        payload["ticks"] = np.asarray(episode.sample_ticks, dtype=np.int64)
        np.savez_compressed(
            episode_dir / "data.npz",
            **payload,  # type: ignore[arg-type]
        )
        meta = {
            **episode.meta,
            "episode_id": episode.episode_id,
            "seed": episode.seed,
            "scenario": episode.scenario,
            "split": episode.split,
        }
        _json_dump(episode_dir / "meta.json", meta)
        _json_dump(
            episode_dir / "replay.json",
            {
                "seed": episode.seed,
                "scenario": episode.scenario,
                "sample_ticks": episode.sample_ticks,
                "state_hashes": episode.state_hashes,
                "actions": [],
                "world_version": manifest_meta["world_version"],
                "config_hash": manifest_meta["config_hash"],
            },
        )

    stats = _stats(episodes)
    manifest = {
        "name": name,
        "version": "0.1.0",
        "created_at": datetime.now(UTC).isoformat(),
        "world_version": manifest_meta["world_version"],
        "fabline_version": __version__,
        "config_hash": manifest_meta["config_hash"],
        "factory_config": manifest_meta.get("factory_config", {}),
        "plan_name": manifest_meta.get("plan_name", "unknown"),
        "plan_metadata": manifest_meta.get("plan_metadata", {}),
        "episode_config": manifest_meta.get("episode_config", {}),
        "episodes": len(episodes),
        "stats": stats,
    }
    _json_dump(root / "manifest.json", manifest)
    _json_dump(root / "stats.json", stats)
    (root / "dataset_card.md").write_text(
        _dataset_card(name, manifest),
        encoding="utf-8",
    )
    return manifest
