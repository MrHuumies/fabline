# Task card — assembler recipe choice

- **Task ID:** `factory.production.recipe-choice.v1`
- **Version:** 0.1.0
- **Status:** P3 debug task; formal positive; power robustness tested; not in
  `factory-v0.1`
- **World:** factory-0.1.0 with opt-in recipe switch
- **Owner:** FABLINE
- **Date:** 2026-11-24

## Phenomenon

The assembler can run a fast recipe (2 ingots, 12 ticks) or a slow recipe
(1 ingot, 20 ticks). Both make gears. The depots score gears equally. The best
recipe depends on the ingot queue: slow is cheaper per gear, fast is faster per
tick. A seeded initial ingot buffer varies the trade-off per episode.

## Contract

- **Observation:** 22 features — 18 vector features, recipe one-hot, normalized
  assembler input/output totals.
- **Actions:** 0 fast, 1 slow.
- **Layout:** 16×8 gear scenario, one starter line, no power/faults.
- **Timing:** 500 ticks, decision interval 10.
- **Initial buffer:** seeded 0–6 ingots in the assembler input.
- **Reward:** final production score; success ≥ 300.

## Metrics

- mean score and success;
- gears delivered;
- recipe switches;
- scripted gap over fast.

## Baselines

| Baseline | Rule |
|---|---|
| fast | always fast |
| slow | always slow |
| alternate | switch every decision |
| buffer_aware | fast if assembler input ≥ 2, else slow |
| buffer_aware4 | fast if assembler input ≥ 4, else slow |
| random | uniform legal action |
| lookahead | one-step greedy over the next interval |

## Gates

| Gate | Threshold |
|---|---|
| H1 queue gain | buffer-aware ≥ fast + 10 |
| H2 planning | buffer-aware ≥ one-step lookahead + 10 |
| H3 success | buffer-aware success ≥ 0.60 |
| H4 other baselines | buffer-aware ≥ slow/alternate/random + 10 |
| H5 frozen benchmark | unchanged |

## Known pitfalls

- The one-step lookahead is myopic; it is not a full oracle.
- Only one assembler and one item; no byproducts yet.
- The initial buffer is the only per-seed variation.
- Not part of `factory-v0.1`.

## Results (0070)

Seeds 37,000–37,004.

| policy | mean score | success |
|---|---:|---:|
| fast | 278.0 | 0.00 |
| slow | 230.0 | 0.00 |
| alternate | 246.0 | 0.00 |
| **buffer-aware** | **318.0** | **1.00** |
| buffer-aware4 | 314.0 | 1.00 |
| random | 290.0 | 0.20 |
| one-step lookahead | 278.0 | 0.00 |

All gates pass: queue gain +40, planning +40, success 1.00. See
[`experiments/0070-recipe-choice`](../experiments/0070-recipe-choice/summary.md).

## Power condition (0071)

Capacity 10, radius topology, five fresh seeds 39,000–39,004. Buffer-aware
scores 314 vs fast 272 (+42); power-saver ties buffer-aware at 314;
headroom-gated power policy is worse at 194. The queue policy is robust, but
power state adds no new decision. See
[`experiments/0071-recipe-power`](../experiments/0071-recipe-power/summary.md).

## Changelog

- 2026-11-24 — task card created; recipe costs and gates defined.
- 2026-11-24 — formal run positive; buffer-aware 318 vs fast 278.
- 2026-11-24 — power condition robust; power-saver ties buffer-aware, headroom
  gating worse.
