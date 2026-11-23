"""Generic view-arrival data contracts.

This module defines the task-facing shape of a view-arrival experiment. The
runner is deliberately separate: a task only has to expose named views, labels,
episode-grouped splits, and the base/new/retention view roles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class ViewArrivalSpec:
    """Roles and versioning for one view-arrival task."""

    task_id: str
    task_version: str
    base_views: tuple[str, ...]
    new_view: str
    retention_views: tuple[str, ...]
    label: str

    def __post_init__(self) -> None:
        if not self.task_id or not self.task_version:
            raise ValueError("task id and version must be non-empty")
        if not self.base_views:
            raise ValueError("base_views must be non-empty")
        if self.new_view in self.base_views:
            raise ValueError("new_view must not be a base view")
        if not self.retention_views:
            raise ValueError("retention_views must be non-empty")
        if not set(self.retention_views).issubset(set(self.base_views)):
            raise ValueError("retention views must be base views")
        if not self.label:
            raise ValueError("label must be non-empty")


@dataclass(frozen=True)
class ViewArrivalData:
    """Tabular views and episode-grouped labels for a view-arrival task."""

    views: dict[str, np.ndarray]
    view_mask: dict[str, bool]
    labels: np.ndarray
    splits: np.ndarray
    episode_ids: np.ndarray

    def __post_init__(self) -> None:
        if not self.views:
            raise ValueError("views must be non-empty")
        if set(self.views) != set(self.view_mask):
            raise ValueError("views and view_mask must have the same keys")
        for name, values in self.views.items():
            if values.ndim < 1:
                raise ValueError(f"view {name!r} must have a sample axis")
        lengths = {len(values) for values in self.views.values()}
        lengths.update(
            {
                len(self.labels),
                len(self.splits),
                len(self.episode_ids),
            }
        )
        if len(lengths) != 1:
            raise ValueError("views, labels, splits, episode_ids must align")
        if len(self.episode_ids) == 0:
            raise ValueError("view-arrival data must not be empty")
        for episode_id in np.unique(self.episode_ids):
            episode_splits = set(
                self.splits[self.episode_ids == episode_id].tolist()
            )
            if len(episode_splits) != 1:
                raise ValueError(
                    f"episode {episode_id!r} spans multiple splits"
                )


class ViewArrivalTask(Protocol):
    spec: ViewArrivalSpec

    def load(self) -> ViewArrivalData: ...


def validate_view_selection(
    spec: ViewArrivalSpec,
    data: ViewArrivalData,
) -> None:
    """Check that a task's declared views exist in its data."""

    expected = set(spec.base_views) | {spec.new_view}
    missing = expected - set(data.views)
    if missing:
        raise ValueError(f"task data is missing views: {sorted(missing)}")
