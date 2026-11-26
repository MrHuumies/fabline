"""Feasibility audit for a generative layout/recipe pilot."""

from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS, generate_state


@dataclass(frozen=True)
class GenerativeAuditConfig:
    seeds: int = 100
    seed_start: int = 0
    scenarios: tuple[str, ...] = (
        "ingot",
        "extra_ingot",
        "gear",
        "extra_gear",
        "shift_gear",
        "random_gear",
        "spread_gear",
        "random_topology",
    )

    def __post_init__(self) -> None:
        if self.seeds <= 0:
            raise ValueError("seeds must be positive")
        if not self.scenarios:
            raise ValueError("scenarios must not be empty")
        for name in self.scenarios:
            if name not in SCENARIOS:
                raise ValueError(f"unknown scenario {name}")


def _factory_config() -> FactoryConfig:
    return FactoryConfig(
        width=48,
        height=24,
        ticks_per_episode=300,
        decision_interval=10,
        entity_budget=48,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
        emit_events=True,
    )


def _lines(state: Any) -> list[tuple[tuple[str, ...], int, int]]:
    groups: dict[int, list[Any]] = {}
    for entity in state.entities.values():
        groups.setdefault(entity.y, []).append(entity)
    lines: list[tuple[tuple[str, ...], int, int]] = []
    for y, group in groups.items():
        ordered = sorted(group, key=lambda item: item.x)
        sequence = tuple(entity.type.name for entity in ordered)
        lines.append((sequence, ordered[0].x, y))
    return lines

def _diversity(sequences: list[tuple[str, ...]]) -> float:
    if len(sequences) < 2:
        return 0.0
    similarities = []
    for index, first in enumerate(sequences):
        for second in sequences[index + 1 :]:
            similarities.append(
                SequenceMatcher(None, first, second).ratio()
            )
    if not similarities:
        return 0.0
    return float(1.0 - sum(similarities) / len(similarities))


def run_generative_audit(
    cfg: GenerativeAuditConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or GenerativeAuditConfig()
    config = _factory_config()
    sequences: list[tuple[str, ...]] = []
    positions: list[tuple[int, int]] = []
    per_scenario: dict[str, dict[str, Any]] = {}
    for scenario_name in cfg.scenarios:
        scenario_sequences: list[tuple[str, ...]] = []
        scenario_positions: list[tuple[int, int]] = []
        for offset in range(cfg.seeds):
            seed = cfg.seed_start + offset
            state = generate_state(
                config, seed, SCENARIOS[scenario_name]
            )
            lines = _lines(state)
            scenario_sequences.extend(sequence for sequence, _, _ in lines)
            scenario_positions.extend(
                (x0, y) for _, x0, y in lines
            )
        unique = set(scenario_sequences)
        per_scenario[scenario_name] = {
            "lines": len(scenario_sequences),
            "unique_sequences": len(unique),
            "diversity": _diversity(scenario_sequences),
            "positions": len(set(scenario_positions)),
        }
        sequences.extend(scenario_sequences)
        positions.extend(scenario_positions)
    unique_sequences = set(sequences)
    diversity = _diversity(sequences)
    position_diversity = (
        len(set(positions)) / len(sequences) if sequences else 0.0
    )
    structural_gate = len(unique_sequences) >= 20 and diversity >= 0.25
    return {
        "task": "factory.generative.audit.v1",
        "config": {
            "seeds": cfg.seeds,
            "seed_start": cfg.seed_start,
            "scenarios": list(cfg.scenarios),
        },
        "lines": len(sequences),
        "unique_sequences": len(unique_sequences),
        "diversity": diversity,
        "unique_positions": len(set(positions)),
        "position_diversity": position_diversity,
        "structural_gate": structural_gate,
        "per_scenario": per_scenario,
        "unique_examples": [
            list(sequence) for sequence in sorted(unique_sequences)[:12]
        ],
    }


def write_generative_audit_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "generative_audit_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Generative layout/recipe feasibility audit",
        "",
        f"Lines {report['lines']}; unique sequences "
        f"{report['unique_sequences']}; diversity "
        f"{report['diversity']:.3f}; unique positions "
        f"{report['unique_positions']}.",
        "",
        f"Structural gate: {'pass' if report['structural_gate'] else 'fail'}.",
        "",
        "| scenario | lines | unique | diversity | positions |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in report["per_scenario"].items():
        lines.append(
            f"| {name} | {row['lines']} | {row['unique_sequences']} | "
            f"{row['diversity']:.3f} | {row['positions']} |"
        )
    lines.extend(
        [
            "",
            "Unique examples:",
            "",
            "```text",
            *("\n".join(example) for example in report["unique_examples"]),
            "```",
        ]
    )
    (out / "generative_audit_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "generative_audit_report.md"
