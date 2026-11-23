"""Named multiview observation and view-mask plumbing.

The multiview adapter keeps each view separate so a consumer can train a
per-view model and apply a mask at prediction time. ``flatten`` is the tabular
baseline path: it keeps a fixed width and zeroes masked views.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import WorldState

from .base import ObservationAdapter, ObservationSpec, flatten_observation

ViewFactory = Callable[
    [FactoryConfig, FaultConfig | None, PowerConfig | None],
    ObservationAdapter,
]

_VIEW_FACTORIES: dict[str, ViewFactory] = {}


def register_view(name: str, factory: ViewFactory) -> None:
    """Register a named view factory for multiview consumers."""

    if not name:
        raise ValueError("view name must be non-empty")
    _VIEW_FACTORIES[name] = factory


def build_registered_view(
    name: str,
    config: FactoryConfig,
    faults: FaultConfig | None = None,
    power: PowerConfig | None = None,
) -> ObservationAdapter:
    if name in _VIEW_FACTORIES:
        return _VIEW_FACTORIES[name](config, faults, power)
    from .base import build_observation

    return build_observation(name, config, faults, power)


@dataclass(frozen=True)
class MultiviewFrame:
    """One observation with a named view dictionary and boolean mask."""

    views: dict[str, np.ndarray]
    view_mask: dict[str, bool]

    def __post_init__(self) -> None:
        if set(self.views) != set(self.view_mask):
            raise ValueError("views and view_mask must have the same keys")
        for name in self.views:
            if not isinstance(self.view_mask[name], bool):
                raise ValueError(f"view_mask[{name!r}] must be a bool")

    def active(self, name: str) -> bool:
        return self.view_mask.get(name, False)


class MultiviewObservation:
    """A versioned dictionary of observation adapters with a view mask."""

    def __init__(
        self,
        config: FactoryConfig,
        views: Mapping[str, ObservationAdapter],
        view_mask: Mapping[str, bool] | None = None,
    ) -> None:
        if not views:
            raise ValueError("multiview requires at least one view")
        self.config = config
        self.views = dict(views)
        self.view_mask = {
            name: True if view_mask is None else bool(view_mask.get(name, True))
            for name in self.views
        }
        unknown = set(view_mask or {}) - set(self.views)
        if unknown:
            raise ValueError(f"mask names unknown views: {sorted(unknown)}")
        feature_names: list[str] = []
        width = 0
        for name, adapter in self.views.items():
            shape = adapter.spec.shape
            if shape is None:
                width = -1
                break
            size = int(np.prod(shape))
            width += size
            if adapter.spec.feature_names:
                feature_names.extend(
                    f"{name}:{feature}"
                    for feature in adapter.spec.feature_names
                )
        self.spec = ObservationSpec(
            name="multiview",
            version="1.0.0",
            shape=(width,) if width >= 0 else None,
            feature_names=tuple(feature_names) if width >= 0 else None,
        )

    def observe(
        self,
        state: WorldState,
        view_mask: Mapping[str, bool] | None = None,
    ) -> MultiviewFrame:
        mask = dict(self.view_mask)
        if view_mask is not None:
            unknown = set(view_mask) - set(self.views)
            if unknown:
                raise ValueError(f"mask names unknown views: {sorted(unknown)}")
            mask.update({name: bool(value) for name, value in view_mask.items()})
        return MultiviewFrame(
            views={
                name: np.asarray(adapter.observe(state), dtype=np.float32)
                for name, adapter in self.views.items()
            },
            view_mask=mask,
        )

    def flatten(self, frame: MultiviewFrame) -> np.ndarray:
        parts: list[np.ndarray] = []
        for name, adapter in self.views.items():
            values = flatten_observation(adapter, frame.views[name])
            if not frame.view_mask.get(name, False):
                values = np.zeros_like(values)
            parts.append(values)
        return np.concatenate(parts).astype(np.float32, copy=False)
