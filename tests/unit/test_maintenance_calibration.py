from __future__ import annotations

import numpy as np
import pytest

from fabline.harness.maintenance_calibration import (
    MaintenanceCalibrationConfig,
    generate_maintenance_calibration,
    run_maintenance_calibration,
    write_maintenance_calibration_report,
)


def test_maintenance_calibration_config_validation() -> None:
    with pytest.raises(ValueError):
        MaintenanceCalibrationConfig(episodes=0)
    with pytest.raises(ValueError):
        MaintenanceCalibrationConfig(horizon=0)
    with pytest.raises(ValueError):
        MaintenanceCalibrationConfig(maintenance_probability=1.5)


def test_maintenance_calibration_generation() -> None:
    data = generate_maintenance_calibration(
        MaintenanceCalibrationConfig(
            episodes=4,
            seed_start=61000,
            horizon=5,
        )
    )
    assert data["observation"].shape[1] == 15
    assert len(data["label"]) == len(data["split"])
    assert set(np.unique(data["label"])) <= {0.0, 1.0}


def test_maintenance_calibration_runs(tmp_path) -> None:
    results = run_maintenance_calibration(
        MaintenanceCalibrationConfig(episodes=12, seed_start=61000)
    )
    assert set(results["views"]) == {
        "diagnostics",
        "diagnostics_maintenance",
    }
    for view in results["views"].values():
        assert "gbdt" in view["metrics"]
        assert "brier" in view["calibration"]["gbdt"]["test"]
    report = write_maintenance_calibration_report(tmp_path, results)
    assert report.exists()
