"""Deterministic episode splits and scenario plans."""

from __future__ import annotations

from dataclasses import dataclass, field

from fabline.worlds.factory.generator import SCENARIOS


def assign_split(seed: int) -> str:
    """Assign a split by seed bucket: 70% train, 20% val, 10% test."""

    bucket = seed % 10
    if bucket < 7:
        return "train"
    if bucket < 9:
        return "val"
    return "test"


@dataclass(frozen=True)
class SplitPlan:
    """Scenario-based split plan for shared episodes.

    The default plan holds out the ``extra_gear`` combination for test. Train
    sees ingot, gear, and extra-ingot; test sees the combination of assembler and
    extra belt. A separate shift split uses a harsher layout.
    """

    name: str
    scenarios: dict[str, tuple[str, ...]]
    episodes_per_scenario: dict[str, int]
    seed_start: int = 0
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for split, names in self.scenarios.items():
            if split not in self.episodes_per_scenario:
                raise ValueError(f"missing episode count for split {split}")
            if self.episodes_per_scenario[split] <= 0:
                raise ValueError(f"episode count for {split} must be positive")
            for name in names:
                if name not in SCENARIOS:
                    raise ValueError(f"unknown scenario {name}")
        if not self.scenarios:
            raise ValueError("split plan needs at least one split")


def default_split_plan() -> SplitPlan:
    return SplitPlan(
        name="compositional-v0.1",
        scenarios={
            "train": ("ingot", "gear", "extra_ingot"),
            "val": ("ingot", "gear"),
            "test": ("extra_gear",),
            "shift": ("shift_gear",),
        },
        episodes_per_scenario={
            "train": 10,
            "val": 2,
            "test": 6,
            "shift": 6,
        },
        metadata={
            "held_out": "extra_gear is the test combination (assembler + extra belt)",
            "shift": "shift_gear uses one ore patch and higher rock density",
        },
    )
