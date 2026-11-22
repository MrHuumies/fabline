# Experiment 0042 — Two-crew repair coordination

- **Status:** complete (all gates pass; see [`summary.md`](summary.md))
- **Date:** 2026-11-22
- **Type:** P2 multi-agent assignment experiment
- **Mechanic:** two crews, parallel travel + repair (RFC 0011, ADR 0021)
- **Task:** `factory.power.crew-coordination.v1` (debug/P2, not in
  `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a second crew with a different base produce a real coordination gain over
the best single-crew assignment?

The task assigns one target to each crew in parallel: loop, small bridge, large
bridge. With warnings at 40 and failures at 90/110/130, one crew cannot save both
bridges, but two crews can.

## Environment

- Gear line, wired power, one generator, capacity 12.
- Crew A starts at the depot; crew B starts at the opposite corner.
- Targets: zero-impact loop, small bridge, large bridge.
- Warnings at 40; failures at 90 (loop), 110 (small), 130 (large).
- Assignment is one-shot: each crew gets one target (or noop).
- Travel = 2 × Manhattan distance to the endpoint; service = 40 ticks.
- Same-wire positive assignments are masked.
- Jobs run concurrently; a preventive job aborts if its target fails first.
- Reward: production score gained from the assignment to episode end.
- Outcome: final score; success ≥ 150.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only, earliest positive deadline |
| parallel_nearest | each crew takes its nearest positive target |
| parallel_greedy | maximize summed outage per service time, no duplicates |
| oracle | best pair by simulation |
| random | uniform legal pair |
| tabular Q | role/position state; 500 training layouts |

## Data and seeds

- Pilot: seeds 0–9.
- Formal: seeds 1000, 1001, 1002, 1004, 1005. Seed 1003 has no zero-impact loop and is skipped; 1005 is the next valid seed.
- Q training: 30000 + 1000 × Q seed.
- No dataset artifact.

## Gates

| Gate | Threshold |
|---|---|
| H1 coordination gain | best two-crew scripted ≥ single_edf + 10 |
| H2 oracle gain | oracle ≥ single_edf + 10 |
| H3 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 |
| H4 assignment quality | report duplicate/abort counts and chosen pairs |
| H5 budget | 500 training episodes |

## Predictions

- Single-crew EDF scores about 60; it can save only one bridge.
- Parallel nearest/greedy score about 180–260; timing and crew-target matching
  matter.
- Oracle scores 260 on every seed with pair (small A, large B).
- Q scores about 220–260 and succeeds on 0.8 of seeds.
- If Q fails the quality gate, report it; the coordination gain still decides
  the slice.

## Kill criteria

- Two crews do not beat single-crew EDF by 10.
- Oracle does not beat single-crew by 10.
- Q is below 0.70 × oracle.
- The task requires post-hoc changes to bases, deadlines, or gates.

## Analysis plan

- Report all conditions with score, CI, prevented, aborted, travel, success.
- Report oracle pairs and Q per-seed scores.
- Keep the crew mechanic, deadlines, and one-shot assignment fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0011, ADR 0021
- Env: `src/fabline/env/multi_crew.py`
- Harness: `src/fabline/harness/multi_crew.py`
- CLI: `python -m fabline multi-crew`
- Task card: `docs/tasks/multi-crew.md`
- Raw results: `results/multi_crew/` (ignored)
- Summary: `docs/experiments/0042-multi-crew/summary.md`
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
