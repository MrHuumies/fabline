"""Typed semantic events.

Events are ground truth for analysis and replay diagnostics. They are not part
of the state hash because they do not affect future transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Event:
    tick: int
    kind: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"tick": self.tick, "kind": self.kind, "data": self.data}
