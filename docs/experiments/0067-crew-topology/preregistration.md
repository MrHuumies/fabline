# Experiment 0067 — Random-topology triage

- **Status:** preregistered (formal run pending)
- **Date:** 2026-11-23
- **Type:** P2 random-topology experiment
- **Mechanic:** full-width random three-line layout for the three-bridge survivor
  triage (RFC 0025, ADR 0036)
- **Task:** `factory.power.crew-topology.v1` (debug/P2, not in `factory-v0.1`)
- **Code:** `src/fabline/worlds/factory/generator.py`,
  `src/fabline/harness/crew_multi_orphan.py`
- **CLI:** `python -m fabline crew-topology --layout random|spread`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a full-width random three-line topology create a larger triage-assignment
gap than the controlled spread layout?

## Prior

0055 twin-line triage is positive but controlled. 0059 spread-layout triage is
negative: greedy matches oracle. The P2 review lists larger/random topology as
the remaining structural gap.

## Pilot

Seeds 27,000–27,004, same triage rules. Best scripted is the best of nearest,
greedy, and aware per seed.

| Layout | Oracle | Best scripted | Per-seed gaps | Mean gap |
|---|---:|---:|---|---:|
| spread | 592.0 | 568.0 | 0, 90, 0, 0, 0 | +18.0 |
| random | 472.0 | 438.0 | 0, 50, 50, 30, 40 | +34.0 |

Paired gap difference: +16.0 on average, with one negative seed (27,001,
−40). Random is harder in absolute score and the gap is present on 4/5 seeds.
The pilot is suggestive, not a confirmation.

## Environment

- 48×24 map, three production lines.
- Random line rows at least two apart; full-width random x starts.
- One extra belt per line; no band constraint.
- Existing seeded wire graph; capacity 24, radius 8, redundancy 2.
- Triage: warnings 40; failures 90/110/130; failure and B recall 100.
- Initial 16 A/B pairs; A gets two survivor jobs; all positive bridges eligible.
- Reward: final production score; success ≥ 300.
- Observation and action shape unchanged from 0055.

## Data and seeds

- Pilot: 27,000–27,004.
- Formal: 28,000–28,004 (5 contiguous, fresh).
- Layouts: `random_topology` and `spread_gear` on the same seeds.
- No Q training; scripted and exhaustive two-job oracle.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| nearest | nearest initial pair; nearest survivor |
| greedy | outage per service |
| aware | earliest deadline initial; outage survivor |
| no-replan | initial only |
| oracle | exhaustive 16×4×4 sequence |

## Gates

| Gate | Threshold |
|---|---|
| H1 random gap | per-seed oracle ≥ best scripted + 10 on average |
| H2 coordination | best scripted ≥ single/noop + 10 |
| H3 layout effect | random mean gap ≥ spread mean gap + 10 |
| H4 oracle success | ≥ 0.60 |
| H5 frozen benchmark | unchanged |

The primary unit is the **per-seed gap**, not the difference of means across
seeds. Report the paired difference and its seed range.

## Predictions

- Random mean gap +20–40; spread +10–25.
- H3 pass by +10–20.
- Greedy or aware is the best scripted; nearest fails on some seeds.
- Oracle success 1.00.
- If H3 fails, random topology is harder but not a new decision; close P2 and
  move to P3.

## Analysis plan

- Report all baselines with score/CI/success.
- Compute per-seed best scripted and gap for both layouts.
- Report paired differences and oracle sequences.
- Report `prevented`, `aborted`, `b_aborted`, and travel.
- Do not tune the layout, thresholds, or seeds after seeing the formal block.
- Keep `factory-v0.1` frozen.

## Kill criteria

- Random mean gap under +10: negative.
- Random gap not at least +10 over spread: negative; topology is harder, not a
  new decision.
- Oracle success under 0.60: task not reliable.
- No post-hoc layout tuning.

## Transparency note

The pilot used seeds 27,000–27,004. The formal block is fresh
28,000–28,004. The pilot's +16 paired difference is not a confirmation.
