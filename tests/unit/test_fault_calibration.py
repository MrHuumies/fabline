from __future__ import annotations

import numpy as np
import pytest

from fabline.harness.fault_calibration import (
    FaultCalibrationConfig,
    generate_fault_calibration,
)


def test_fault_calibration_config_validation() -> None:
    with pytest.raises(ValueError):
        FaultCalibrationConfig(episodes=0)
    with pytest.raises(ValueError):
        FaultCalibrationConfig(horizon=0)
    with pytest.raises(ValueError):
        FaultCalibrationConfig(noise=-0.1)


def test_fault_calibration_generation() -> None:
    data = generate_fault_calibration(
        FaultCalibrationConfig(
            episodes=2,
            seed_start=56000,
            sample_interval=10,
            horizon=5,
        )
    )
    assert set(data) == {
        "context",
        "thermal",
        "vibration",
        "top4",
        "label",
        "split",
    }
    assert data["context"].shape[1] == 7
    assert data["top4"].shape[1] == 32
    assert len(data["label"]) == len(data["split"])
    assert set(np.unique(data["label"])) <= {0.0, 1.0}
