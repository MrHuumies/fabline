# Experiment 0070 — Assembler recipe choice

- **Status:** preregistered (formal run pending)
- **Date:** 2026-11-24
- **Type:** P3 queue/scheduling experiment
- **Mechanic:** fast/expensive vs slow/cheap assembler recipe (RFC 0026,
  ADR 0037)
- **Task:** `factory.production.recipe-choice.v1` (debug/P3, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/recipe.py`, `src/fabline/harness/recipe.py`
- **CLI:** `python -m fabline recipe-choice`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does queue-aware recipe selection beat fixed and myopic policies on a
long-horizon production task?

## Pilot

Seeds 36,000–36,004, initial ingot buffer seeded 0–6:

| policy | mean score |
|---|---:|
| fast | 278 |
| slow | 230 |
| alternate | 248 |
| random | 284 |
| one-step lookahead | 278 |
| **buffer-aware** | **320** |

The myopic lookahead matches fast; buffer-aware gains +42. The pilot is
promising but uses the same seeds that motivated the task.

## Environment

- 16×8 gear scenario, one starter line.
- Fast: 2 ingots, 12 ticks. Slow: 1 ingot, 20 ticks.
- Initial assembler input: seeded 0–6 ingots.
- 500 ticks, decision interval 10.
- Reward: final production score; success ≥ 300.
- No power or faults.

## Data and seeds

- Pilot: 36,000–36,004.
- Formal: 37,000–37,004 (5 fresh seeds).
- No training; scripted baselines only.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| fast | always fast |
| slow | always slow |
| alternate | switch every decision |
| buffer_aware | fast if input ≥ 2, else slow |
| buffer_aware4 | fast if input ≥ 4, else slow |
| random | uniform |
| lookahead | one-step greedy |

## Gates

| Gate | Threshold |
|---|---|
| H1 queue gain | buffer-aware ≥ fast + 10 |
| H2 planning | buffer-aware ≥ lookahead + 10 |
| H3 success | buffer-aware success ≥ 0.60 at 300 |
| H4 other baselines | buffer-aware ≥ slow/alternate/random + 10 |
| H5 frozen benchmark | unchanged |

## Predictions

- Buffer-aware 310–330; fast 270–290; lookahead 270–290; slow 230; random
  270–290.
- H1 and H2 pass; success 1.00.
- If H1 or H2 fails, the queue decision is not robust; retire the axis.

## Analysis plan

- Report all baselines with score/CI/success/gears/switches.
- Report per-seed scores.
- Do not tune the recipe cost or threshold after the formal block.
- Keep `factory-v0.1` frozen.

## Kill criteria

- Queue gain under +10: negative.
- Buffer-aware not +10 over lookahead: the gain is not a planning/queue effect.
- Success under 0.60: task not reliable.
- No post-hoc cost tuning.

## Transparency note

The pilot used seeds 36,000–36,004. The formal block is fresh
37,000–37,004. The pilot's +42 is not a confirmation.
