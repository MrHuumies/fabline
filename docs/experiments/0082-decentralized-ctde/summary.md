# Experiment 0082 — Centralized critic, decentralized actors for triage

- **Status:** complete (negative: CTDE collapses to noop-like behavior)
- **Date:** 2026-11-25
- **Type:** P3 decentralized multi-agent follow-up
- **Task:** `factory.multiagent.decentralized.v1` (debug/P3, not in
  `factory-v0.2`)
- **Code:** `src/fabline/env/crew_decentralized.py`,
  `src/fabline/harness/crew_decentralized.py`
- **CLI:** `python -m fabline crew-decentralized-ctde`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**The centralized critic did not produce a useful decentralized actor policy.**
On fresh seeds 56,000–56,004 with 1,000 training episodes per seed, CTDE scores
**248** with success **0.00**, below local greedy (532, 0.20), local nearest
(414, 0.00), and the 0081 independent-Q reference (616, 0.40). The global oracle
is 764 (success 1.00). Per-seed CTDE scores are `170, 180, 160, 570, 160`, and
all three Q seeds produce the same policy. H1 passes; H2, H3, and H4 fail. The
pre-registered kill criterion applies: retire the local-policy line for this
task and report it as oracle/scripted-only. The negative is specific to this
tabular critic/count-actor method, not a proof that all CTDE methods fail.

## Formal results

Five evaluation seeds, three Q seeds, 1,000 training episodes:

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| local nearest | 414.00 | [258.00, 572.00] | 0.00 |
| local greedy | 532.00 | [336.00, 694.00] | 0.20 |
| local aware | 332.00 | [172.00, 496.00] | 0.00 |
| private Q (0081 reference) | 616.00 | [578.67, 657.33] | 0.40 |
| compact Q (0081 reference) | 616.00 | [578.67, 657.33] | 0.40 |
| **CTDE** | **248.00** | **[168.00, 330.00]** | **0.00** |
| global oracle | 764.00 | [748.00, 780.00] | 1.00 |

Per-Q-seed CTDE results are identical: Q seed 0, 1, and 2 each score 248 with
success 0.00.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 task validity | oracle ≥ local greedy + 10 | **pass**, +232 |
| H2 CTDE skill | CTDE mean ≥ local greedy + 10 | **fail**, −284 |
| H3 CTDE over independent Q | CTDE mean ≥ best independent Q + 10 | **fail**, −368 |
| H4 CTDE reliability | CTDE success ≥ 0.60 | **fail**, 0.00 |
| H5 frozen benchmark | `factory-v0.2` unchanged | **pass** |

## Interpretation

- **The actors collapsed to noop-like behavior.** The per-seed scores are near
  the no-repair baseline, and the policy is identical across Q seeds.
- **The centralized critic did not provide a usable learning signal** for the
  marginal actor update at this budget and state granularity. The critic and
  actor keys are both compact tabular abstractions; the global key is large
  enough that the critic remains sparse after 1,000 episodes.
- **This is a method-level negative, not a task-level one.** The oracle/local
  gap is intact (+232), and independent Q still beats local greedy (+84). The
  task remains valid for scripted/oracle evaluation.
- **Do not add another critic or actor variant to this task.** The
  pre-registered kill criterion applies.

## Caveats

- Five evaluation seeds and three Q seeds; CIs are wide.
- One radius-16 spread layout and one task configuration.
- No communication and no shared reports.
- The CTDE method is a tabular centralized critic with count-based marginal
  actors; other CTDE methods are not tested.
- The 0081 private/compact Q values are carried forward references, not rerun in
  this block.

## Next

1. Retire the local-policy line for decentralized triage; keep the task as a
   debug oracle/scripted surface.
2. Move to **transition-model planning** or **maintenance calibration**, the
   remaining 0.3.0 gaps.
3. Keep `factory-v0.2` and `v0.3.0` unchanged.

## Artifacts

- Task card: [`../../tasks/crew-decentralized.md`](../../tasks/crew-decentralized.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/crew_decentralized.py`
- Raw results: `results/crew-decentralized-ctde/` (ignored)
