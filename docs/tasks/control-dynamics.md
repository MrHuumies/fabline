# Task card — action-conditioned control dynamics

- **Task ID:** `factory.control_dynamics.predict.v1`
- **Version:** 0.1.0
- **Status:** benchmark candidate (`factory-v0.1`)
- **World:** factory-0.1.0
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Predict the next control observation after an action. Unlike passive
next-state prediction, the input includes the action, so the model must learn
action consequences rather than continuity.

## Contract

- **Observation:** control vector (49 features) plus a one-hot macro action
  (6), for 55 input features.
- **Actions:** `noop`, `build_miner`, `build_belt`, `build_furnace`,
  `build_assembler`, `remove`.
- **Data generation:** 30 episodes of random legal actions in the line-building
  environment; one transition per decision step.
- **Target:** the next 49-feature control observation.
- **Splits:** by episode seed, 70/20/10.
- **Metrics:** MSE, MAE, mean cosine with 95% bootstrap confidence intervals.
- **Baselines:** copy (current observation), linear, MLP.

## Results — `factory-v0.1`

Test:

| method | MSE | cosine |
|---|---:|---:|
| copy | 0.0140 | 0.9363 |
| linear | **0.0085** | **0.9609** |
| MLP | 0.0176 | 0.9250 |

## Known pitfalls

- **Random actions, not an expert distribution.** The model sees many wrong
  builds and removes; it is not a policy dataset.
- **Short horizon.** One decision step (10 ticks); long-horizon dynamics is
  future work.
- **Small data.** About 900 transitions; CIs are wide.
- **Fixed environment.** One path, one world size, no faults or power.
- **A good next-state model is not a planner.** Planning and rollback are
  separate tests.

## Negative controls

- Copy ignores the action; a model that cannot beat copy is not using action
  information.
- Linear beats copy on MSE and cosine; the gap is the action-conditioning
  signal.

## Changelog

- 2026-11-21 — card created; M3 results added.
