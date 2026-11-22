# Pilot 0039 — Contextual maintenance thresholds

- **Status:** pilot negative; not promoted
- **Date:** 2026-11-22
- **Type:** exploratory pilot; follow-up to
  [`0038`](../0038-preventive-threshold/summary.md)
- **Mechanic:** machine-wear maintenance (RFC 0009, ADR 0019)
- **Code:** `experiments/preventive_fault/context_pilot.py`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a maintenance context shift the optimal threshold enough to justify a
contextual policy-selection task?

Experiment 0038 showed a fixed threshold bandit is learnable. The natural next
step is a context — fault repair time and maintenance downtime — so the optimal
wear threshold depends on the episode.

## Setup

- Threshold arms: 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0.
- Contexts: `(repair ticks, maintenance ticks)`:
  - (90, 5), (20, 80), (60, 10), (30, 20), (90, 40), (20, 5).
- One threshold per episode; scripted policy applies it.
- Deterministic gear line; one seed per context for the pilot.

## Results

| repair | maintenance | scores by threshold | best |
|---:|---:|---|---:|
| 90 | 5 | 240, 250, 250, 250, 250, 250, 260, 200 | 0.9 |
| 20 | 80 | 120, 130, 150, 170, 170, 170, 170, 200 | 1.0 |
| 60 | 10 | 220, 230, 240, 240, 250, 250, 250, 200 | 0.7 |
| 30 | 20 | 200, 200, 220, 230, 230, 230, 240, 230 | 0.9 |
| 90 | 40 | 150, 170, 200, 200, 210, 220, 220, 190 | 0.8 |
| 20 | 5 | 240, 250, 250, 250, 250, 250, 260, 240 | 0.9 |

The best fixed threshold is 0.9:

- mean score 233.3 across contexts;
- context oracle mean 238.3;
- contextual gain **+5.0**.

## Why it is not promoted

- **The 0.8–0.9 plateau is robust.** Most contexts score 250 at 0.7–0.9; only
  the extreme long-maintenance context prefers 1.0.
- **The contextual gain is tiny.** +5 points over the best fixed arm is within
  the task's noise and not a meaningful gate.
- **The score ceiling compresses the trade.** Early maintenance often ties at
  250–260; the cost differences do not separate arms enough.
- **A contextual task needs a sharper trade** — per-entity scheduling with one
  crew, travel time, or explicit maintenance cost.

Do not add this as a benchmark.

## Next

- **Per-entity maintenance scheduling:** several worn machines, one crew, and a
  choice of which to service.
- **Crew travel:** spatial downtime that makes the context actionable.
- **Noisy wear sensors:** prediction quality for normal maintenance.
- Keep `factory-v0.1` frozen.

## Artifacts

- Code: `experiments/preventive_fault/context_pilot.py`
- Raw output: not committed
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
