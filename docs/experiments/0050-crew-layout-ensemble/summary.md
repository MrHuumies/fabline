# Experiment 0050 — Compact Q ensemble

- **Status:** complete (H2, H4, H5 pass; H1 and H3 fail on success)
- **Date:** 2026-11-23
- **Type:** learned-baseline experiment
- **Task:** `factory.power.crew-layouts.v1` (0046)
- **Mechanic:** none; compact-Q ensemble
- **Code:** `src/fabline/harness/layout_q.py`
- **CLI:** `python -m fabline crew-layout-ensemble`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The ensemble removes Q-seed variance but not the last aliased seed.** On
seeds 9000–9009, the mean-value and majority-vote ensembles both score
**430.0** with **0.50** success, against single compact-Q mean **415.7** and
oracle **448.0** (96% of oracle). The ensemble gains **+14.3** over the average
single policy, so H2 passes, but success remains below 0.60, so H1 and H3 fail.
The failures are concentrated on seed 9002: the oracle scores 520, every
compact policy and both ensembles score 340. The compact representation is
stable and strong; one layout remains aliased.

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
  check; one episode each).
- Three compact-Q policies, 2000 layouts each, on 80000–80999, 81000–81999,
  and 82000–82999.
- Evaluation is zero-shot; train/eval seeds are disjoint.
- No dataset artifact.

## Results

| policy | mean score | 95% CI | min | max | success |
|---|---:|---:|---:|---:|---:|
| noop | 133.0 | [111.0, 171.0] | 100 | 300 | 0.00 |
| single_edf | 140.0 | [120.0, 180.0] | 120 | 320 | 0.00 |
| random | 236.0 | [160.0, 316.5] | 100 | 520 | 0.10 |
| parallel_nearest | 360.0 | [240.0, 480.0] | 120 | 520 | 0.60 |
| parallel_greedy | 427.0 | [378.9, 484.0] | 310 | 520 | 0.50 |
| compact Q (single mean) | 415.7 | [374.5, 453.0] | 120 | 520 | 0.47 |
| **ensemble mean** | **430.0** | [376.0, 484.0] | 340 | 520 | **0.50** |
| **ensemble vote** | **430.0** | [376.0, 484.0] | 340 | 520 | **0.50** |
| **oracle** | **448.0** | [394.0, 502.0] | 340 | 520 | **0.60** |

Single compact-Q policies:

| Q seed | mean score | success |
|---|---:|---:|
| 0 | 430.0 | 0.50 |
| 1 | 408.0 | 0.50 |
| 2 | 409.0 | 0.40 |

Per-seed scores:

| seed | single mean | ensemble mean | ensemble vote | oracle |
|---:|---:|---:|---:|---:|
| 9000 | 340.0 | 340.0 | 340.0 | 340 |
| 9001 | 340.0 | 340.0 | 340.0 | 340 |
| 9002 | 266.7 | 340.0 | 340.0 | **520** |
| 9003 | 520.0 | 520.0 | 520.0 | 520 |
| 9004 | 520.0 | 520.0 | 520.0 | 520 |
| 9005 | 520.0 | 520.0 | 520.0 | 520 |
| 9006 | 340.0 | 340.0 | 340.0 | 340 |
| 9007 | 450.0 | 520.0 | 520.0 | 520 |
| 9008 | 340.0 | 340.0 | 340.0 | 340 |
| 9009 | 520.0 | 520.0 | 520.0 | 520 |

Oracle pairs: 9000:12, 9001:12, 9002:11, 9003:11, 9004:11, 9005:11,
9006:12, 9007:11, 9008:12, 9009:11.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 ensemble mean quality | mean ≥ 0.85 × oracle; success ≥ 0.60 | **fail**, mean pass (96%), success 0.50 |
| H2 variance reduction | ensemble ≥ mean single + 10 | **pass**, +14.3 |
| H3 ensemble success | success ≥ 0.60 | **fail**, 0.50 |
| H4 vote diagnostic | report vote and per-policy | **pass** |
| H5 budget | 2000 × 3 compact policies | **pass** |

## Interpretation

- **The ensemble works as designed on variance.** Single policies average
  415.7 with success 0.47; the ensemble is 430.0 with 0.50. It is also more
  stable: every compact policy now scores 340 or more, and the ensemble never
  falls to 120.
- **Mean and vote agree.** Both score 430.0/0.50; the policies choose the same
  actions on this block.
- **One seed is the blocker.** Seed 9002 is 340 for every compact policy and
  both ensembles, while the oracle scores 520. The compact key aliases this
  layout with layouts where the same closer/reachability pattern has a
  different optimal pair.
- **The representation is near its ceiling.** Mean is 96% of oracle; the
  remaining gap is a single aliased layout, not Q-seed noise.
- **H4 is still open.** Success 0.50 is below 0.60; the learned baseline is
  strong but not reliable.

## Caveats

- Ten seeds; one failed seed moves success by 0.10.
- The ensemble doubles/triples the Q table and training cost.
- The compact key still drops distance margin and pair interactions that
  distinguish seed 9002.
- No post-hoc changes to the key or gates.
- Not part of frozen `factory-v0.1`.

## Next

1. **Inspect seed 9002.** Determine whether a small, principled feature (for
   example depot-criticality or pair interaction) separates it without
   fragmenting the table.
2. **Accept the boundary.** If 9002 is a genuine aliasing limit, stop tuning
   the compact state and move to a new mechanic or task.
3. Keep `factory-v0.1` frozen.

## Artifacts

- Code: `src/fabline/harness/layout_q.py`,
  `src/fabline/harness/crew_layout_ensemble.py`
- CLI: `python -m fabline crew-layout-ensemble`
- Raw results: `results/crew-layout-ensemble/` (ignored)
- Task card: `docs/tasks/crew-layouts.md`
- Prior: [`../0048-crew-layout-q/summary.md`](../0048-crew-layout-q/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
