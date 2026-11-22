# Experiment 0040 — Crew scheduling with travel time

- **Status:** preregistered; implementation pending
- **Date:** 2026-11-22
- **Type:** P1 phase 1D spatial-scheduling experiment
- **Mechanic:** one repair crew, travel + service time (RFC 0010, ADR 0020)
- **Task:** `factory.power.crew-schedule.v1` (debug/P1, not in `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does travel time make per-entity repair scheduling a real decision, or is
impact-only already sufficient?

The 0.1.2 coverage review found that impact-only and threshold policies are
close to optimal. This task adds a crew position and travel time; the agent
chooses which of three wires (loop, small bridge, large bridge) to service under
a two-job budget.

## Environment

- Gear line, wired power, one generator, capacity 12.
- Target roles: zero-impact loop, small bridge, large bridge.
- Warnings at tick 40; failures at 220 (loop), 280 (small), 340 (large).
- Service time: 2 × Manhattan travel from the crew to the nearest endpoint,
  plus 40 repair ticks.
- Crew starts at the depot.
- Budget: 2 jobs; 3 targets.
- A preventive job that completes before failure cancels it; a job that hits
  failure aborts and spends the budget.
- Reward: time-weighted prevented/restored outage.
- Outcome: final production score; success threshold to be set in the pilot.

## Baselines

| Baseline | Rule |
|---|---|
| noop | never service |
| impact_only | service the largest positive outage |
| nearest | service the nearest positive outage |
| travel_aware | maximize outage per service tick |
| oracle | best two-wire order by simulation |
| random | uniform legal action |
| tabular Q | spatial/role state; train on fresh seeds |

## Data and seeds

- Pilot: seeds 0–9 (design).
- Formal: seeds 800–804.
- Q training: seeds 10000+ (disjoint).
- No dataset artifact.

## Gates

| Gate | Threshold |
|---|---|
| H1 travel gain | best travel-aware scripted ≥ impact_only + 5 |
| H2 oracle gain | oracle ≥ impact_only + 10 |
| H3 order sensitivity | travel-aware order/subset differs from impact-only on ≥3/5 seeds |
| H4 Q quality | Q ≥ 0.85 × best scripted; success ≥ 0.80 |
| H5 budget | report travel ticks, aborted jobs, and service counts |

## Kill criteria

- Travel-aware gain is under 5 points.
- Impact-only and oracle are within 5 points (travel is not the binding
  variable).
- Q is below 0.70 × best scripted.
- The task requires post-hoc changes to travel, warnings, or gates.

If the travel-aware gain is under 5, retire P1 and move to P2 as the coverage
review recommends.

## Predictions

- Impact-only often chooses the far large bridge; nearest chooses the near small
  bridge.
- Travel-aware and oracle should win by 5–15 points if the spatial trade is
  real.
- Some seeds will have the large bridge near, making impact-only optimal; the
  order-sensitivity gate counts those.
- Q may need a small spatial state; if it fails, the scripted result still
  decides the kill rule.

## Artifacts

- Mechanic: RFC 0010, ADR 0020
- Planned code: `src/fabline/env/crew_schedule.py`,
  `src/fabline/harness/crew_schedule.py`
- Task card: `docs/tasks/crew-scheduling.md`
- Raw results: `results/crew_schedule/` (ignored)
- Summary: `docs/experiments/0040-crew-schedule/summary.md`
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
