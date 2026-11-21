from __future__ import annotations

import os
import platform
import time

import pytest

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.world import FactoryWorld

pytestmark = pytest.mark.perf


@pytest.mark.skipif(
    os.environ.get("FABLINE_PERF") != "1",
    reason="set FABLINE_PERF=1 to run perf tests",
)
def test_factory_throughput_floor() -> None:
    config = FactoryConfig(width=32, height=32, ticks_per_episode=10_000)
    world = FactoryWorld(config)
    world.reset(seed=0)

    start = time.perf_counter()
    world.run_ticks(2_000)
    elapsed = time.perf_counter() - start
    rate = 2_000 / elapsed

    print(
        f"factory ticks/s: {rate:.0f} "
        f"(machine={platform.machine()}, processor={platform.processor() or 'unknown'})"
    )
    assert rate >= 1_000.0, f"below supported floor: {rate:.0f} ticks/s"
