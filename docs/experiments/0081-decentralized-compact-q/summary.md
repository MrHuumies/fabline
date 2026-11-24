# Experiment 0081 — Compact relative-geometry Q for decentralized triage

- **Status:** complete (negative: compact state and ensemble miss the reliability gate)
- **Date:** 2026-11-25
- **Type:** P3 decentralized multi-agent follow-up
- **Task:** `factory.multiagent.decentralized.v1` (debug/P3, not in
  `factory-v0.2`)
- **Code:** `src/fabline/env/crew_decentralized.py`,
  `src/fabline/harness/crew_decentralized.py`
- **CLI:** `python -m fabline crew-decentralized-compact`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**The compact state did not change the learned policy, and the ensemble did not
close the reliability gate.** On fresh seeds 56,000–56,004 with 1,000 training
episodes per Q seed, the old private Q and the compact Q both score **616** with
success **0.40**; the compact ensemble scores the same. The global oracle is
**764** (success 1.00), local greedy **532** (0.20), local nearest **414**
(0.00), and local aware **332** (0.00). H1 and H2 pass; H3 and H4 fail. The
local/global gap is +232 and compact Q closes +84 over local greedy, but the
learned policy remains unreliable. Per the pre-registration, the next step is
centralized training with decentralized execution, not another compact-state
variant.

## Formal results

Five evaluation seeds, three Q seeds, 1,000 training episodes:

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| local nearest | 414.00 | [258.00, 572.00] | 0.00 |
| local greedy | 532.00 | [336.00, 694.00] | 0.20 |
| local aware | 332.00 | [172.00, 496.00] | 0.00 |
| private Q (old state) | **616.00** | [578.67, 657.33] | **0.40** |
| compact Q | **616.00** | [578.67, 657.33] | **0.40** |
| compact ensemble | **616.00** | [566.00, 700.00] | **0.40** |
| global oracle | **764.00** | [748.00, 780.00] | **1.00** |

Per-Q-seed compact results are identical: Q seed 0, 1, and 2 each score 616
with success 0.40. The ensemble is identical to each member.

Per-seed oracle scores: `740, 740, 780, 780, 780`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 task validity | oracle ≥ best local scripted + 10 | **pass**, +232 |
| H2 compact skill | compact mean ≥ best local scripted + 10 | **pass**, +84 |
| H3 compact reliability | compact success ≥ 0.60 | **fail**, 0.40 |
| H4 ensemble | ensemble success ≥ 0.60 and mean ≥ best single compact | **fail**, success 0.40; mean equal |
| H5 frozen benchmark | `factory-v0.2` unchanged | **pass** |

## Interpretation

- **Representation was not the binding constraint.** The compact state included
  phase-relative time, service time, and deadline slack, but the learned policy
  and score were exactly the same as the old state at equal training budget.
  The result is not a small-sample difference; all five evaluation seeds and all
  three Q seeds agree.
- **The ensemble had nothing to combine.** All compact Q seeds converged to the
  same policy, so mean-value ensembling could not reduce variance.
- **The task is still valid.** The oracle-local gap is +232, and Q gains +84
  over local greedy. The failure is reliability on the learned policy, not task
  construction.
- **Credit assignment and partial observability remain the likely causes.**
  Independent Q shares the reward but not the state; a better state abstraction
  alone does not fix it.
- **Do not tune the compact state after this block.** The pre-registration's
  kill criterion applies: move to centralized training with decentralized
  execution.

## Caveats

- Five evaluation seeds and three Q seeds; CIs are wide.
- One radius-16 spread layout and one task configuration.
- No communication, no centralized execution, no shared reports.
- The compact state is a fixed hand-designed abstraction; no representation
  learning.
- The result is a negative representation/ensemble result, not a claim that all
  compact states fail.

## Next

1. Pre-register **centralized training with decentralized execution** on the
   same task. The critic may use the full state during training; execution stays
   per crew with the private view.
2. Keep the task and seeds; do not tune the compact state or success threshold.
3. Keep `factory-v0.2` unchanged.

## Artifacts

- Task card: [`../../tasks/crew-decentralized.md`](../../tasks/crew-decentralized.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/crew_decentralized.py`
- Raw results: `results/crew-decentralized-compact/` (ignored)
