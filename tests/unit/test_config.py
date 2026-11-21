from __future__ import annotations

from pathlib import Path

import pytest

from fabline.core.hashing import config_hash
from fabline.worlds.factory.config import FactoryConfig, load_config


def test_defaults_validate() -> None:
    config = FactoryConfig()
    assert config.width == 32
    assert config.height == 32
    assert config.ticks_per_episode == 500


def test_unknown_key_rejected() -> None:
    with pytest.raises(ValueError, match="unknown config keys"):
        FactoryConfig.from_dict({"width": 16, "height": 8, "nope": 1})


def test_invalid_values_rejected() -> None:
    with pytest.raises(ValueError):
        FactoryConfig(width=4)
    with pytest.raises(ValueError):
        FactoryConfig(rock_density=1.0)
    with pytest.raises(ValueError):
        FactoryConfig(entity_budget=2)


def test_toml_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "factory.toml"
    path.write_text("width = 16\nheight = 8\nstarter_line = false\n", encoding="utf-8")
    config = load_config(path)
    assert config.width == 16
    assert config.height == 8
    assert config.starter_line is False


def test_repo_config_loads() -> None:
    root = Path(__file__).resolve().parents[2]
    config = load_config(root / "configs" / "factory_debug.toml")
    assert config.width == 32
    assert config.ticks_per_episode == 500


def test_config_hash_is_stable() -> None:
    first = FactoryConfig()
    second = FactoryConfig()
    third = FactoryConfig(width=16, height=8)
    assert config_hash(first) == config_hash(second)
    assert config_hash(first) != config_hash(third)
