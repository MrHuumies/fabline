# mypy: ignore-errors
"""Interactive viewer, replay player, and playable control client."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import pygame

from fabline.env.control import ControlConfig, ControlEnv, MacroAction
from fabline.harness.human_demos import make_scripted_demos
from fabline.record.human import HumanDemo, write_human_demos
from fabline.render.factory_view import FactoryView
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.world import FactoryWorld

ACTION_KEYS = {
    pygame.K_0: int(MacroAction.NOOP),
    pygame.K_1: int(MacroAction.BUILD_MINER),
    pygame.K_2: int(MacroAction.BUILD_BELT),
    pygame.K_3: int(MacroAction.BUILD_FURNACE),
    pygame.K_4: int(MacroAction.BUILD_ASSEMBLER),
    pygame.K_5: int(MacroAction.REMOVE),
}
ACTION_NAMES = {
    int(action): action.name.lower()
    for action in MacroAction
}


def _init_pygame(screenshot: str | None) -> None:
    if screenshot:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.font.init()


def run_factory_viewer(
    config: FactoryConfig,
    *,
    seed: int = 0,
    ticks_per_second: float = 20.0,
    screenshot: str | None = None,
    screenshot_ticks: int = 200,
    max_ticks: int | None = None,
    faults: FaultConfig | None = None,
    power: PowerConfig | None = None,
) -> None:
    """Watch a live factory. With ``screenshot``, render one frame headlessly."""

    _init_pygame(screenshot)
    fault_config = faults or FaultConfig()
    power_config = power or PowerConfig()
    world = FactoryWorld(config, fault_config, power_config)
    world.reset(seed)
    view = FactoryView(config, faults=fault_config, power=power_config)

    if screenshot:
        world.run_ticks(min(screenshot_ticks, max_ticks or config.ticks_per_episode))
        surface = view.render(
            world.state,
            {"mode": "factory", "seed": seed, "paused": False},
        )
        path = Path(screenshot)
        path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(surface, str(path))
        print(f"saved {path}")
        pygame.quit()
        return

    screen = pygame.display.set_mode((view.width, view.height))
    pygame.display.set_caption("FABLINE — factory")
    clock = pygame.time.Clock()
    paused = False
    speed = ticks_per_second
    accumulator = 0.0
    done = False
    limit = max_ticks or config.ticks_per_episode

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_n and not done:
                    world.tick()
                elif event.key == pygame.K_r:
                    world.reset(seed)
                    accumulator = 0.0
                    done = False
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    speed = min(240.0, speed * 1.5)
                elif event.key == pygame.K_MINUS:
                    speed = max(1.0, speed / 1.5)

        if not paused and not done:
            accumulator += dt * speed
            while accumulator >= 1.0 and not done:
                world.tick()
                accumulator -= 1.0
                if world.state.tick >= limit:
                    done = True

        info = {
            "mode": "factory",
            "seed": seed,
            "paused": paused,
            "speed": speed,
            "message": "episode complete — R to reset" if done else "",
        }
        screen.blit(view.render(world.state, info), (0, 0))
        pygame.display.flip()

    pygame.quit()


def run_replay_viewer(
    config: FactoryConfig | None,
    dataset_dir: str | Path,
    episode_id: str,
    *,
    ticks_per_second: float = 20.0,
) -> None:
    """Watch a passive shared episode from a dataset directory."""

    dataset_path = Path(dataset_dir)
    episode_dir = dataset_path / "episodes" / episode_id
    meta = json.loads((episode_dir / "meta.json").read_text(encoding="utf-8"))
    replay = json.loads((episode_dir / "replay.json").read_text(encoding="utf-8"))
    if config is None:
        manifest = json.loads(
            (dataset_path / "manifest.json").read_text(encoding="utf-8")
        )
        raw = manifest.get("factory_config") or {}
        config = (
            FactoryConfig.from_dict(raw)
            if raw
            else FactoryConfig(
                width=16,
                height=8,
                ticks_per_episode=500,
                rock_density=0.02,
                ore_patches=2,
            )
        )
    scenario = SCENARIOS.get(replay.get("scenario", ""))
    fault_data = replay.get("faults")
    faults = FaultConfig.from_dict(fault_data) if fault_data else FaultConfig()
    power_data = replay.get("power")
    power = PowerConfig.from_dict(power_data) if power_data else PowerConfig()
    _init_pygame(None)
    world = FactoryWorld(config, faults, power)
    world.reset(int(replay["seed"]), scenario)
    view = FactoryView(config, faults=faults, power=power)
    screen = pygame.display.set_mode((view.width, view.height))
    pygame.display.set_caption(f"FABLINE — replay {episode_id}")
    clock = pygame.time.Clock()
    paused = False
    speed = ticks_per_second
    accumulator = 0.0
    limit = int(meta.get("episode_ticks", config.ticks_per_episode))
    done = False

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_n and not done:
                    world.tick()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    speed = min(240.0, speed * 1.5)
                elif event.key == pygame.K_MINUS:
                    speed = max(1.0, speed / 1.5)

        if not paused and not done:
            accumulator += dt * speed
            while accumulator >= 1.0 and not done:
                world.tick()
                accumulator -= 1.0
                if world.state.tick >= limit:
                    done = True

        info = {
            "mode": "replay",
            "seed": replay["seed"],
            "paused": paused,
            "speed": speed,
            "message": "replay complete" if done else f"episode {episode_id}",
        }
        screen.blit(view.render(world.state, info), (0, 0))
        pygame.display.flip()

    pygame.quit()


def run_control_play(
    config: FactoryConfig,
    control: ControlConfig,
    out_dir: str | Path,
    *,
    seed: int = 0,
) -> None:
    """Play the six-tile construction task and save human demos."""

    _init_pygame(None)
    env = ControlEnv(config, control)
    view = FactoryView(config)
    screen = pygame.display.set_mode((view.width, view.height))
    pygame.display.set_caption("FABLINE — build the line")
    clock = pygame.time.Clock()

    current_seed = seed
    observation, info = env.reset(current_seed)
    observations: list[np.ndarray] = []
    actions: list[int] = []
    rewards: list[float] = []
    hashes: list[str] = []
    last_action: str | None = None
    last_reward: float | None = None
    message = "Build a working line. 0 noop, 1 miner, 2 belt, 3 furnace, 4 assembler, 5 remove."
    done = False

    running = True
    while running:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    observation, info = env.reset(current_seed)
                    observations.clear()
                    actions.clear()
                    rewards.clear()
                    hashes.clear()
                    last_action = None
                    last_reward = None
                    done = False
                    message = "reset"
                elif event.key == pygame.K_s:
                    if not actions:
                        message = "nothing to save yet"
                    else:
                        demo = HumanDemo(
                            demo_id=f"human_{current_seed:04d}_{int(time.time())}",
                            seed=current_seed,
                            observations=np.stack(observations),
                            actions=np.asarray(actions, dtype=np.int64),
                            rewards=np.asarray(rewards, dtype=np.float32),
                            state_hashes=hashes,
                            final_score=int(info["score"]),
                            success=bool(info["success"]),
                            source="human",
                            meta={"episode_steps": len(actions)},
                        )
                        write_human_demos(
                            out_dir,
                            "human-control",
                            [demo],
                            config,
                            control,
                        )
                        current_seed += 1
                        observation, info = env.reset(current_seed)
                        observations.clear()
                        actions.clear()
                        rewards.clear()
                        hashes.clear()
                        last_action = None
                        last_reward = None
                        done = False
                        message = f"saved — new episode seed {current_seed}"
                elif event.key in ACTION_KEYS and not done:
                    action = ACTION_KEYS[event.key]
                    observations.append(observation)
                    actions.append(action)
                    last_action = ACTION_NAMES[action]
                    observation, reward, terminated, truncated, info = env.step(action)
                    rewards.append(reward)
                    hashes.append(env.world.state_hash())
                    last_reward = reward
                    done = terminated or truncated
                    if done:
                        message = "episode complete — S save, R retry, Esc quit"

        view_info = {
            **info,
            "mode": "control",
            "path": env.path,
            "path_index": info["path_index"],
            "last_action": last_action,
            "reward": last_reward,
            "message": message,
            "paused": False,
        }
        screen.blit(view.render(env.world.state, view_info), (0, 0))
        pygame.display.flip()

    pygame.quit()


def run_scripted_demo(
    config: FactoryConfig,
    control: ControlConfig,
    out_dir: str | Path,
    *,
    episodes: int = 10,
    seed: int = 0,
) -> dict[str, Any]:
    demos = make_scripted_demos(config, control, episodes=episodes, seed=seed)
    manifest = write_human_demos(out_dir, "scripted-control", demos, config, control)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest
