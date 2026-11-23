# Pilot 0059 — Spread-layout triage

- **Status:** pilot negative; not promoted
- **Date:** 2026-11-23
- **Type:** exploratory layout/triage pilot
- **Base tasks:** 0055 (twin-line triage) and 0052 (spread visibility)
- **Code:** exploratory CLI preset; not committed
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does moving the three-bridge survivor triage onto the distributed 48×24 layout
widen the oracle gap over scripted policies?

The twin-line triage (0055) has oracle 456 vs greedy 378 (+78). The spread
layout makes bridge distances nonlocal; the hope was a harder initial pair and
recovery order.

## Setup

- 48×24 spread layout (three lines), three positive bridges.
- Failure/recall 100; two survivor jobs.
- Success threshold 450.
- Baselines: noop, single EDF, nearest, greedy, recall-aware, no-replan, and an
  exhaustive two-job oracle.
- Seeds 17000–17002.

## Results

| policy | mean score | success |
|---|---:|---:|
| noop | 130.0 | 0.00 |
| single_edf | 130.0 | 0.00 |
| nearest | 473.3 | 0.33 |
| greedy | **600.0** | **0.67** |
| recall-aware | 463.3 | 0.33 |
| no-replan | 130.0 | 0.00 |
| oracle | **600.0** | **0.67** |

Oracle sequences: `[12,4,8]`, `[12,4,8]`, `[0,12,4]`. Greedy matches the oracle
on every seed (670/700/430).

## Why it is not promoted

- **The oracle gap is zero.** Greedy equals oracle, so the spread layout does
  not add a harder assignment/triage decision.
- **The layout makes the greedy priority better, not the task deeper.** With
  three distributed bridges and two repairs, outage-per-service-time is the
  right ranking on every pilot seed.
- **The task is a positive recovery demonstration but shallow.** It is not a
  better benchmark than 0055 and does not justify another task version.
- **The nearest/aware failures are not enough.** Their lower scores reflect
  weaker heuristics, not an oracle gap.

The exploratory `crew-triage-layouts` CLI was reverted.

## What it tells us

Spreading the layout does not automatically make triage harder. To create a
real trade-off, the values/deadlines must be asymmetric, or the survivor needs
a tighter budget, a third crew, or a partial view of the targets. The twin-line
0055 remains the positive triage task.

## Next

1. **Asymmetric triage:** vary bridge values, distances, and deadlines so the
   best order is not always highest-outage.
2. **Third crew/replacement:** test handoff and parallel recovery.
3. **Spread-layout triage with visibility:** combine 0052 with 0055; the
   survivor may not see the third bridge.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Twin-line triage: [`../0055-crew-triage/summary.md`](../0055-crew-triage/summary.md)
- Spread visibility: [`../0052-crew-visibility/summary.md`](../0052-crew-visibility/summary.md)
- Task card: [`../../tasks/crew-triage.md`](../../tasks/crew-triage.md)
- Exploratory CLI: not committed.
