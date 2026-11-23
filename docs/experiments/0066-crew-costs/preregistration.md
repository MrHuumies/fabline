# Experiment 0066 — Asymmetric repair-cost triage

- **Status:** preregistered (formal run pending)
- **Date:** 2026-11-23
- **Type:** P2 asymmetric-triage experiment
- **Mechanic:** role-specific repair durations on the three-bridge survivor
  triage (RFC 0024, ADR 0035)
- **Task:** `factory.power.crew-triage-costs.v1` (debug/P2, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/multi_crew.py`,
  `src/fabline/env/crew_replan.py`,
  `src/fabline/harness/crew_multi_orphan.py`
- **CLI:** `python -m fabline crew-costs`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does asymmetric repair cost make the triage order matter beyond the existing
greedy and deadline-aware rules?

## Prior

0055 has oracle 456 vs greedy 378 (+78), but greedy and aware are close. 0059
showed that spreading the layout does not widen the gap. A value-weighted pilot
was negative: naive value-greedy 256 vs greedy 378. Repair cost is a direct
time-budget asymmetry.

## Pilot

Reused 0055 seeds 12000–12004 with repair costs `(20, 40, 100)`:

| policy | mean score | success |
|---|---:|---:|
| noop | 90.0 | 0.00 |
| single_edf | 98.0 | 0.00 |
| nearest | 258.0 | 0.60 |
| greedy | 336.0 | 0.80 |
| aware | 334.0 | 0.80 |
| no-replan | 104.0 | 0.00 |
| **oracle** | **388.0** | **1.00** |

The pilot is positive: +52 over greedy, +54 over aware. The formal run uses
fresh seeds.

## Environment

- 32×16 twin-line layout, three positive bridges.
- Roles: `loop` = medium, `small` = smallest outage, `large` = largest.
- Warnings 40; failures 90/110/130; failure and B recall 100.
- Repair: loop 20, small 40, large 100; travel 2 × Manhattan.
- Initial 16 A/B pairs; A gets two survivor jobs; all positive bridges eligible.
- Reward: final production score; success ≥ 300.
- Observation: 31 features (25 crew-replan + 6 service-time features).

## Data and seeds

- Pilot: 0055 seeds 12000–12004.
- Formal: seeds 25000–25004 (5 contiguous, fresh).
- No Q training; scripted and exhaustive two-job oracle.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| nearest | nearest initial pair; nearest survivor |
| greedy | outage per service, initial and survivor |
| aware | earliest deadline initial; outage survivor |
| no-replan | initial only |
| oracle | exhaustive 16×4×4 sequence |

## Gates

| Gate | Threshold |
|---|---|
| H1 oracle gap | oracle ≥ best scripted + 10 |
| H2 coordination | best scripted ≥ single/noop + 10 |
| H3 cost sensitivity | report greedy, aware, and oracle; best scripted below oracle |
| H4 oracle success | ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Predictions

- Best scripted 310–350; oracle 360–400; gap +30–60.
- Greedy remains the best scripted or ties aware.
- Oracle success 0.80–1.00.
- If the gap is under 10 on fresh seeds, the cost axis is retired.

## Analysis plan

- Report all baselines with score/CI/success.
- Report per-seed oracle sequences and whether greedy/aware differ.
- Report `prevented`, `aborted`, `b_aborted`, and travel.
- Do not tune the cost tuple after the formal seeds.
- Keep `factory-v0.1` frozen.

## Kill criteria

- Oracle gap under +10: negative; retire the cost axis.
- Best scripted under single/noop +10: no coordination gain.
- Oracle success under 0.60: task not reliable.
- No post-hoc cost tuning.

## Transparency note

The pilot reused the 0055 formal seeds. The formal gates and cost tuple were
fixed before the fresh-seed run. Do not treat the pilot as a confirmation.
