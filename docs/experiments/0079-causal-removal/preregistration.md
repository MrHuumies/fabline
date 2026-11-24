# Experiment 0079 — Counterfactual entity removal

- **Status:** preregistered (formal run pending)
- **Date:** 2026-11-24
- **Type:** P3 causal-intervention experiment
- **Task:** `factory.causal.remove.v1` (debug/P3, not in `factory-v0.1`)
- **Code:** `src/fabline/harness/causal_intervention.py`
- **CLI:** `python -m fabline causal-remove`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Do target-specific intervention features predict which same-type entity removal
hurts production more, beyond a type-only model?

## Pilot

40 episodes, seed 57,000, 120 rows, same-type pairs, 100-tick horizon:

| view | method | R² |
|---|---|---:|
| type_only | GBDT | 0.035 |
| type_only | linear | 0.005 |
| target | GBDT | **0.987** |
| target | linear | 0.380 |
| target | MLP | 0.429 |

The type-only view is near mean; target positions and buffers carry the signal.

## Design

- Three formal blocks: 58,000, 58,100, 58,200; 40 episodes each.
- Same-type pairs at ticks 150/250/350.
- 100-tick counterfactual horizon.
- Views: type-only vs target.
- Models: mean, linear, GBDT, MLP.

## Formal results

Target GBDT R²: `0.986, 0.753, 0.992` (mean 0.910).
Type-only GBDT R²: `-0.234, -0.594, -0.072` (mean −0.300).
Target linear mean R² 0.598; target MLP mean 0.157.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 target skill | target GBDT R² ≥ 0.30 | **pass**, 0.910 |
| H2 causal signal | target ≥ type-only + 0.20 | **pass**, +1.21 |
| H3 linear/MLP | report | pass, linear 0.598 |
| H4 frozen benchmark | unchanged | **pass** |

## Interpretation

- **The intervention target matters.** Same-type pairs remove the type shortcut;
  target position/buffer features explain most of the score difference.
- **The effect is model-dependent.** GBDT is strongest; linear/MLP are weaker
  but still above type-only.
- **The task is small.** 120 rows per block; treat as a debug causal benchmark.
- **It closes the causal intervention gap** at the task level, not a full causal
  discovery benchmark.

## Kill criteria

- Target GBDT under 0.30: no causal signal.
- Target not +0.20 over type-only: not promoted.
- No post-hoc target/horizon tuning.

## Transparency note

The pilot used 57,000. Formal blocks are fresh. The result is a task-level
counterfactual prediction, not a causal graph recovery claim.
