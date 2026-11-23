# Experiment 0072 — Byproduct queue on recipe choice

- **Status:** complete (positive; all gates pass)
- **Date:** 2026-11-24
- **Type:** P3 queue/scheduling experiment
- **Mechanic:** recipe choice plus a blocking byproduct queue (RFC 0027,
  ADR 0039)
- **Task:** `factory.production.recipe-choice.v1`, byproduct capacity 2
- **Code:** `src/fabline/env/recipe.py`, `src/fabline/harness/recipe.py`
- **CLI:** `python -m fabline recipe-choice --byproduct --byproduct-capacity 2`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The byproduct queue creates a new decision.** On fresh seeds 41,000–41,004,
purge-aware scores **302.0** against fast **274.0** (**+28**) and buffer-aware
without purge **274.0** (**+28**). Slow collapses to **20.0** because it blocks
at capacity; slow-plus-purge is **200.0**; random is **276.0**; one-step
lookahead is **274.0**. The purge action is the active ingredient, not just the
slow recipe. Purge-aware succeeds on every seed at threshold 300.

## Results

| policy | mean score | 95% CI | success | gears |
|---|---:|---:|---:|---:|
| fast | 274.0 | [270.0, 282.0] | 0.00 | 27.4 |
| slow | 20.0 | [20.0, 20.0] | 0.00 | 2.0 |
| slow + purge | 200.0 | [200.0, 200.0] | 0.00 | 20.0 |
| buffer-aware (no purge) | 274.0 | [270.0, 282.0] | 0.00 | 27.4 |
| **purge-aware** | **302.0** | [300.0, 306.0] | **1.00** | **30.2** |
| random | 276.0 | [258.0, 294.0] | 0.20 | 27.6 |
| one-step lookahead | 274.0 | [270.0, 282.0] | 0.00 | 27.4 |

Per-seed purge-aware: `310, 300, 300, 300, 300`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 purge gain | purge-aware ≥ fast + 10 | **pass**, +28 |
| H2 queue action | purge-aware ≥ buffer-aware + 10 | **pass**, +28 |
| H3 success | purge-aware success ≥ 0.60 | **pass**, 1.00 |
| H4 not just slow | purge-aware ≥ slow+purge + 10 | **pass**, +102 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **The purge action is the decision.** Buffer-aware without purge matches fast;
  adding purge when the queue is full gains +28.
- **Slow alone is a trap.** It blocks at capacity and scores 20; slow with purge
  is still worse than fast.
- **The queue state is visible and actionable.** The policy needs both the
  input queue and the byproduct queue.
- **The byproduct is a clean blocking constraint.** No new item, no logistics,
  and default hashes are unchanged.
- **The recipe line now has two positive results.** Recipe choice (0070) and
  byproduct purge (0072); power is a robustness condition (0071).

## Caveats

- One assembler, one item, one byproduct; no power.
- Byproduct capacity 2; not tuned after the formal block.
- The one-step lookahead is myopic; no long-horizon oracle.
- Scores are nearly deterministic across seeds; the initial buffer is the main
  variation.
- Not part of frozen `factory-v0.1`.

## Next

1. **Byproduct under power or faults:** test whether the purge policy survives a
   tighter budget or machine faults; likely a robustness result, not a new
   decision.
2. **Deadlines/contracts:** a new P3 axis with multi-objective trade-offs.
3. **Stop the recipe line:** it now has a positive recipe result and a positive
   queue result; more variants risk saturation.

## Artifacts

- Mechanic: RFC 0027, ADR 0039
- Env: `src/fabline/env/recipe.py`
- Harness: `src/fabline/harness/recipe.py`
- CLI: `python -m fabline recipe-choice --byproduct`
- Task card: [`../../tasks/recipe-choice.md`](../../tasks/recipe-choice.md)
- Raw results: `results/recipe-byproduct/` (ignored)
