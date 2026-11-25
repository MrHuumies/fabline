from __future__ import annotations

import numpy as np

from fabline.env.crew_replan import CrewReplanEnv
from fabline.harness.planning_transition import (
    DeltaTransitionModel,
    EnsembleTransitionModel,
    TwoStepDeltaModel,
    _action_index,
    _encode,
    _encode_pair,
    _spearman,
    _trace_sequence,
)
from fabline.harness.planning_triage import _factory_config, _replan_config


def test_transition_encoding_layout() -> None:
    state = np.zeros(25, dtype=np.float64)
    encoded = _encode(state, phase=0, action=5)
    assert encoded.shape == (48,)
    assert encoded[25] == 1.0
    assert encoded[28 + 5] == 1.0
    assert _action_index(1, 4) == 17
    assert _action_index(2, 12) == 19


def test_pair_encoding_layout() -> None:
    encoded = _encode_pair(np.zeros(25), phase=0, action=5, next_action=4)
    assert encoded.shape == (68,)
    assert encoded[25] == 1.0
    assert encoded[28 + 5] == 1.0
    assert encoded[48 + 17] == 1.0


def test_two_step_model_fits_and_scores() -> None:
    rng = np.random.default_rng(2)
    x = rng.normal(size=(64, 68))
    y = np.zeros((64, 26))
    y[:, :25] = 0.01 * x[:, :25]
    two_step = TwoStepDeltaModel(ridge=1.0)
    two_step.fit(x, y)
    state, done = two_step.predict_pair(np.full(25, 0.5), 0, 0, 0)
    assert state.shape == (25,)
    assert isinstance(done, bool)
    one_step = DeltaTransitionModel(ridge=1.0)
    one_step.fit(x[:, :48], y)
    score = two_step.score_pair(
        np.full(25, 0.5), [0, 0, 0], one_step
    )
    assert np.isfinite(score)


def test_delta_transition_model_fits_and_clips() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(size=(64, 48))
    y = np.zeros((64, 26))
    y[:, :25] = 0.01 * x[:, :25]
    model = DeltaTransitionModel(ridge=1.0)
    model.fit(x, y)
    predicted = model.predict_delta(x[:4])
    assert predicted.shape == (4, 26)
    next_state, done = model.predict_step(
        np.full(25, 0.5), phase=0, action=0
    )
    assert next_state.shape == (25,)
    assert isinstance(done, bool)
    assert np.all(next_state >= 0.0)
    assert np.all(next_state <= 1.0)
    score = model.score(np.full(25, 0.5), [0, 0, 0])
    assert np.isfinite(score)


def test_transition_ensemble_fits_and_scores() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(size=(64, 48))
    y = np.zeros((64, 26))
    y[:, :25] = 0.01 * x[:, :25]
    ensemble = EnsembleTransitionModel.fit(
        x,
        y,
        members=3,
        ridge=1.0,
        seed=0,
    )
    mean, std = ensemble.score_stats(np.full(25, 0.5), [0, 0, 0])
    assert np.isfinite(mean)
    assert std >= 0.0
    assert ensemble.mean_mse(x, y) >= 0.0
    assert _spearman([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) > 0.9


def test_transition_trace_has_three_decisions() -> None:
    env = CrewReplanEnv(_factory_config(), _replan_config())
    score, states, actions, next_states, dones = _trace_sequence(
        env, (5, 4, 8), 49000
    )
    assert score >= 0.0
    assert len(states) == 3
    assert len(actions) == 3
    assert len(next_states) == 3
    assert len(dones) == 3
    assert dones[-1] is True
