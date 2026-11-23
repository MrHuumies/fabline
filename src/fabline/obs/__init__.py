"""Observation adapters."""

from __future__ import annotations

from .base import ObservationSpec, build_observation, flatten_observation
from .entities import EntitiesObservation, GraphObservation
from .grid import GridObservation
from .interaction import FaultPowerObservation
from .line import LineStateObservation
from .multiview import MultiviewFrame, MultiviewObservation, build_registered_view, register_view
from .partial import DelayedObservation, FeatureDropoutObservation, GridFogObservation
from .power import PowerControlObservation, PowerGridObservation, PowerObservation
from .sensors import (
    DiagnosticsObservation,
    SensorsObservation,
    TopKEntitySensorsObservation,
)
from .vector import VectorObservation

__all__ = [
    "DiagnosticsObservation",
    "EntitiesObservation",
    "FaultPowerObservation",
    "DelayedObservation",
    "FeatureDropoutObservation",
    "GraphObservation",
    "GridFogObservation",
    "GridObservation",
    "LineStateObservation",
    "MultiviewFrame",
    "MultiviewObservation",
    "ObservationSpec",
    "PowerControlObservation",
    "PowerGridObservation",
    "PowerObservation",
    "SensorsObservation",
    "TopKEntitySensorsObservation",
    "VectorObservation",
    "build_observation",
    "build_registered_view",
    "register_view",
    "flatten_observation",
]
