from __future__ import annotations

import numpy as np

from fabline.harness.baselines import evaluate_classification_baselines
from fabline.harness.graph_models import (
    GraphMPBaseline,
    evaluate_graph_baseline,
    message_passing_features,
)
from fabline.harness.metrics import classification_metrics
from fabline.tasks.control_dynamics import generate_control_transitions
from fabline.worlds.factory.config import FactoryConfig


def test_message_passing_features_shape(line_world) -> None:
    from fabline.obs import EntitiesObservation

    adapter = EntitiesObservation(line_world.config)
    graph = adapter.observe(line_world.state)
    features = message_passing_features(
        graph.entity_features[None, ...],
        graph.entity_mask[None, ...],
        graph.adjacency[None, ...],
    )
    assert features.shape == (1, 6 * len(graph.feature_names) + 2)
    assert np.all(np.isfinite(features))


def test_graph_mp_baseline_runs() -> None:
    rng = np.random.default_rng(0)
    count, nodes, features = 30, 8, 6
    entity_features = rng.normal(size=(count, nodes, features))
    entity_mask = np.ones((count, nodes), dtype=bool)
    adjacency = (rng.random((count, nodes, nodes)) < 0.1).astype(np.float32)
    y = rng.normal(size=count)
    splits = np.array(["train"] * 18 + ["val"] * 6 + ["test"] * 6, dtype=object)
    results = evaluate_graph_baseline(
        {
            "entity_features": entity_features,
            "entity_mask": entity_mask,
            "adjacency": adjacency,
        },
        splits,
        y,
    )
    assert "graph_mp" in results
    assert "test" in results["graph_mp"]

    model = GraphMPBaseline()
    model.fit(
        entity_features[:18],
        entity_mask[:18],
        adjacency[:18],
        y[:18],
    )
    predictions = model.predict(
        entity_features[18:],
        entity_mask[18:],
        adjacency[18:],
    )
    assert predictions.shape == (12,)


def test_classification_metrics() -> None:
    truth = np.array(["a", "a", "b", "b", "c"])
    pred = np.array(["a", "b", "b", "b", "c"])
    metrics = classification_metrics(truth, pred)
    assert metrics["accuracy"] == 0.8
    assert metrics["balanced_accuracy"] == (0.5 + 1.0 + 1.0) / 3
    assert 0.0 <= metrics["macro_f1"] <= 1.0


def test_control_dynamics_dataset() -> None:
    from fabline.env.control import ControlConfig

    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=300,
        rock_density=0.0,
        starter_line=False,
    )
    dataset = generate_control_transitions(
        config,
        ControlConfig(episode_ticks=300),
        episodes=3,
        seed=0,
    )
    assert dataset.X.shape[1] == 49 + 6
    assert dataset.y.shape[1] == 49
    assert len(dataset.X) == len(dataset.y) == len(dataset.splits)
    assert len(dataset.action_names) == 6


def test_classification_baselines() -> None:
    rng = np.random.default_rng(1)
    X = rng.normal(size=(60, 4))
    y = np.where(X[:, 0] > 0.0, "positive", "negative")
    splits = np.array(["train"] * 36 + ["val"] * 12 + ["test"] * 12, dtype=object)
    train = splits == "train"
    val = splits == "val"
    test = splits == "test"
    results = evaluate_classification_baselines(
        X[train],
        y[train],
        X[val],
        y[val],
        X[test],
        y[test],
    )
    assert set(results) == {"majority", "gbdt", "mlp"}
    assert "test" in results["gbdt"]
