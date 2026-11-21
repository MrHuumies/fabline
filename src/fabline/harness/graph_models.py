"""A message-passing feature baseline for the entity graph.

This is not an end-to-end GNN. It applies one and two normalized graph
aggregation steps, pools node features, and trains a tabular regressor on the
pooled representation. It is a relational baseline that uses the graph
structure, unlike the flattened tabular baselines.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fabline.harness.baselines import GradientBoostingBaseline
from fabline.harness.metrics import regression_metrics


def message_passing_features(
    entity_features: np.ndarray,
    entity_mask: np.ndarray,
    adjacency: np.ndarray,
) -> np.ndarray:
    features = np.asarray(entity_features, dtype=np.float64)
    mask = np.asarray(entity_mask, dtype=bool)
    adjacency = np.asarray(adjacency, dtype=np.float64)
    if features.ndim != 3 or mask.ndim != 2 or adjacency.ndim != 3:
        raise ValueError("expected (N,M,F), (N,M), (N,M,M) arrays")
    count, nodes, _ = features.shape
    mask_float = mask[..., None].astype(np.float64)
    features = features * mask_float

    identity = np.eye(nodes, dtype=np.float64)[None, :, :]
    normalized = adjacency + identity
    degree = normalized.sum(axis=2, keepdims=True)
    normalized = normalized / np.maximum(degree, 1.0)

    hop1 = normalized @ features
    hop2 = normalized @ hop1
    denominators = np.maximum(mask.sum(axis=1, keepdims=True), 1.0)[..., None]

    def pool(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return values.sum(axis=1), values.sum(axis=1) / denominators[:, 0, :]

    sum0, mean0 = pool(features)
    sum1, mean1 = pool(hop1)
    sum2, mean2 = pool(hop2)
    node_count = mask.sum(axis=1, keepdims=True) / max(1, nodes)
    edge_count = adjacency.sum(axis=(1, 2))[:, None] / max(1, nodes * nodes)
    return np.concatenate(
        [sum0, mean0, sum1, mean1, sum2, mean2, node_count, edge_count],
        axis=1,
    )


@dataclass
class GraphMPBaseline:
    name: str = "graph_mp"

    def __post_init__(self) -> None:
        self.model = GradientBoostingBaseline()

    def fit(
        self,
        entity_features: np.ndarray,
        entity_mask: np.ndarray,
        adjacency: np.ndarray,
        y: np.ndarray,
    ) -> None:
        self.model.fit(
            message_passing_features(entity_features, entity_mask, adjacency),
            y,
        )

    def predict(
        self,
        entity_features: np.ndarray,
        entity_mask: np.ndarray,
        adjacency: np.ndarray,
    ) -> np.ndarray:
        return self.model.predict(
            message_passing_features(entity_features, entity_mask, adjacency)
        )


def evaluate_graph_baseline(
    graph: dict[str, np.ndarray],
    splits: np.ndarray,
    y: np.ndarray,
    *,
    graph_extra: dict[str, np.ndarray] | None = None,
    y_extra: np.ndarray | None = None,
) -> dict[str, dict[str, object]]:
    features = graph["entity_features"]
    mask = graph["entity_mask"]
    adjacency = graph["adjacency"]
    train = np.asarray(splits) == "train"
    val = np.asarray(splits) == "val"
    test = np.asarray(splits) == "test"
    model = GraphMPBaseline()
    model.fit(features[train], mask[train], adjacency[train], y[train])
    result: dict[str, object] = {
        "val": regression_metrics(
            y[val],
            model.predict(features[val], mask[val], adjacency[val]),
        ),
        "test": regression_metrics(
            y[test],
            model.predict(features[test], mask[test], adjacency[test]),
        ),
    }
    if graph_extra is not None and y_extra is not None:
        result["shift"] = regression_metrics(
            y_extra,
            model.predict(
                graph_extra["entity_features"],
                graph_extra["entity_mask"],
                graph_extra["adjacency"],
            ),
        )
    return {"graph_mp": result}
