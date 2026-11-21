"""Deterministic hashing for state, configs, and manifests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any, cast


def canonical_json(value: Any) -> str:
    """Serialize a value deterministically.

    Values must be JSON-compatible after ``to_canonical`` conversion. This
    helper deliberately does not try to be clever about arbitrary objects.
    """

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_hash(value: Any) -> str:
    """Return a sha256 hex digest of the canonical JSON form of ``value``."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def config_hash(config: Any) -> str:
    """Hash a dataclass config or a plain mapping."""

    if is_dataclass(config) and not isinstance(config, type):
        return canonical_hash(asdict(cast(Any, config)))
    return canonical_hash(config)
