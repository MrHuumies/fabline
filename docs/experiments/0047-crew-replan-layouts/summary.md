# Experiment 0047 — Recall/replanning on twin-line layouts

- **Status:** complete (H1, H2, H5 pass; H3 and H4 fail)
- **Date:** 2026-11-22
- **Type:** P2 multi-agent combination experiment
- **Mechanic:** known crew recall on twin-line randomized layouts (RFC 0014,
  ADR 0024)
- **Task:** `factory.power.crew-replan-layouts.v1` (debug/P2, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/crew_replan.py`,
  `src/fabline/harness/crew_replan.py`
- **CLI:** `python -m fabline crew-replan-layouts`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The recovery dispatch survives the larger layout, but the layout gap does
not.** On seeds 7000–7009, recall-aware scores **480.0** against no-replan
**240.0** (**+240 [135, 339]**), and the best scripted two-crew policy (greedy)
scores **496.0** against single-crew **120.0** (**+376 [358, 394]**). However,
the oracle is **505.0** and the oracle-greedy gap is only **+9 [0, 21]**,
missing the pre-registered +10 gate by one point. Full tabular Q scores
**210.0** with **23%** success and fails the 0.85 quality gate. The combined
task is a strong recovery result but not a robust new layout benchmark.

## Environment

- 32×16, two gear lines, random x offsets, one generator capacity 24.
- Crew A at the first depot; B on a random empty cell at least eight Manhattan
  cells from A.
- Warnings 40; failures 90 (loop), 110 (small), 130 (large).
- B recall 100; unfinished B job aborts.
- Initial pair assignment; A's second dispatch is noop or the abandoned
  positive bridge.
- Travel = 2 × Manhattan; service 40 ticks.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 0–9. Pilot oracle 512, greedy 491, recall-aware 433, nearest
  405, no-replan 260.
- Formal evaluation: seeds 7000–7009 (10 contiguous, all valid by reset-only
  check; one episode each).
- Q training: three policies, 500 layouts each, on 65000–65499, 66000–66499,
  67000–67499.
- Q evaluation is zero-shot on the formal seeds; train/eval disjoint.
- No dataset artifact.

## Results

| policy | mean score | 95% CI | min | max | success | B aborted | prevented | travel |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| noop | 110.0 | [106.0, 114.0] | 100 | 120 | 0.00 | 0.0 | 0.00 | 0.0 |
| single_edf | 120.0 | [120.0, 120.0] | 120 | 120 | 0.00 | 0.0 | 1.00 | 17.2 |
| random | 167.0 | [118.0, 218.5] | 100 | 340 | 0.00 | 0.7 | 0.40 | 54.0 |
| **parallel_nearest** | **486.0** | [466.0, 504.0] | 440 | 520 | **1.00** | 0.6 | 1.40 | 65.0 |
| **parallel_greedy** | **496.0** | [478.0, 514.0] | 440 | 520 | **1.00** | 0.4 | 1.60 | 56.6 |
| **recall_aware** | **480.0** | [462.0, 500.0] | 440 | 520 | **1.00** | 0.7 | 1.30 | 74.8 |
| recall_aware_no_replan | 240.0 | [120.0, 360.0] | 120 | 520 | 0.30 | 0.7 | 1.30 | 47.8 |
| tabular Q | 210.0 | [153.5, 270.7] | 100 | 520 | 0.23 | 0.2 | 0.57 | 24.7 |
| **oracle** | **505.0** | [487.5, 519.5] | 440 | 520 | **1.00** | 0.3 | 1.70 | 58.8 |

Paired differences:

| comparison | mean | 95% CI |
|---|---:|---:|
| recall_aware − no_replan | +240.0 | [135.0, 339.1] |
| parallel_greedy − single_edf | +376.0 | [358.0, 394.0] |
| oracle − parallel_greedy | **+9.0** | **[0.0, 21.0]** |

Oracle actions (initial, replan):

| seed | initial | replan | score |
|---:|---:|---:|---:|
| 7000 | 14 | 0 | 520 |
| 7001 | 11 | 0 | 520 |
| 7002 | 11 | 0 | 520 |
| 7003 | 11 | 12 | 440 |
| 7004 | 14 | 8 | 510 |
| 7005 | 11 | 0 | 520 |
| 7006 | 14 | 0 | 520 |
| 7007 | 11 | 12 | 460 |
| 7008 | 14 | 0 | 520 |
| 7009 | 14 | 0 | 520 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 coordination gain | best two-crew scripted ≥ single_edf + 10 | **pass**, +376 |
| H2 replan gain | recall_aware ≥ no_replan + 10 | **pass**, +240 |
| H3 layout gap | oracle ≥ best two-crew scripted + 10 | **fail**, +9 |
| H4 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 | **fail**, 41.6%; 0.23 |
| H5 budget | 500 episodes per Q policy; 3 policies | **pass** |

## Interpretation

- **The recovery dispatch is robust.** It adds 240 points on the larger
  layout, more than on the 16×8 task.
- **The layout gap is not robust to recall.** Once the survivor can recover the
  abandoned bridge, greedy is within 9 points of oracle; the oracle-greedy
  difference is driven by two seeds (7004 and 7008) and has a CI that includes
  zero.
- **The 0046 assignment gap does not carry over.** The combined task is easier
  for scripted policies than the assignment-only twin-line task.
- **Q fails.** 210 mean, 23% success, 41.6% of oracle; the larger two-decision
  state is still unsolved.
- **Do not promote this task as a benchmark.** Keep 0045 (recall, 16×8) and 0046
  (assignment, twin lines) as the separate positive slices; this combination
  is a near-miss on its layout gate.

## Caveats

- Ten formal seeds; CIs are wide.
- The oracle-greedy gap is +9 with CI [0, 21]; do not read it as a positive.
- Some layouts cap at 440/460; success 400 is a secondary threshold.
- Q uses a reduced budget (three policies × 500 episodes); the failure is
  consistent with the larger-state boundary.
- Not part of frozen `factory-v0.1`.

## Next

1. **Keep the combined task unpromoted.** The separate 0045 and 0046 slices
   remain the P2 results.
2. **Layout-aware Q.** The learned baseline is the open weakness on both 0046
   and 0047.
3. **Harder recovery variants.** Multiple orphans, repeated failure, or a
   deadline that prevents free recovery would restore the layout gap.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0014, ADR 0024
- Env: `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_replan.py`
- CLI: `python -m fabline crew-replan-layouts`
- Raw results: `results/crew-replan-layouts/` (ignored)
- Task card: `docs/tasks/crew-replan-layouts.md`
- Prior: [`../0046-crew-layouts/summary.md`](../0046-crew-layouts/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
