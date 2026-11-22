# Experiment 0040 — Crew scheduling with travel time

- **Status:** complete (H1–H3/H5 pass; H4 fails)
- **Date:** 2026-11-22
- **Type:** P1 phase 1D spatial-scheduling experiment
- **Mechanic:** one repair crew, travel + service time (RFC 0010, ADR 0020)
- **Task:** `factory.power.crew-schedule.v1` (debug/P1, not in `factory-v0.1`)
- **Code:** `src/fabline/env/crew_schedule.py`,
  `src/fabline/harness/crew_schedule.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Proximity and deadlines are the binding variables, not outage impact alone.**
With warnings at 40 and failures at 90/120/150, impact-only scores **62.4**,
nearest scores 223.2, and earliest-deadline-first scores **260.0**, matching the
oracle. Impact-only services the far large bridge and misses the small deadline;
EDF services the small bridge at 120, then the large at 150. H1, H2, H3, and H5
pass. **H4 fails:** tabular Q scores 156.4 and succeeds on only 0.52 of episodes.
The task is a positive spatial-scheduling result with an unresolved learned
baseline.

## Environment

- Gear line, wired power, one generator, capacity 12.
- Roles: zero-impact loop, small bridge, large bridge.
- Warnings at tick 40; failures at 90 (loop), 120 (small), 150 (large).
- Crew starts at the depot.
- Service time: 2 × Manhattan travel to the nearest endpoint + 40 repair ticks.
- Budget: 2 jobs for 3 wires.
- Reward: time-weighted prevented/restored outage.
- Outcome: final production score; success ≥ 150.

## Data and seeds

- Evaluation: seeds 800–804, 5 episodes each.
- Q training: 500 layouts from 15000 + 1000 × Q seed.
- Pilot: seeds 0–9; formal seeds are fresh.
- No dataset artifact.

## Results

| policy | mean score | 95% CI | prevented | travel | success |
|---|---:|---:|---:|---:|---:|
| noop | 56.8 | [53.6, 60.0] | 0.00 | 0.0 | 0.00 |
| impact_only | 62.4 | [55.6, 68.6] | 1.00 | 16.7 | 0.00 |
| travel_aware | 62.4 | [55.6, 68.6] | 1.00 | 16.7 | 0.00 |
| random | 110.4 | [80.8, 143.6] | 1.00 | 18.2 | 0.24 |
| tabular Q | 156.4 | [123.2, 192.6] | 1.24 | 16.4 | 0.52 |
| nearest | 223.2 | [192.4, 251.6] | 1.80 | 14.0 | 0.80 |
| **earliest_deadline** | **260.0** | [260.0, 260.0] | **2.00** | 14.4 | **1.00** |
| oracle | **260.0** | [260.0, 260.0] | **2.00** | 14.0 | **1.00** |

Oracle sequences: `[2, 3]` on all five seeds (small bridge, then large bridge).

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 travel gain | best spatial scripted ≥ impact_only + 5 | **pass**, +197.6 |
| H2 oracle gain | oracle ≥ impact_only + 10 | **pass**, +197.6 |
| H3 order sensitivity | spatial order differs from impact on ≥3/5 seeds | **pass**, 5/5 |
| H4 Q quality | Q ≥ 0.85 × best; success ≥ 0.80 | **fail**, 156.4 vs 221; 0.52 |
| H5 budget | report travel/abort/service counts | **pass** |

## Interpretation

- **Impact-only is the wrong prior when deadlines are tight.** The large bridge
  is farther away; servicing it first misses the small deadline.
- **Nearest is a strong but imperfect spatial policy.** It improves to 223.2 but
  still chooses the wrong order on some seeds.
- **Deadline-aware repair matches the oracle.** EDF scores 260 on every seed;
  the spatial trade is real and measurable.
- **The travel kill rule does not trigger.** The review's <5-point rule is
  cleared by a wide margin.
- **Q is the blocker.** Tabular Q does not learn the deadline/order policy; its
  state is too coarse and the action is a multi-tick option.
- **This is a planning/scripted result, not a learned-control result.** The task
  is a useful spatial benchmark only if a learned baseline can be made
  competitive.

## Caveats

- Deterministic gear line and role selection.
- One crew; atomic travel + service.
- EDF uses known failure ticks; it is a forecast-aware scripted baseline.
- Q is seed-sensitive and below the scripted policies.
- Budget 2 for 3 targets; the loop remains a trap.
- Not part of frozen `factory-v0.1`.

## Next

1. **Make Q competitive:** add deadline/role features, use a semi-MDP option for
   the multi-tick service, or use Q(λ).
2. **Multi-crew scheduling** only if the single-crew learned baseline works.
3. **P2:** multi-agent or larger/random layouts, per the coverage review.

Do not add another scripted policy layer before the learned baseline is fixed.

## Artifacts

- Mechanic: RFC 0010, ADR 0020
- Env: `src/fabline/env/crew_schedule.py`
- Harness: `src/fabline/harness/crew_schedule.py`
- CLI: `python -m fabline crew-schedule`
- Raw results: `results/crew_schedule/` (ignored)
- Task card: `docs/tasks/crew-scheduling.md`
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
