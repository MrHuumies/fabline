# Experiment 0071 — Recipe choice under power constraints

- **Status:** complete (robustness positive; power interaction negative)
- **Date:** 2026-11-24
- **Type:** P3 robustness experiment
- **Mechanic:** recipe choice (RFC 0026 / ADR 0037) under a tight opt-in power
  budget (ADR 0038)
- **Task:** `factory.production.recipe-choice.v1`, power capacity 10
- **Code:** `src/fabline/env/recipe.py`, `src/fabline/harness/recipe.py`
- **CLI:** `python -m fabline recipe-choice --power-capacity 10`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The queue policy is robust to a tight power budget, but power state adds no
new decision.** On fresh seeds 39,000–39,004 at capacity 10, buffer-aware scores
**314.0** against fast **272.0** (**+42**), slow **180.0**, random **208.0**, and
one-step lookahead **272.0**. A brownout-aware policy ties buffer-aware at
**314.0**; a headroom-gated power policy is worse at **194.0**. The power budget
punishes slow and random production but leaves the best queue policy unchanged.
H2 is a negative-interaction gate: power does not add a decision beyond the
ingot queue.

## Results

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| fast | 272.0 | [262.0, 282.0] | 0.00 |
| slow | 180.0 | [180.0, 180.0] | 0.00 |
| alternate | 182.0 | [180.0, 186.0] | 0.00 |
| **buffer-aware** | **314.0** | [310.0, 318.0] | **1.00** |
| buffer-aware4 | 310.0 | [302.0, 318.0] | 1.00 |
| power-aware (headroom) | 194.0 | [190.0, 198.0] | 0.00 |
| power-saver (brownout) | 314.0 | [310.0, 318.0] | 1.00 |
| random | 208.0 | [184.0, 235.0] | 0.00 |
| one-step lookahead | 272.0 | [262.0, 282.0] | 0.00 |

Per-seed buffer-aware: `310, 310, 320, 320, 310`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 queue gain | buffer-aware ≥ fast + 10 | **pass**, +42 |
| H2 power decision | power-saver ≤ buffer-aware + 5 | **pass**, tie (no new decision) |
| H3 success | buffer-aware success ≥ 0.60 | **pass**, 1.00 |
| H4 other baselines | ≥ slow/random + 10 | **pass**, +134/+106 |
| H5 robustness | gain within 10 of 0070's +40 | **pass**, +42 |
| H6 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Queue state dominates.** The same buffer-aware policy wins with and without
  power: +42 here, +40 in 0070.
- **Power is a constraint, not a new decision.** Headroom gating is harmful;
  brownout-aware gating only ties the queue policy.
- **The tight budget removes low-value policies.** Slow and random collapse,
  but the best policy is unchanged.
- **No new mechanic is needed for power robustness.** The recipe task is stable
  under an existing opt-in mechanic.
- **The next P3 decision needs a new output/queue structure.** Byproducts or a
  purge/queue action are the candidates.

## Caveats

- One generator, radius topology, capacity 10; other capacities were not part of
  the formal block.
- No faults, only power.
- The brownout-aware policy uses the current brownout ratio; a predictive policy
  was not tested.
- Not part of frozen `factory-v0.1`.

## Next

1. **Byproduct queue:** add a second output or a purge action and test whether
   it creates a new decision beyond recipe choice.
2. **Fault interaction:** test recipe choice under machine faults; larger
   interaction than power.
3. Keep the frozen benchmark unchanged.

## Artifacts

- Mechanic: RFC 0026, ADR 0037, ADR 0038
- Env: `src/fabline/env/recipe.py`
- Harness: `src/fabline/harness/recipe.py`
- CLI: `python -m fabline recipe-choice --power-capacity 10`
- Task card: [`../../tasks/recipe-choice.md`](../../tasks/recipe-choice.md)
- Raw results: `results/recipe-power/` (ignored)
