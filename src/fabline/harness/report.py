"""Benchmark report writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_benchmark_report(
    out_dir: str | Path,
    dataset_name: str,
    results: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    payload = {
        "dataset": dataset_name,
        "manifest": manifest,
        "results": results,
    }
    (out / "results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        f"# Benchmark report — {dataset_name}",
        "",
        "This is an M1 debug benchmark, not a frozen research benchmark.",
        "",
        "## Versions",
        "",
        f"- world: `{manifest.get('world_version', 'unknown')}`",
        f"- task: `{manifest.get('task_id', 'unknown')}`",
        f"- observation: `{manifest.get('observation', {}).get('name', 'unknown')}`",
        f"- config hash: `{manifest.get('config_hash', 'unknown')}`",
        f"- episodes: {manifest.get('episodes', 'unknown')}",
        "",
    ]

    for split in ("val", "test"):
        lines.extend(
            [
                f"## {split}",
                "",
                "| baseline | MAE | RMSE | R² |",
                "|---|---:|---:|---:|",
            ]
        )
        for name, result in results.items():
            if "skipped" in result:
                lines.append(f"| {name} | — | — | — |")
                continue
            metrics = result[split]
            lines.append(
                f"| {name} | {metrics['mae']:.4f} | {metrics['rmse']:.4f} | "
                f"{metrics['r2']:.4f} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Caveats",
            "",
            "- This report uses a debug dataset and a single task.",
            "- Baselines are not tuned; they exist to prove the pipeline.",
            "- Do not compare these numbers to a frozen benchmark release.",
            "",
        ]
    )
    report_path = out / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
