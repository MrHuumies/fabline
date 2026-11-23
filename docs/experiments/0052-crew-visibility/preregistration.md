# Experiment 0052 — Distributed-layout visibility and reports

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-23
- **Type:** P2 multi-agent information experiment
- **Mechanic:** per-crew visibility plus shared report age on the spread layout
  (RFC 0015, ADR 0026)
- **Task:** `factory.power.crew-visibility.v1` (debug/P2, not in
  `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does the distributed layout create a useful local-view task, and does a delayed
shared report recover the global/local gap?

The twin-line layout was negative (0051): radius 8 hid the bridges, 12–16 was a
flat plateau, and 20 was global. On a 48×24 three-line spread layout, the pilot
found a useful block at radius 16: local nearest 683 vs global 757, and a
60-tick report recovered 767. Age 30 did not.

## Environment

- 48×24 map, three gear lines spread across independent x bands and rows.
- One generator, capacity 48; per-crew Manhattan radius 16.
- Random crew-B base at least eight cells from A.
- Warnings 40; failures 90 (loop), 110 (small), 130 (large); recall 100.
- Actions are the existing pair actions; the mask excludes targets a crew
  neither sees nor has a report for.
- Shared report memory: age 0 (local), 30, or 60 ticks.
- Success ≥ 600.

## Data and seeds

- Pilot: seeds 0–2; local/global/delayed conditions.
- Formal: seeds 10000–10004 (5 contiguous, all valid by reset-only check).
- No Q training; scripted and oracle baselines.
- No dataset artifact.

## Conditions

| Condition | Visibility | Report age |
|---|---|---:|
| global | ∞ | — |
| local | 16 | 0 |
| delayed30 | 16 | 30 |
| delayed60 | 16 | 60 |

## Baselines

| Baseline | Rule |
|---|---|
| nearest | nearest known target per crew |
| greedy | outage per service time among known targets |
| recall-aware | earliest known bridge for A; other for B |
| oracle | best pair under the same visibility mask |
| single/noop | context |

## Gates

| Gate | Threshold |
|---|---|
| H1 local cost | global oracle ≥ local oracle + 10 |
| H2 communication gain | delayed60 oracle ≥ local + 10 |
| H3 report-age sensitivity | delayed60 oracle > delayed30 oracle |
| H4 delayed success | delayed60 oracle success ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Predictions

- Global oracle about 760; local oracle about 690.
- Delayed30 is close to local; delayed60 recovers most or all of the gap.
- Nearest/greedy show the same pattern; recall-aware is weaker.
- Report age is the active variable, not the radius alone.

## Kill criteria

- Local and global are identical (no information cost).
- Delayed60 does not beat delayed30.
- The task requires post-hoc changes to radius, ages, or gates.

## Analysis plan

- Report mean score, CI, success, and per-seed scores for every condition and
  baseline.
- Report oracle pair choices.
- Keep the layout, radius, report ages, and success threshold fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0015, ADR 0026
- Env: `src/fabline/env/crew_visibility.py`
- Harness: `src/fabline/harness/crew_visibility.py`
- CLI: `python -m fabline crew-visibility`
- Task card: `docs/tasks/crew-visibility.md`
- Raw results: `results/crew-visibility/` (ignored)
- Summary: `docs/experiments/0052-crew-visibility/summary.md`
- Prior: [`../0051-visibility-pilot/summary.md`](../0051-visibility-pilot/summary.md)
