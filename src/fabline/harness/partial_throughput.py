"""Public partial-observability throughput benchmark.

The task masks a fixed fraction of the current feature frame and asks for the
future depot score. A single masked frame is compared with a short window of
recent masked frames; the window tests whether history recovers hidden state.
This is an original public reimplementation of `factory.throughput.partial.v1`.
"""

from __future__ import annotations

import importlib
import json
import random
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from fabline.harness.baselines import evaluate_baselines
from fabline.harness.metrics import regression_metrics
from fabline.obs.line import LINE_STATE_FEATURES, LineStateObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.labels import future_score
from fabline.worlds.factory.state import EntityType, TileType, entity_counts, tile_counts
from fabline.worlds.factory.world import FactoryWorld

PARTIAL_THROUGHPUT_TASK_ID = "factory.throughput.partial.v1"
PARTIAL_THROUGHPUT_TASK_VERSION = "0.1.0"

CONTEXT_FEATURES = (
    "miner_count_norm",
    "belt_count_norm",
    "furnace_count_norm",
    "assembler_count_norm",
    "ore_tile_fraction",
    "depot_x_norm",
    "depot_y_norm",
)

PARTIAL_FEATURES = (*CONTEXT_FEATURES, *LINE_STATE_FEATURES)


@dataclass(frozen=True)
class PartialThroughputConfig:
    episodes: int = 100
    warmup_ticks: int = 150
    episode_ticks: int = 300
    sample_interval: int = 10
    horizon: int = 50
    dropout: float = 0.6
    window: int = 4
    seed_start: int = 0
    train_fraction: float = 0.7
    val_fraction: float = 0.2
    sequence_epochs: int = 30
    sequence_hidden: int = 16
    sequence_layers: int = 1
    sequence_batch_size: int = 16
    seed: int = 0

    def __post_init__(self) -> None:
        if self.episodes <= 0:
            raise ValueError("episodes must be positive")
        if self.warmup_ticks < 0:
            raise ValueError("warmup_ticks must be non-negative")
        if self.sample_interval <= 0:
            raise ValueError("sample_interval must be positive")
        if self.horizon <= 0:
            raise ValueError("horizon must be positive")
        if self.episode_ticks <= self.warmup_ticks + self.horizon:
            raise ValueError("episode_ticks must exceed warmup + horizon")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")
        if self.window <= 0:
            raise ValueError("window must be positive")
        if self.seed_start < 0:
            raise ValueError("seed_start must be non-negative")
        if not 0.0 < self.train_fraction < 1.0:
            raise ValueError("train_fraction must be in (0, 1)")
        if not 0.0 <= self.val_fraction < 1.0:
            raise ValueError("val_fraction must be in [0, 1)")
        if self.train_fraction + self.val_fraction >= 1.0:
            raise ValueError("train and val fractions must leave a test split")
        if self.sequence_epochs <= 0 or self.sequence_batch_size <= 0:
            raise ValueError("sequence budgets must be positive")
        if self.sequence_hidden <= 0 or self.sequence_layers <= 0:
            raise ValueError("sequence dimensions must be positive")


@dataclass
class PartialThroughputDataset:
    current: np.ndarray
    single: np.ndarray
    window: np.ndarray
    labels: np.ndarray
    splits: np.ndarray
    episode_ids: np.ndarray

    @property
    def samples(self) -> int:
        return int(len(self.labels))


def _factory_config(cfg: PartialThroughputConfig) -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=cfg.episode_ticks,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
    )


def _context_features(state: Any, config: FactoryConfig) -> np.ndarray:
    counts = entity_counts(state)
    tiles = tile_counts(state)
    depot = next(
        (
            entity
            for entity in state.entities.values()
            if entity.type is EntityType.DEPOT
        ),
        None,
    )
    scale = max(1, config.entity_budget)
    return np.asarray(
        (
            counts[EntityType.MINER] / scale,
            counts[EntityType.BELT] / scale,
            counts[EntityType.FURNACE] / scale,
            counts[EntityType.ASSEMBLER] / scale,
            tiles[TileType.ORE] / max(1, state.width * state.height),
            (depot.x / max(1, state.width - 1)) if depot is not None else 0.0,
            (depot.y / max(1, state.height - 1)) if depot is not None else 0.0,
        ),
        dtype=np.float32,
    )


def _mask_frame(
    frame: np.ndarray,
    *,
    seed: int,
    dropout: float,
) -> np.ndarray:
    rng = random.Random(seed)
    mask = np.asarray(
        [rng.random() < dropout for _ in range(frame.size)],
        dtype=np.float32,
    )
    values = np.where(mask > 0.0, 0.0, frame).astype(np.float32)
    return np.concatenate([values, mask])


def _split_for_episode(
    position: int,
    total: int,
    cfg: PartialThroughputConfig,
) -> str:
    train_end = max(1, int(total * cfg.train_fraction))
    val_end = max(train_end + 1, int(total * (cfg.train_fraction + cfg.val_fraction)))
    if position < train_end:
        return "train"
    if position < val_end:
        return "val"
    return "test"


def generate_partial_dataset(
    cfg: PartialThroughputConfig | None = None,
) -> PartialThroughputDataset:
    """Generate the masked-frame dataset."""

    config = cfg or PartialThroughputConfig()
    factory = FactoryWorld(_factory_config(config))
    line_view = LineStateObservation(factory.config)
    current_rows: list[np.ndarray] = []
    single_rows: list[np.ndarray] = []
    window_rows: list[np.ndarray] = []
    labels: list[float] = []
    splits: list[str] = []
    episode_ids: list[int] = []
    for episode in range(config.episodes):
        seed = config.seed_start + episode
        factory.reset(seed, SCENARIOS["gear"])
        factory.run_ticks(config.warmup_ticks)
        split = _split_for_episode(episode, config.episodes, config)
        history: deque[np.ndarray] = deque(maxlen=config.window)
        sample_index = 0
        while (
            factory.state.tick + config.horizon
            <= config.episode_ticks
        ):
            frame = np.concatenate(
                [
                    _context_features(factory.state, factory.config),
                    line_view.observe(factory.state),
                ]
            )
            masked = _mask_frame(
                frame,
                seed=seed * 100_003 + sample_index,
                dropout=config.dropout,
            )
            history.append(masked)
            padded = list(history)
            while len(padded) < config.window:
                padded.insert(0, np.zeros_like(masked))
            current_rows.append(frame)
            single_rows.append(masked)
            window_rows.append(np.concatenate(padded))
            labels.append(float(future_score(factory, config.horizon)))
            splits.append(split)
            episode_ids.append(seed)
            sample_index += 1
            factory.run_ticks(config.sample_interval)
    if not current_rows:
        raise RuntimeError("no partial-observability samples were generated")
    return PartialThroughputDataset(
        current=np.stack(current_rows),
        single=np.stack(single_rows),
        window=np.stack(window_rows),
        labels=np.asarray(labels, dtype=np.float32),
        splits=np.asarray(splits, dtype=object),
        episode_ids=np.asarray(episode_ids, dtype=np.int64),
    )


def _sequence_metrics(
    dataset: PartialThroughputDataset,
    cfg: PartialThroughputConfig,
) -> dict[str, Any]:
    try:
        module = importlib.import_module("fabline.harness.models")
    except ImportError:
        return {"skipped": "optional public-model package is unavailable"}
    gru_class = getattr(module, "GRURegressor", None)
    transformer_class = getattr(module, "TransformerRegressor", None)
    train_config_class = getattr(module, "TorchTrainConfig", None)
    torch_available = getattr(module, "torch_available", None)
    if (
        gru_class is None
        or transformer_class is None
        or train_config_class is None
        or torch_available is None
        or not torch_available()
    ):
        return {"skipped": "optional public-model package is unavailable"}
    train = dataset.splits == "train"
    val = dataset.splits == "val"
    test = dataset.splits == "test"
    sequences = dataset.window.reshape(
        len(dataset.window), cfg.window, len(PARTIAL_FEATURES) * 2
    )
    config = train_config_class(
        epochs=cfg.sequence_epochs,
        batch_size=cfg.sequence_batch_size,
        hidden=cfg.sequence_hidden,
        seed=cfg.seed,
    )
    results: dict[str, Any] = {}
    for name, model_class in (
        ("gru", gru_class),
        (
            "transformer",
            lambda config: transformer_class(
                config,
                layers=cfg.sequence_layers,
                heads=max(1, min(4, cfg.sequence_hidden)),
            ),
        ),
    ):
        try:
            model = (
                model_class(config)
                if name == "gru"
                else model_class(config)
            )
            model.fit(sequences[train], dataset.labels[train])
            result = {
                "val": regression_metrics(
                    dataset.labels[val], model.predict(sequences[val])
                ),
                "test": regression_metrics(
                    dataset.labels[test], model.predict(sequences[test])
                ),
            }
            if model.report is not None:
                result["cost"] = model.report.as_dict()
            results[name] = result
        except (ValueError, RuntimeError):
            results[name] = {"skipped": "model is unavailable for this shape"}
    return results


def run_partial_throughput(
    cfg: PartialThroughputConfig | None = None,
    *,
    include_sequence: bool = True,
) -> dict[str, Any]:
    """Run the partial-throughput benchmark and return a compact report."""

    config = cfg or PartialThroughputConfig()
    dataset = generate_partial_dataset(config)
    train = dataset.splits == "train"
    val = dataset.splits == "val"
    test = dataset.splits == "test"
    views: dict[str, Any] = {}
    for name, values, feature_names in (
        ("current", dataset.current, PARTIAL_FEATURES),
        ("single", dataset.single, None),
        ("window", dataset.window, None),
    ):
        views[name] = evaluate_baselines(
            values[train],
            dataset.labels[train],
            values[val],
            dataset.labels[val],
            values[test],
            dataset.labels[test],
            feature_names,
            include_models=True,
            with_ci=True,
        )
    if include_sequence:
        views["window_sequence"] = _sequence_metrics(dataset, config)
    current_best = max(
        row["test"]["r2"]
        for name, row in views["current"].items()
        if "test" in row
    )
    single_best = max(
        row["test"]["r2"]
        for name, row in views["single"].items()
        if "test" in row
    )
    window_best = max(
        row["test"]["r2"]
        for name, row in views["window"].items()
        if "test" in row
    )
    gates = {
        "H1_mask_loss": bool(single_best < current_best),
        "H2_window_recovery": bool(window_best >= single_best + 0.10),
        "H3_no_leakage": bool(window_best <= current_best + 0.05),
        "H4_budget": "report",
    }
    return {
        "task": {
            "id": PARTIAL_THROUGHPUT_TASK_ID,
            "version": PARTIAL_THROUGHPUT_TASK_VERSION,
            "kind": "regression",
        },
        "config": asdict(config),
        "dataset": {
            "episodes": int(len(set(dataset.episode_ids.tolist()))),
            "samples": dataset.samples,
            "splits": {
                split: int((dataset.splits == split).sum())
                for split in ("train", "val", "test")
            },
            "label_mean": float(dataset.labels.mean()),
            "label_std": float(dataset.labels.std()),
        },
        "views": views,
        "gates": gates,
    }


def write_partial_throughput_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "partial_throughput_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Partial throughput",
        "",
        f"Task: `{report['task']['id']}` / `{report['task']['version']}`",
        "",
        f"- episodes: {report['dataset']['episodes']}",
        f"- samples: {report['dataset']['samples']}",
        f"- splits: {report['dataset']['splits']}",
        "",
        "| view | model | test R² | test MAE |",
        "|---|---|---:|---:|",
    ]
    for view, rows in report["views"].items():
        for model, row in rows.items():
            if "test" not in row:
                lines.append(f"| {view} | {model} | — | — |")
                continue
            lines.append(
                f"| {view} | {model} | {row['test']['r2']:.4f} | "
                f"{row['test']['mae']:.4f} |"
            )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            "| Gate | Result |",
            "|---|---|",
        ]
    )
    for name, value in report["gates"].items():
        lines.append(f"| {name} | {value} |")
    lines.append("")
    (out / "partial_throughput_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "partial_throughput_report.md"
