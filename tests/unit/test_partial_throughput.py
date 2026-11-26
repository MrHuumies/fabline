from __future__ import annotations

from pathlib import Path

import numpy as np

from fabline.harness.partial_throughput import (
    PartialThroughputConfig,
    generate_partial_dataset,
    run_partial_throughput,
    write_partial_throughput_report,
)


def _config(**overrides: object) -> PartialThroughputConfig:
    values: dict[str, object] = {
        "episodes": 6,
        "warmup_ticks": 30,
        "episode_ticks": 100,
        "sample_interval": 10,
        "horizon": 20,
        "dropout": 0.6,
        "window": 3,
        "sequence_epochs": 2,
        "sequence_hidden": 8,
        "sequence_layers": 1,
        "sequence_batch_size": 4,
        "seed": 0,
    }
    values.update(overrides)
    return PartialThroughputConfig(**values)  # type: ignore[arg-type]


def test_partial_dataset_shapes() -> None:
    dataset = generate_partial_dataset(_config())
    assert dataset.samples > 0
    assert dataset.current.shape == (dataset.samples, 13)
    assert dataset.single.shape == (dataset.samples, 26)
    assert dataset.window.shape == (dataset.samples, 78)
    assert set(dataset.splits).issubset({"train", "val", "test"})
    assert np.all(np.isfinite(dataset.labels))


def test_partial_deterministic() -> None:
    first = generate_partial_dataset(_config())
    second = generate_partial_dataset(_config())
    np.testing.assert_allclose(first.current, second.current)
    np.testing.assert_allclose(first.single, second.single)
    np.testing.assert_allclose(first.window, second.window)


def test_partial_runs_and_reports() -> None:
    report = run_partial_throughput(_config(), include_sequence=True)
    assert report["task"]["id"] == "factory.throughput.partial.v1"
    assert "current" in report["views"]
    assert "single" in report["views"]
    assert "window" in report["views"]
    assert "H1_mask_loss" in report["gates"]
    assert isinstance(report["gates"]["H1_mask_loss"], bool)


def test_partial_report(tmp_path: Path) -> None:
    report = run_partial_throughput(_config(), include_sequence=False)
    path = write_partial_throughput_report(tmp_path, report)
    assert path.exists()
    assert "Partial throughput" in path.read_text(encoding="utf-8")
    assert (tmp_path / "partial_throughput_results.json").exists()
