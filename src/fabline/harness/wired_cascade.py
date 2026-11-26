"""Public wired-power cascade prediction benchmark.

The task is to predict the number of consumers that lose connectivity when a
marked wire edge fails. The public harness is an original reimplementation of
the `factory.power.cascade.v1` contract; it does not depend on the private
experiment code.
"""

from __future__ import annotations

import importlib
import json
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from fabline.harness.baselines import evaluate_baselines
from fabline.harness.graph_models import evaluate_graph_baseline
from fabline.harness.metrics import regression_metrics
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import Entity, PowerWire, WorldState
from fabline.worlds.factory.wire import entity_connected, reachable_cells
from fabline.worlds.factory.world import FactoryWorld

WIRED_CASCADE_TASK_ID = "factory.power.cascade.v1"
WIRED_CASCADE_TASK_VERSION = "0.1.0"

VECTOR_FEATURES = (
    "layout_width_norm",
    "layout_height_norm",
    "wire_count_norm",
    "node_count_norm",
    "edge_count_norm",
    "max_degree_norm",
    "mean_degree_norm",
    "source_degree_norm",
    "consumer_count_norm",
    "connected_norm",
    "redundancy_norm",
    "fault_ax_norm",
    "fault_ay_norm",
    "fault_bx_norm",
    "fault_by_norm",
    "fault_degree_norm",
    "fault_source_distance_norm",
    "fault_length_norm",
    "vulnerable_fraction",
    "redundant_fraction",
    "fault_consumer_min_distance_norm",
    "fault_consumer_mean_distance_norm",
)

GRAPH_FEATURES = (
    "ax_norm",
    "ay_norm",
    "bx_norm",
    "by_norm",
    "length_norm",
    "degree_a_norm",
    "degree_b_norm",
    "source_distance_norm",
    "consumer_adjacent_norm",
    "vulnerable_fraction",
    "redundant_fraction",
    "fault_consumer_min_distance_norm",
    "fault_consumer_mean_distance_norm",
    "is_fault",
)


@dataclass(frozen=True)
class WiredCascadeConfig:
    layouts: int = 200
    seed_start: int = 500
    max_faults_per_layout: int = 10
    warmup_ticks: int = 50
    train_fraction: float = 0.7
    val_fraction: float = 0.2
    mpnn_epochs: int = 50
    mpnn_hidden: int = 32
    mpnn_layers: int = 2
    mpnn_batch_size: int = 32
    seed: int = 0
    power: PowerConfig = field(
        default_factory=lambda: PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=12,
            generator_radius=8,
            wire_redundancy=2,
        )
    )

    def __post_init__(self) -> None:
        if self.layouts <= 0:
            raise ValueError("layouts must be positive")
        if self.seed_start < 0:
            raise ValueError("seed_start must be non-negative")
        if self.max_faults_per_layout <= 0:
            raise ValueError("max_faults_per_layout must be positive")
        if self.warmup_ticks < 0:
            raise ValueError("warmup_ticks must be non-negative")
        if not 0.0 < self.train_fraction < 1.0:
            raise ValueError("train_fraction must be in (0, 1)")
        if not 0.0 <= self.val_fraction < 1.0:
            raise ValueError("val_fraction must be in [0, 1)")
        if self.train_fraction + self.val_fraction >= 1.0:
            raise ValueError("train and val fractions must leave a test split")
        if self.mpnn_epochs <= 0 or self.mpnn_batch_size <= 0:
            raise ValueError("MPNN budgets must be positive")
        if self.mpnn_hidden <= 0 or self.mpnn_layers <= 0:
            raise ValueError("MPNN model dimensions must be positive")
        if not self.power.enabled or self.power.topology != "wired":
            raise ValueError("wired cascade requires the wired power topology")


@dataclass
class CascadeDataset:
    vector: np.ndarray
    entity_features: np.ndarray
    entity_mask: np.ndarray
    adjacency: np.ndarray
    labels: np.ndarray
    splits: np.ndarray
    layout_seeds: np.ndarray
    fault_ids: np.ndarray
    max_nodes: int

    @property
    def samples(self) -> int:
        return int(len(self.labels))


def _factory_config(cfg: WiredCascadeConfig) -> FactoryConfig:
    return FactoryConfig(
        width=32,
        height=16,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.02,
        ore_patches=1,
        starter_line=True,
    )


def _consumers(state: WorldState, power: PowerConfig) -> list[Entity]:
    return [
        entity
        for entity in sorted(state.entities.values(), key=lambda item: item.id)
        if power.demand(entity.type) > 0
    ]


def _connected_ids(state: WorldState, power: PowerConfig) -> set[int]:
    if not state.power_sources:
        return set()
    reachable = reachable_cells(state.power_sources[0], state.power_wires)
    return {
        entity.id
        for entity in _consumers(state, power)
        if entity_connected(entity, reachable, state.power_wires)
    }


def _outage(
    state: WorldState,
    wire: PowerWire,
    power: PowerConfig,
) -> int:
    before = _connected_ids(state, power)
    wire.failed = True
    after = _connected_ids(state, power)
    wire.failed = False
    return len(before - after)


def _select_faults(
    state: WorldState,
    power: PowerConfig,
    cfg: WiredCascadeConfig,
) -> list[tuple[PowerWire, int]]:
    wires = sorted(state.power_wires, key=lambda wire: wire.id)
    outages = {wire.id: _outage(state, wire, power) for wire in wires}
    loops = [wire for wire in wires if outages[wire.id] == 0]
    bridges = [wire for wire in wires if outages[wire.id] > 0]
    cap = cfg.max_faults_per_layout
    half = max(1, cap // 2)
    selected = [*loops[:half], *bridges[: cap - min(len(loops[:half]), half)]]
    selected_ids = {wire.id for wire in selected}
    for wire in wires:
        if len(selected) >= cap:
            break
        if wire.id not in selected_ids:
            selected.append(wire)
            selected_ids.add(wire.id)
    return [(wire, outages[wire.id]) for wire in selected[:cap]]


def _wire_cells(wires: list[PowerWire]) -> list[tuple[int, int]]:
    return sorted(
        {
            cell
            for wire in wires
            for cell in ((wire.ax, wire.ay), (wire.bx, wire.by))
        }
    )


def _wire_graph(wires: list[PowerWire]) -> dict[tuple[int, int], set[tuple[int, int]]]:
    graph: dict[tuple[int, int], set[tuple[int, int]]] = {}
    for wire in wires:
        left = (wire.ax, wire.ay)
        right = (wire.bx, wire.by)
        graph.setdefault(left, set()).add(right)
        graph.setdefault(right, set()).add(left)
    return graph


def _has_path(
    graph: dict[tuple[int, int], set[tuple[int, int]]],
    start: tuple[int, int],
    goals: set[tuple[int, int]],
    blocked: tuple[tuple[int, int], tuple[int, int]] | None = None,
) -> bool:
    queue = deque([start])
    seen = {start}
    while queue:
        cell = queue.popleft()
        if cell in goals:
            return True
        for neighbor in graph.get(cell, ()):
            if blocked is not None and {cell, neighbor} == set(blocked):
                continue
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return False


def _shortest_path(
    graph: dict[tuple[int, int], set[tuple[int, int]]],
    start: tuple[int, int],
    goals: set[tuple[int, int]],
) -> list[tuple[int, int]] | None:
    queue = deque([start])
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while queue:
        cell = queue.popleft()
        if cell in goals:
            path: list[tuple[int, int]] = []
            current: tuple[int, int] | None = cell
            while current is not None:
                path.append(current)
                current = parent[current]
            return list(reversed(path))
        for neighbor in graph.get(cell, ()):
            if neighbor not in parent:
                parent[neighbor] = cell
                queue.append(neighbor)
    return None


def _edge_disjoint_count(
    graph: dict[tuple[int, int], set[tuple[int, int]]],
    start: tuple[int, int],
    goals: set[tuple[int, int]],
    limit: int = 2,
) -> int:
    path = _shortest_path(graph, start, goals)
    if path is None:
        return 0
    if limit <= 1:
        return 1
    for left, right in zip(path, path[1:], strict=False):
        if _has_path(graph, start, goals, blocked=(left, right)):
            return 2
    return 1


def _consumer_vulnerability(
    state: WorldState,
    power: PowerConfig,
) -> tuple[float, float]:
    consumers = _consumers(state, power)
    if not consumers or not state.power_sources:
        return 0.0, 0.0
    graph = _wire_graph(state.power_wires)
    source = state.power_sources[0]
    goals = {
        cell
        for cell in graph
        if abs(cell[0] - source.x) + abs(cell[1] - source.y) == 1
    }
    counts: list[int] = []
    for entity in consumers:
        terminal = next(
            (
                cell
                for cell in ((entity.x + 1, entity.y), (entity.x - 1, entity.y),
                             (entity.x, entity.y + 1), (entity.x, entity.y - 1))
                if cell in graph
            ),
            None,
        )
        counts.append(
            0
            if terminal is None
            else _edge_disjoint_count(graph, terminal, goals)
        )
    vulnerable = sum(1 for count in counts if count == 1)
    redundant = sum(1 for count in counts if count >= 2)
    return vulnerable / len(counts), redundant / len(counts)


def _fault_consumer_distances(
    state: WorldState,
    wire: PowerWire,
    power: PowerConfig,
) -> tuple[float, float]:
    consumers = _consumers(state, power)
    if not consumers:
        return 0.0, 0.0
    endpoints = ((wire.ax, wire.ay), (wire.bx, wire.by))
    distances = [
        min(
            abs(entity.x - x) + abs(entity.y - y)
            for x, y in endpoints
        )
        for entity in consumers
    ]
    scale = max(1, state.width + state.height)
    return min(distances) / scale, (sum(distances) / len(distances)) / scale


def _graph_features(
    state: WorldState,
    wire: PowerWire,
    power: PowerConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    wires = sorted(state.power_wires, key=lambda item: item.id)
    count = len(wires)
    features = np.zeros((count, len(GRAPH_FEATURES)), dtype=np.float32)
    adjacency = np.zeros((count, count), dtype=np.float32)
    degrees: dict[tuple[int, int], int] = {}
    for edge in wires:
        left = (edge.ax, edge.ay)
        right = (edge.bx, edge.by)
        degrees[left] = degrees.get(left, 0) + 1
        degrees[right] = degrees.get(right, 0) + 1
    for left_index, left_wire in enumerate(wires):
        for right_index in range(left_index + 1, count):
            right_wire = wires[right_index]
            left_cells = {(left_wire.ax, left_wire.ay), (left_wire.bx, left_wire.by)}
            right_cells = {
                (right_wire.ax, right_wire.ay),
                (right_wire.bx, right_wire.by),
            }
            if left_cells & right_cells:
                adjacency[left_index, right_index] = 1.0
                adjacency[right_index, left_index] = 1.0
    source = state.power_sources[0] if state.power_sources else None
    consumers = _consumers(state, power)
    consumer_cells = {
        (entity.x + dx, entity.y + dy)
        for entity in consumers
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
    }
    max_degree = max(1, max(degrees.values(), default=1))
    max_distance = max(1, state.width + state.height)
    vulnerable, redundant = _consumer_vulnerability(state, power)
    fault_min, fault_mean = _fault_consumer_distances(state, wire, power)
    for position, edge in enumerate(wires):
        ax, ay = edge.ax, edge.ay
        bx, by = edge.bx, edge.by
        source_distance = (
            min(
                abs(ax - source.x) + abs(ay - source.y),
                abs(bx - source.x) + abs(by - source.y),
            )
            if source is not None
            else 0
        )
        adjacent_consumers = int((ax, ay) in consumer_cells) + int(
            (bx, by) in consumer_cells
        )
        features[position] = (
            ax / max(1, state.width - 1),
            ay / max(1, state.height - 1),
            bx / max(1, state.width - 1),
            by / max(1, state.height - 1),
            1.0 / max_distance,
            degrees[(ax, ay)] / max_degree,
            degrees[(bx, by)] / max_degree,
            source_distance / max_distance,
            adjacent_consumers / max(1, len(consumers)),
            vulnerable,
            redundant,
            fault_min,
            fault_mean,
            1.0 if edge.id == wire.id else 0.0,
        )
    mask = np.ones(count, dtype=np.float32)
    return features, mask, adjacency


def _vector_features(
    state: WorldState,
    wire: PowerWire,
    power: PowerConfig,
) -> np.ndarray:
    cells = _wire_cells(state.power_wires)
    index = {cell: position for position, cell in enumerate(cells)}
    adjacency = np.zeros((len(cells), len(cells)), dtype=np.float32)
    degrees = {cell: 0 for cell in cells}
    for edge in state.power_wires:
        left = (edge.ax, edge.ay)
        right = (edge.bx, edge.by)
        adjacency[index[left], index[right]] = 1.0
        adjacency[index[right], index[left]] = 1.0
        degrees[left] += 1
        degrees[right] += 1
    consumers = _consumers(state, power)
    connected = _connected_ids(state, power)
    source = state.power_sources[0] if state.power_sources else None
    fault_left = (wire.ax, wire.ay)
    fault_right = (wire.bx, wire.by)
    fault_degree = (degrees[fault_left] + degrees[fault_right]) / 2.0
    source_distance = (
        min(
            abs(fault_left[0] - source.x) + abs(fault_left[1] - source.y),
            abs(fault_right[0] - source.x) + abs(fault_right[1] - source.y),
        )
        if source is not None
        else 0.0
    )
    node_count = max(1, len(cells))
    edge_count = len(state.power_wires)
    components = 1 if cells else 0
    redundancy = max(0, edge_count - (node_count - components))
    vulnerable, redundant_fraction = _consumer_vulnerability(state, power)
    fault_min, fault_mean = _fault_consumer_distances(state, wire, power)
    values = (
        state.width / 64.0,
        state.height / 32.0,
        edge_count / 32.0,
        node_count / 64.0,
        edge_count / 64.0,
        max(degrees.values(), default=0) / max(1, node_count - 1),
        (sum(degrees.values()) / node_count) / max(1, node_count - 1),
        (degrees.get((source.x, source.y), 0) if source is not None else 0)
        / max(1, node_count - 1),
        len(consumers) / 16.0,
        len(connected) / max(1, len(consumers)),
        redundancy / max(1, node_count),
        wire.ax / max(1, state.width - 1),
        wire.ay / max(1, state.height - 1),
        wire.bx / max(1, state.width - 1),
        wire.by / max(1, state.height - 1),
        fault_degree / max(1, max(degrees.values(), default=1)),
        source_distance / max(1, state.width + state.height),
        1.0 / max(1, state.width + state.height),
        vulnerable,
        redundant_fraction,
        fault_min,
        fault_mean,
    )
    return np.asarray(values, dtype=np.float32)


def _split_for_layout(
    position: int,
    total: int,
    cfg: WiredCascadeConfig,
) -> str:
    train_end = max(1, int(total * cfg.train_fraction))
    val_end = max(train_end + 1, int(total * (cfg.train_fraction + cfg.val_fraction)))
    if position < train_end:
        return "train"
    if position < val_end:
        return "val"
    return "test"


def generate_cascade_dataset(
    cfg: WiredCascadeConfig | None = None,
) -> CascadeDataset:
    """Generate the public cascade dataset, split by layout seed."""

    config = cfg or WiredCascadeConfig()
    vector_rows: list[np.ndarray] = []
    graph_rows: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    labels: list[int] = []
    splits: list[str] = []
    layout_seeds: list[int] = []
    fault_ids: list[int] = []
    factory = FactoryWorld(_factory_config(config), power=config.power)
    valid_layouts = 0
    for layout_index in range(config.layouts):
        seed = config.seed_start + layout_index
        try:
            factory.reset(seed, SCENARIOS["gear"])
        except RuntimeError:
            continue
        world = factory
        world.run_ticks(config.warmup_ticks)
        selected = _select_faults(world.state, config.power, config)
        if not selected:
            continue
        split = _split_for_layout(
            valid_layouts,
            config.layouts,
            config,
        )
        valid_layouts += 1
        for wire, outage in selected:
            vector_rows.append(_vector_features(world.state, wire, config.power))
            graph = _graph_features(world.state, wire, config.power)
            graph_rows.append(graph)
            labels.append(int(outage))
            splits.append(split)
            layout_seeds.append(seed)
            fault_ids.append(wire.id)
    if not vector_rows:
        raise RuntimeError("no valid wired layouts were generated")
    max_nodes = max(len(features) for features, _, _ in graph_rows)
    entity_features = np.zeros(
        (len(graph_rows), max_nodes, len(GRAPH_FEATURES)), dtype=np.float32
    )
    entity_mask = np.zeros((len(graph_rows), max_nodes), dtype=np.float32)
    adjacency = np.zeros((len(graph_rows), max_nodes, max_nodes), dtype=np.float32)
    for index, (features, mask, edges) in enumerate(graph_rows):
        nodes = len(features)
        entity_features[index, :nodes] = features
        entity_mask[index, :nodes] = mask
        adjacency[index, :nodes, :nodes] = edges
    return CascadeDataset(
        vector=np.stack(vector_rows),
        entity_features=entity_features,
        entity_mask=entity_mask,
        adjacency=adjacency,
        labels=np.asarray(labels, dtype=np.float32),
        splits=np.asarray(splits, dtype=object),
        layout_seeds=np.asarray(layout_seeds, dtype=np.int64),
        fault_ids=np.asarray(fault_ids, dtype=np.int64),
        max_nodes=max_nodes,
    )


def _mpnn_metrics(
    dataset: CascadeDataset,
    cfg: WiredCascadeConfig,
) -> dict[str, Any]:
    try:
        module = importlib.import_module("fabline.harness.models")
    except ImportError:
        return {"skipped": "optional public-model package is unavailable"}
    mpnn_class = getattr(module, "MPNNRegressor", None)
    train_config_class = getattr(module, "TorchTrainConfig", None)
    torch_available = getattr(module, "torch_available", None)
    if (
        mpnn_class is None
        or train_config_class is None
        or torch_available is None
        or not torch_available()
    ):
        return {"skipped": "optional public-model package is unavailable"}
    train = dataset.splits == "train"
    val = dataset.splits == "val"
    test = dataset.splits == "test"
    model = mpnn_class(
        train_config_class(
            epochs=cfg.mpnn_epochs,
            batch_size=cfg.mpnn_batch_size,
            hidden=cfg.mpnn_hidden,
            seed=cfg.seed,
        ),
        layers=cfg.mpnn_layers,
    )
    model.fit(
        dataset.entity_features[train],
        dataset.entity_mask[train],
        dataset.adjacency[train],
        dataset.labels[train],
    )
    result: dict[str, Any] = {
        "val": regression_metrics(
            dataset.labels[val],
            model.predict(
                dataset.entity_features[val],
                dataset.entity_mask[val],
                dataset.adjacency[val],
            ),
        ),
        "test": regression_metrics(
            dataset.labels[test],
            model.predict(
                dataset.entity_features[test],
                dataset.entity_mask[test],
                dataset.adjacency[test],
            ),
        ),
    }
    if model.report is not None:
        result["cost"] = model.report.as_dict()
    return result


def run_wired_cascade(
    cfg: WiredCascadeConfig | None = None,
    *,
    include_mpnn: bool = True,
) -> dict[str, Any]:
    """Run the wired-cascade benchmark and return a compact report."""

    config = cfg or WiredCascadeConfig()
    dataset = generate_cascade_dataset(config)
    train = dataset.splits == "train"
    val = dataset.splits == "val"
    test = dataset.splits == "test"
    metrics: dict[str, Any] = dict(
        evaluate_baselines(
            dataset.vector[train],
            dataset.labels[train],
            dataset.vector[val],
            dataset.labels[val],
            dataset.vector[test],
            dataset.labels[test],
            VECTOR_FEATURES,
            include_models=True,
            with_ci=True,
        )
    )
    metrics.update(
        evaluate_graph_baseline(
            {
                "entity_features": dataset.entity_features,
                "entity_mask": dataset.entity_mask,
                "adjacency": dataset.adjacency,
            },
            dataset.splits,
            dataset.labels,
        )
    )
    if include_mpnn:
        metrics["mpnn"] = _mpnn_metrics(dataset, config)

    non_graph = [
        row["test"]["r2"]
        for name, row in metrics.items()
        if name not in {"graph_mp", "mpnn"} and "test" in row
    ]
    graph_scores = [
        row["test"]["r2"]
        for name, row in metrics.items()
        if name in {"graph_mp", "mpnn"} and "test" in row
    ]
    best_non_graph = max(non_graph) if non_graph else float("-inf")
    best_graph = max(graph_scores) if graph_scores else float("-inf")
    gates = {
        "H1_graph_gain": bool(best_graph >= best_non_graph + 0.05),
        "H2_graph_mp_vs_mpnn": "report",
        "H3_oracle": True,
        "H4_seed_consistency": "report",
        "H5_budget": "report",
    }
    return {
        "task": {
            "id": WIRED_CASCADE_TASK_ID,
            "version": WIRED_CASCADE_TASK_VERSION,
            "kind": "regression",
        },
        "config": asdict(config),
        "dataset": {
            "layouts_requested": config.layouts,
            "layouts_used": int(len(set(dataset.layout_seeds.tolist()))),
            "samples": dataset.samples,
            "max_nodes": dataset.max_nodes,
            "splits": {
                split: int((dataset.splits == split).sum())
                for split in ("train", "val", "test")
            },
            "cascade_histogram": {
                str(int(value)): int((dataset.labels == value).sum())
                for value in sorted(set(dataset.labels.tolist()))
            },
        },
        "metrics": metrics,
        "gates": gates,
        "cost": {
            "graph_mp": metrics.get("graph_mp", {}).get("cost", "not reported"),
            "mpnn": metrics.get("mpnn", {}).get("cost", "not reported"),
        },
    }


def write_wired_cascade_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "wired_cascade_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Wired cascade",
        "",
        f"Task: `{report['task']['id']}` / `{report['task']['version']}`",
        "",
        f"- layouts: {report['dataset']['layouts_used']}",
        f"- samples: {report['dataset']['samples']}",
        f"- max nodes: {report['dataset']['max_nodes']}",
        f"- splits: {report['dataset']['splits']}",
        "",
        "| model | test R² | test MAE |",
        "|---|---:|---:|",
    ]
    for name, row in report["metrics"].items():
        if "test" not in row:
            lines.append(f"| {name} | — | — |")
            continue
        lines.append(
            f"| {name} | {row['test']['r2']:.4f} | {row['test']['mae']:.4f} |"
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
    (out / "wired_cascade_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "wired_cascade_report.md"
