from __future__ import annotations

import numpy as np
import pytest

from fabline.env.crew_replan import CrewReplanEnv
from fabline.harness.planning_triage import (
    TriagePlanningConfig,
    _encode,
    _factory_config,
    _replan_config,
    _run_sequence,
)


def test_planning_config_validation() -> None:
    with pytest.raises(ValueError):
        TriagePlanningConfig(elites=0)
    with pytest.raises(ValueError):
        TriagePlanningConfig(elites=10, population=4)
    with pytest.raises(ValueError):
        TriagePlanningConfig(model_seeds=0)


def test_planning_encoding_shape() -> None:
    initial = np.zeros(25, dtype=np.float32)
    encoded = _encode(initial, (2, 8, 12))
    assert encoded.shape == (49,)
    assert encoded[25 + 2] == 1.0
    assert encoded[16 + 25 + 2] == 1.0
    assert encoded[20 + 25 + 3] == 1.0


def test_planning_sequence_runs() -> None:
    env = CrewReplanEnv(_factory_config(), _replan_config())
    score, initial = _run_sequence(env, (0, 0, 0), 0)
    assert score >= 0.0
    assert initial.shape == (25,)
