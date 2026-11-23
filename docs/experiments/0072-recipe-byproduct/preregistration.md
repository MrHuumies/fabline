# Experiment 0072 — Byproduct queue on recipe choice

- **Status:** preregistered (formal run pending)
- **Date:** 2026-11-24
- **Type:** P3 queue/scheduling experiment
- **Mechanic:** recipe choice plus a blocking byproduct queue (RFC 0027,
  ADR 0039)
- **Task:** `factory.production.recipe-choice.v1`, byproduct capacity 2
- **Code:** `src/fabline/env/recipe.py`, `src/fabline/harness/recipe.py`
- **CLI:** `python -m fabline recipe-choice --byproduct --byproduct-capacity 2`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a blocking byproduct queue create a new decision beyond the fast/slow
recipe choice?

## Pilot

Seeds 40,000–40,004, success 300:

| policy | mean score |
|---|---:|
| fast | 278 |
| buffer-aware (no purge) | 278 |
| slow | 20 |
| slow + purge | 200 |
| random | 280 |
| one-step lookahead | 278 |
| **purge-aware** | **304** |

The purge action adds +26 over fast and buffer-aware. Slow without purge
collapses; slow with purge is still worse than fast.

## Design

- Five fresh seeds: 41,000–41,004.
- 16×8 gear scenario, 500 ticks, decision interval 10.
- Fast: 2 ingots/12 ticks, no byproduct.
- Slow: 1 ingot/20 ticks, 1 byproduct.
- Byproduct capacity 2; at capacity slow crafts block.
- Action 2 purges the queue.
- Initial ingot buffer seeded 0–6.
- No power.
- Success ≥ 300.

## Baselines

| Baseline | Rule |
|---|---|
| fast | always fast |
| slow | always slow (blocks) |
| slow_purge | slow, purge at capacity |
| buffer_aware | fast if input ≥ 2 else slow, no purge |
| purge_aware | buffer-aware plus purge at capacity |
| random | uniform legal action |
| lookahead | one-step greedy over three actions |

## Gates

| Gate | Threshold |
|---|---|
| H1 purge gain | purge-aware ≥ fast + 10 |
| H2 queue action | purge-aware ≥ buffer-aware + 10 |
| H3 success | purge-aware success ≥ 0.60 |
| H4 not just slow | purge-aware ≥ slow_purge + 10 |
| H5 frozen benchmark | unchanged |

## Predictions

- Purge-aware 300–315; fast/buffer-aware 270–285; slow 20; slow_purge 200.
- H1/H2/H3/H4 pass; success 1.00.
- If H2 fails, the purge action adds nothing beyond recipe choice; retire it.

## Kill criteria

- H1 or H2 under +10: negative.
- Success under 0.60: unreliable.
- No post-hoc capacity or threshold tuning.

## Transparency note

The pilot used seeds 40,000–40,004. The formal block is fresh
41,000–41,004. The pilot's +26 is not a confirmation.
