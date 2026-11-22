# Experiment 0048 — Compact layout-aware Q for twin-line assignment

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-22
- **Type:** learned-baseline experiment
- **Task:** `factory.power.crew-layouts.v1` (0046)
- **Mechanic:** none; new Q state representation
- **Code:** `src/fabline/harness/layout_q.py`
- **CLI:** `python -m fabline crew-layout-q`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Can a compact relative-geometry/reachability Q state close the learned-baseline
gap on the twin-line assignment task?

The old tabular Q over tick/wire states and binned absolute distances scores
217.0 with 0/10 success (0046). A compact state that encodes which crew is
closer to each bridge and whether each crew can finish before the deadline may
generalize better.

## Environment

- 32×16, two gear lines, random x offsets, one generator capacity 24.
- Crew A at the first depot; B on a random empty cell at least eight Manhattan
  cells from A.
- Targets: loop, small bridge, large bridge.
- Warning 40; failures 90 (loop), 110 (small), 130 (large).
- One-shot pair assignment; same-wire positive pairs masked.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot (compact Q): seeds 6000–6009, 2000 training layouts, compact Q 441.0
  with 0.70 success; old tabular Q 217.0 with 0.00 success.
- Formal: seeds 8000–8009 (10 contiguous, all valid by reset-only check).
- Compact Q: three policies, 2000 training layouts each, starting at
  80000 + 1000 × Q seed.
- Old tabular Q: three policies, 500 training layouts each, same disjoint
  ranges.
- Evaluation is zero-shot and disjoint from training.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| parallel_nearest | nearest target per crew |
| parallel_greedy | outage per service time |
| random | uniform legal pair |
| oracle | best pair by simulation |
| old tabular Q | full tick/wire/absolute-distance state, 500 layouts |
| compact Q | closer-crew + reachability bins, 2000 layouts |

## Gates

| Gate | Threshold |
|---|---|
| H1 compact Q quality | compact Q mean ≥ 0.85 × oracle mean; success ≥ 0.60 |
| H2 representation gain | compact Q mean ≥ old tabular Q mean + 100 |
| H3 success | compact Q success ≥ 0.60 |
| H4 scripted ceiling | report nearest/greedy/oracle; no gate change |
| H5 budget | 2000 episodes × 3 compact policies; 500 × 3 old policies |

## Predictions

- Compact Q averages 400–450 with success 0.60–0.80.
- Old tabular Q averages 150–250 with success 0.00–0.20.
- Oracle averages 440–460; compact Q is within 0.85 × oracle.
- The compact state is the active ingredient: relative geometry and
  reachability, not more training episodes alone.

## Kill criteria

- Compact Q is below 0.85 × oracle or below 0.60 success.
- Compact Q does not beat the old tabular Q by 100.
- The result requires post-hoc changes to the state, seeds, or gates.

## Analysis plan

- Report all scripted, old-Q, compact-Q, and oracle scores with CIs and success.
- Report per-seed scores and oracle pairs.
- Report compact Q per-policy means.
- Keep the task, layout, and success threshold fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Code: `src/fabline/harness/layout_q.py`
- CLI: `python -m fabline crew-layout-q`
- Task card: `docs/tasks/crew-layouts.md`
- Raw results: `results/crew-layout-q/` (ignored)
- Summary: `docs/experiments/0048-crew-layout-q/summary.md`
- Prior: [`../0046-crew-layouts/summary.md`](../0046-crew-layouts/summary.md)
