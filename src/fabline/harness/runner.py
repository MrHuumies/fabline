"""M1 benchmark runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .baselines import evaluate_baselines
from .data import LoadedDataset
from .report import write_benchmark_report


def run_throughput_benchmark(
    dataset: LoadedDataset,
    out_dir: str | Path,
) -> dict[str, dict[str, Any]]:
    splits = np.asarray(dataset.splits)
    train = splits == "train"
    val = splits == "val"
    test = splits == "test"
    if not train.any() or not val.any() or not test.any():
        raise ValueError("dataset must contain train, val, and test episodes")

    results = evaluate_baselines(
        dataset.X[train],
        dataset.y[train],
        dataset.X[val],
        dataset.y[val],
        dataset.X[test],
        dataset.y[test],
        dataset.feature_names,
    )
    write_benchmark_report(
        out_dir,
        dataset.manifest.get("name", "dataset"),
        results,
        dataset.manifest,
    )
    return results
