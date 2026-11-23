# Experiment 0070 — Assembler recipe choice

- **Status:** complete (positive; all gates pass)
- **Date:** 2026-11-24
- **Type:** P3 queue/scheduling experiment
- **Mechanic:** fast/expensive vs slow/cheap assembler recipe (RFC 0026,
  ADR 0037)
- **Task:** `factory.production.recipe-choice.v1` (debug/P3, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/recipe.py`, `src/fabline/harness/recipe.py`
- **CLI:** `python -m fabline recipe-choice`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Queue-aware recipe selection beats fixed and myopic policies.** On fresh seeds
37,000–37,004, buffer-aware scores **318.0** against fast **278.0** (**+40**),
one-step lookahead **278.0** (**+40**), slow **230.0**, alternate **246.0**, and
random **290.0**. Buffer-aware succeeds on every seed; success threshold 300.
The one-step lookahead collapses to fast, so the gain is a queue/long-horizon
effect, not a myopic score chase. All gates pass.

## Results

| policy | mean score | 95% CI | success | gears | switches |
|---|---:|---:|---:|---:|---:|
| fast | 278.0 | [268.0, 286.0] | 0.00 | 27.8 | 0 |
| slow | 230.0 | [230.0, 230.0] | 0.00 | 23.0 | 1 |
| alternate | 246.0 | [242.0, 250.0] | 0.00 | 24.6 | 49 |
| **buffer-aware** | **318.0** | [312.0, 324.0] | **1.00** | **31.8** | 27.4 |
| buffer-aware4 | 314.0 | [306.0, 320.0] | 1.00 | 31.4 | 28.0 |
| random | 290.0 | [284.0, 296.0] | 0.20 | 29.0 | 24.8 |
| one-step lookahead | 278.0 | [268.0, 286.0] | 0.00 | 27.8 | 0 |

Per-seed buffer-aware: `320, 330, 320, 310, 310`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 queue gain | buffer-aware ≥ fast + 10 | **pass**, +40 |
| H2 planning | buffer-aware ≥ lookahead + 10 | **pass**, +40 |
| H3 success | buffer-aware success ≥ 0.60 | **pass**, 1.00 |
| H4 other baselines | ≥ slow/alternate/random + 10 | **pass**, +88/+72/+28 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Queue state is the decision variable.** Fast is best per tick, slow is best
  per ingot; buffer-aware switches on the ingot queue and wins.
- **Myopic lookahead is not enough.** The one-step greedy policy matches fast
  exactly; the value comes from holding the queue in a productive range.
- **The initial buffer creates real episode variation.** Seeded 0–6 ingot
  starts make fixed policies score 260–290 and buffer-aware 310–330.
- **The task is deterministic otherwise.** The only variation is the initial
  buffer; the production line and recipe costs are fixed.
- **No new item or byproduct is needed for a useful scheduling task.**

## Caveats

- One assembler, one item, one line; no power or faults.
- The one-step lookahead is not a full oracle; no long-horizon optimal policy is
  computed.
- Recipe costs are fixed at 2/12 and 1/20; not tuned after the formal block.
- The initial buffer is the only per-seed variation.
- Not part of frozen `factory-v0.1`.

## Next

1. **Byproducts/queues:** add a second output or a purge/queue action only if it
   creates a new decision beyond the recipe switch.
2. **Power/fault interaction:** test recipe choice under power constraints or
   machine faults; this reuses opt-in mechanics.
3. Keep the frozen benchmark unchanged.

## Artifacts

- Mechanic: RFC 0026, ADR 0037
- Env: `src/fabline/env/recipe.py`
- Harness: `src/fabline/harness/recipe.py`
- CLI: `python -m fabline recipe-choice`
- Task card: [`../../tasks/recipe-choice.md`](../../tasks/recipe-choice.md)
- Raw results: `results/recipe-choice/` (ignored)
