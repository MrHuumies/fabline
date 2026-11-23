# Experiment 0055 — Three-bridge survivor triage

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-23
- **Type:** P2 repeated-failure/triage experiment
- **Mechanic:** three positive bridges, job failure at 100, two survivor jobs
  (RFC 0017, ADR 0028)
- **Task:** `factory.power.crew-triage.v1` (debug/P2, not in `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does moving the failure to tick 100 make the initial assignment matter and
create a real three-bridge triage gap over the best scripted policy?

The all-abort sequential task (0054) is shallow: both jobs fail before
completing, so the initial pair is irrelevant. Here some jobs finish before 100;
the first assignment trades off against A's two survivor jobs.

## Environment

- 32×16 twin-line layout, random crew-B base.
- Three positive bridges; internal `loop` = medium bridge.
- Warnings 40; failures 90/110/130.
- Job failure and B recall at 100.
- A has two survivor jobs; all unresolved positive bridges are eligible.
- Reward: final production score; success ≥ 300.

## Data and seeds

- Pilot: seeds 0–4. Oracle 440/460/510/480/410 (mean 460); nearest mean 434;
  aware 374; greedy 332; no-replan ~100.
- Formal: seeds 12000–12004 (5 contiguous, all valid by reset-only check).
- No Q training; scripted and exhaustive two-job oracle.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| nearest | nearest pair; nearest unresolved target |
| greedy | outage per service time |
| recall-aware | earliest bridge for A, other for B |
| no-replan | initial pair only |
| oracle | best initial pair and two-action survivor sequence |

## Gates

| Gate | Threshold |
|---|---|
| H1 oracle gap | oracle ≥ best scripted + 10 |
| H2 coordination gain | best scripted ≥ single/noop + 10 |
| H3 nearest sensitivity | nearest mean < oracle |
| H4 oracle success | oracle success ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Predictions

- Oracle 440–480; nearest 420–450; aware/greedy variable.
- No-replan 90–120; single/noop 60–100.
- The initial pair is relevant because some jobs finish before 100.
- The oracle sequence varies; expect a +10–30 gap over the best scripted.
- If greedy/nearest matches oracle, report the shallow ceiling.

## Kill criteria

- Oracle does not beat the best scripted by 10.
- The task requires post-hoc changes to the failure tick, roles, or gates.

## Analysis plan

- Report all baselines with score, CI, success, and per-seed scores.
- Report oracle sequences and initial-job completion/abort counts.
- Keep the layout, failure tick, role mode, and two-job budget fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0017, ADR 0028
- Env: `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_multi_orphan.py`
- CLI: `python -m fabline crew-triage`
- Task card: `docs/tasks/crew-triage.md`
- Raw results: `results/crew-triage/` (ignored)
- Summary: `docs/experiments/0055-crew-triage/summary.md`
- Prior: [`../0054-crew-multi-orphan/summary.md`](../0054-crew-multi-orphan/summary.md)
