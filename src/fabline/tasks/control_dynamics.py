"""Action-conditioned dynamics from the line-building control environment."""

from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np

from fabline.env.control import ControlConfig, ControlEnv, MacroAction
from fabline.worlds.factory.config import FactoryConfig

from .splits import assign_split


@dataclass
class ControlTransitionDataset:
    X: np.ndarray
    y: np.ndarray
    splits: np.ndarray
    action_names: tuple[str, ...]
    episodes: int


def generate_control_transitions(
    config: FactoryConfig,
    control: ControlConfig,
    *,
    episodes: int = 30,
    seed: int = 0,
) -> ControlTransitionDataset:
    """Collect ``(observation, action) -> next observation`` transitions."""

    env = ControlEnv(config, control)
    rng = random.Random(seed)
    action_names = tuple(action.name.lower() for action in MacroAction)
    X: list[np.ndarray] = []
    y: list[np.ndarray] = []
    splits: list[str] = []

    for episode in range(episodes):
        observation, _ = env.reset(seed=seed + episode)
        done = False
        while not done:
            mask = env.action_mask()
            legal = np.flatnonzero(mask)
            action = int(rng.choice(legal.tolist()))
            one_hot = np.zeros(env.n_actions, dtype=np.float32)
            one_hot[action] = 1.0
            next_observation, _, terminated, truncated, _ = env.step(action)
            X.append(np.concatenate([observation, one_hot]))
            y.append(next_observation)
            splits.append(assign_split(seed + episode))
            observation = next_observation
            done = terminated or truncated

    return ControlTransitionDataset(
        X=np.stack(X),
        y=np.stack(y),
        splits=np.asarray(splits),
        action_names=action_names,
        episodes=episodes,
    )
