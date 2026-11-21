from __future__ import annotations

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from fabline.render.app import run_factory_viewer  # noqa: E402
from fabline.render.factory_view import FactoryView, render_frame  # noqa: E402


def test_factory_view_is_read_only(line_world) -> None:
    pygame.init()
    before = line_world.state_hash()
    view = FactoryView(line_world.config)
    surface = view.render(line_world.state)
    assert surface.get_size() == (view.width, view.height)
    assert line_world.state_hash() == before


def test_render_frame_returns_surface(line_world) -> None:
    pygame.init()
    surface = render_frame(line_world.state, line_world.config)
    assert surface.get_width() > 0
    assert surface.get_height() > 0


def test_screenshot_mode(tmp_path, small_config) -> None:
    target = tmp_path / "shot.png"
    run_factory_viewer(
        small_config,
        seed=0,
        screenshot=str(target),
        screenshot_ticks=20,
    )
    assert target.exists()
    assert target.stat().st_size > 0
