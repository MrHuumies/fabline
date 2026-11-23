from __future__ import annotations

import numpy as np
import pytest

from fabline.tasks.view_arrival import (
    ViewArrivalData,
    ViewArrivalSpec,
    validate_view_selection,
)


def _data() -> ViewArrivalData:
    return ViewArrivalData(
        views={
            "vector": np.zeros((4, 3), dtype=np.float32),
            "power": np.ones((4, 2), dtype=np.float32),
        },
        view_mask={"vector": True, "power": False},
        labels=np.asarray([0, 1, 0, 1]),
        splits=np.asarray(["train", "train", "test", "test"]),
        episode_ids=np.asarray(["e1", "e1", "e2", "e2"]),
    )


def test_view_arrival_spec_roles() -> None:
    spec = ViewArrivalSpec(
        task_id="factory.power.brownout.v1",
        task_version="0.1.0",
        base_views=("vector",),
        new_view="power",
        retention_views=("vector",),
        label="brownout",
    )
    assert spec.new_view not in spec.base_views
    with pytest.raises(ValueError):
        ViewArrivalSpec(
            task_id="x",
            task_version="1",
            base_views=("vector",),
            new_view="vector",
            retention_views=("vector",),
            label="label",
        )
    with pytest.raises(ValueError):
        ViewArrivalSpec(
            task_id="x",
            task_version="1",
            base_views=("vector",),
            new_view="power",
            retention_views=("line",),
            label="label",
        )


def test_view_arrival_data_alignment_and_grouped_splits() -> None:
    data = _data()
    assert len(data.labels) == 4
    with pytest.raises(ValueError):
        ViewArrivalData(
            views={"vector": np.zeros((3, 3), dtype=np.float32)},
            view_mask={"vector": True},
            labels=np.zeros(4),
            splits=np.asarray(["train"] * 4),
            episode_ids=np.asarray(["e1"] * 4),
        )
    with pytest.raises(ValueError):
        ViewArrivalData(
            views={"vector": np.zeros((2, 3), dtype=np.float32)},
            view_mask={"vector": True},
            labels=np.zeros(2),
            splits=np.asarray(["train", "test"]),
            episode_ids=np.asarray(["e1", "e1"]),
        )


def test_validate_view_selection() -> None:
    spec = ViewArrivalSpec(
        task_id="x",
        task_version="1",
        base_views=("vector",),
        new_view="power",
        retention_views=("vector",),
        label="label",
    )
    validate_view_selection(spec, _data())
    bad = ViewArrivalData(
        views={"vector": np.zeros((2, 3), dtype=np.float32)},
        view_mask={"vector": True},
        labels=np.zeros(2),
        splits=np.asarray(["train", "train"]),
        episode_ids=np.asarray(["e1", "e1"]),
    )
    with pytest.raises(ValueError):
        validate_view_selection(spec, bad)
