from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("torch")

from fabline.harness.models import (  # noqa: E402
    CNNRegressor,
    GRURegressor,
    MPNNRegressor,
    TorchTrainConfig,
    TransformerRegressor,
    torch_available,
)

CONFIG = TorchTrainConfig(epochs=2, batch_size=4, hidden=8, seed=0)


def _grid_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    grids = rng.normal(size=(12, 8, 8, 3)).astype(np.float32)
    targets = grids.mean(axis=(1, 2, 3))
    return grids[:8], targets[:8], grids[8:]


def _graph_data() -> tuple[
    tuple[np.ndarray, np.ndarray, np.ndarray],
    np.ndarray,
    tuple[np.ndarray, np.ndarray, np.ndarray],
]:
    rng = np.random.default_rng(1)
    count, nodes, features = 12, 6, 4
    values = rng.normal(size=(count, nodes, features)).astype(np.float32)
    mask = np.ones((count, nodes), dtype=np.float32)
    mask[::3, -1] = 0.0
    adjacency = (rng.random((count, nodes, nodes)) < 0.25).astype(np.float32)
    adjacency = np.maximum(adjacency, adjacency.transpose(0, 2, 1))
    targets = np.asarray(
        [
            values[index][mask[index] > 0].sum()
            for index in range(count)
        ],
        dtype=np.float32,
    )
    train = (values[:8], mask[:8], adjacency[:8])
    test = (values[8:], mask[8:], adjacency[8:])
    return train, targets[:8], test


def _sequence_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(2)
    sequences = rng.normal(size=(12, 5, 3)).astype(np.float32)
    targets = sequences[:, -1, :].sum(axis=1)
    return sequences[:8], targets[:8], sequences[8:]


def test_torch_available() -> None:
    assert torch_available()


def test_cnn_fit_predict_and_report() -> None:
    train, targets, test = _grid_data()
    model = CNNRegressor(CONFIG).fit(train, targets)
    predictions = model.predict(test)
    assert predictions.shape == (len(test),)
    assert np.all(np.isfinite(predictions))
    assert model.report is not None
    assert model.report.samples == len(train)
    assert model.report.parameters > 0
    assert model.report.epochs == 2


def test_mpnn_fit_predict_and_report() -> None:
    train, targets, test = _graph_data()
    model = MPNNRegressor(CONFIG, layers=2).fit(
        train[0], train[1], train[2], targets
    )
    predictions = model.predict(test[0], test[1], test[2])
    assert predictions.shape == (len(test[0]),)
    assert np.all(np.isfinite(predictions))
    assert model.report is not None
    assert model.report.parameters > 0


def test_gru_fit_predict_and_report() -> None:
    train, targets, test = _sequence_data()
    model = GRURegressor(CONFIG).fit(train, targets)
    predictions = model.predict(test)
    assert predictions.shape == (len(test),)
    assert np.all(np.isfinite(predictions))
    assert model.report is not None


def test_transformer_fit_predict_and_report() -> None:
    train, targets, test = _sequence_data()
    model = TransformerRegressor(CONFIG, layers=1, heads=2).fit(train, targets)
    predictions = model.predict(test)
    assert predictions.shape == (len(test),)
    assert np.all(np.isfinite(predictions))
    assert model.report is not None


def test_deterministic_seed() -> None:
    train, targets, test = _grid_data()
    first = CNNRegressor(CONFIG).fit(train, targets).predict(test)
    second = CNNRegressor(CONFIG).fit(train, targets).predict(test)
    np.testing.assert_allclose(first, second, rtol=1e-6, atol=1e-6)


def test_shape_validation() -> None:
    train, targets, _ = _grid_data()
    model = CNNRegressor(CONFIG).fit(train, targets)
    with pytest.raises(ValueError):
        model.predict(train[:, :4, :4, :])
    with pytest.raises(ValueError):
        CNNRegressor(CONFIG).fit(train.reshape(8, -1), targets)
