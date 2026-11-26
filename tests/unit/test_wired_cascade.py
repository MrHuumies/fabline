from __future__ import annotations

from pathlib import Path

from fabline.harness.wired_cascade import (
    WiredCascadeConfig,
    generate_cascade_dataset,
    run_wired_cascade,
    write_wired_cascade_report,
)


def _config(**overrides: object) -> WiredCascadeConfig:
    values: dict[str, object] = {
        "layouts": 8,
        "seed_start": 500,
        "max_faults_per_layout": 3,
        "warmup_ticks": 10,
        "mpnn_epochs": 2,
        "mpnn_hidden": 8,
        "mpnn_layers": 1,
        "mpnn_batch_size": 4,
        "seed": 0,
    }
    values.update(overrides)
    return WiredCascadeConfig(**values)  # type: ignore[arg-type]


def test_cascade_dataset_shapes() -> None:
    dataset = generate_cascade_dataset(_config())
    assert dataset.samples > 0
    assert dataset.vector.shape == (dataset.samples, 22)
    assert dataset.entity_features.shape[0] == dataset.samples
    assert dataset.entity_features.shape[2] == 14
    assert dataset.entity_mask.shape == (
        dataset.samples,
        dataset.max_nodes,
    )
    assert dataset.adjacency.shape == (
        dataset.samples,
        dataset.max_nodes,
        dataset.max_nodes,
    )
    assert set(dataset.splits).issubset({"train", "val", "test"})
    assert (dataset.labels >= 0).all()


def test_wired_cascade_runs_and_reports() -> None:
    report = run_wired_cascade(_config(), include_mpnn=True)
    assert report["task"]["id"] == "factory.power.cascade.v1"
    assert report["dataset"]["samples"] > 0
    assert "graph_mp" in report["metrics"]
    assert "test" in report["metrics"]["graph_mp"]
    assert "mpnn" in report["metrics"]
    assert isinstance(report["gates"]["H1_graph_gain"], bool)


def test_wired_cascade_report(tmp_path: Path) -> None:
    report = run_wired_cascade(_config(), include_mpnn=False)
    path = write_wired_cascade_report(tmp_path, report)
    assert path.exists()
    assert "Wired cascade" in path.read_text(encoding="utf-8")
    assert (tmp_path / "wired_cascade_results.json").exists()
