# Experiment 0050 — Compact Q ensemble

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-22
- **Type:** learned-baseline experiment
- **Task:** `factory.power.crew-layouts.v1` (0046)
- **Mechanic:** none; compact-Q ensemble
- **Code:** `src/fabline/harness/layout_q.py`
- **CLI:** `python -m fabline crew-layout-ensemble`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Can averaging three compact-Q policies remove Q-seed variance and clear the
0.60 success gate?

Compact Q (0048) lifted the twin-line baseline from 233 to 422, but one Q seed
matched oracle exactly (442/0.60) while the others scored 424/0.50 and
400/0.40. The state is sufficient; the remaining problem is seed variance.

## Environment

- 32×16, two gear lines, random x offsets, one generator capacity 24.
- Crew A at the first depot; B on a random empty cell at least eight Manhattan
  cells from A.
- Targets: loop, small bridge, large bridge.
- Warning 40; failures 90 (loop), 110 (small), 130 (large).
- One-shot pair assignment; same-wire positive pairs masked.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Formal evaluation: seeds 9000–9009 (10 contiguous, all valid by reset-only
  check).
- Three compact-Q policies, 2000 training layouts each, on 80000–80999,
  81000–81999, and 82000–82999.
- Evaluation is zero-shot; train/eval seeds are disjoint.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| nearest | nearest target per crew |
| greedy | outage per service time |
| random | uniform legal pair |
| oracle | best pair by simulation |
| single compact Q | each of the three policies alone |
| ensemble mean | average the three masked Q vectors, then argmax |
| ensemble vote | majority vote of the three greedy actions |

## Gates

| Gate | Threshold |
|---|---|
| H1 ensemble mean quality | mean ≥ 0.85 × oracle; success ≥ 0.60 |
| H2 variance reduction | ensemble mean ≥ mean of single compact Q means + 10 |
| H3 ensemble success | ensemble mean success ≥ 0.60 |
| H4 vote diagnostic | report ensemble vote and per-policy scores; no gate |
| H5 budget | 2000 episodes × 3 compact policies |

## Predictions

- Single compact Q policies average 410–430 with success 0.45–0.55.
- Ensemble mean averages 430–445 with success 0.60–0.70.
- Ensemble vote is close to ensemble mean, possibly more variable.
- Oracle averages 440–460.
- If the ensemble passes, the compact state is a usable learned baseline on the
  twin-line task without a larger state.

## Kill criteria

- Ensemble mean is below 0.85 × oracle or below 0.60 success.
- Ensemble mean does not beat the mean single policy by 10.
- The result requires post-hoc policy selection or gate changes.

## Analysis plan

- Report all baselines, single policies, ensemble mean, and ensemble vote with
  CIs and success.
- Report per-seed scores and oracle pairs.
- Keep the task, layout, success threshold, and Q budget fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Code: `src/fabline/harness/layout_q.py`
- CLI: `python -m fabline crew-layout-ensemble`
- Task card: `docs/tasks/crew-layouts.md`
- Raw results: `results/crew-layout-ensemble/` (ignored)
- Summary: `docs/experiments/0050-crew-layout-ensemble/summary.md`
- Prior: [`../0048-crew-layout-q/summary.md`](../0048-crew-layout-q/summary.md)
