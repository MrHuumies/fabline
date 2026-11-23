# Experiment 0060 — Replacement crew handoff

- **Status:** complete (H1, H3, H4, H5 pass; H2 fails)
- **Date:** 2026-11-23
- **Type:** P2 third-crew/handoff experiment
- **Mechanic:** replacement crew at the recalled slot (RFC 0019, ADR 0030)
- **Task:** `factory.power.crew-replacement.v1` (debug/P2, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/crew_replan.py`,
  `src/fabline/harness/crew_replacement.py`
- **CLI:** `python -m fabline crew-replacement`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The replacement oracle helps, but the scripted replacement policies do not
capture the handoff.** On seeds 20000–20004, replacement oracle scores **476.0**
against no-replacement oracle **456.0** (**+20**), but the best scripted
replacement is recall-aware **386.0**, while no-replacement recall-aware scores
**424.0** (**−38**). H1 passes, H2 fails; H3 (coordination over single/noop) and
H4 (oracle gap 90) pass. The handoff is a real oracle opportunity, but the
current scripted pair policies are worse at using it.

## Environment

- 32×16 twin-line, three positive bridges.
- Initial A/B pair; failure/recall at 100.
- B's unfinished job aborts; C arrives at B's base.
- Post-failure A/C pair; duplicate positive targets masked.
- Reward: final production score; success ≥ 300.

## Data and seeds

- Pilot: seeds 19000–19002. No-replacement oracle 476.7, best aware 430;
  replacement oracle 490, greedy 490, nearest 480, aware 466.7.
- Formal: seeds 20000–20004 (5 contiguous, all valid by reset-only check).
- No Q training.
- No dataset artifact.

## Results

| condition | policy | mean score | 95% CI | success |
|---|---|---:|---:|---:|
| no-replacement | noop | 86.0 | [78.0, 94.0] | 0.00 |
| no-replacement | single_edf | 100.0 | [94.0, 108.0] | 0.00 |
| no-replacement | nearest | 278.0 | [136.0, 414.0] | 0.60 |
| no-replacement | greedy | 364.0 | [298.0, 438.0] | 0.80 |
| no-replacement | **aware** | **424.0** | [368.0, 474.1] | **1.00** |
| no-replacement | no_replan | 102.0 | [94.0, 112.0] | 0.00 |
| no-replacement | **oracle** | **456.0** | [426.0, 488.0] | **1.00** |
| replacement | nearest | 314.0 | [166.0, 464.0] | 0.60 |
| replacement | greedy | 378.0 | [304.0, 459.1] | 0.80 |
| replacement | **aware** | **386.0** | [238.0, 473.1] | **0.80** |
| replacement | **oracle** | **476.0** | [458.0, 494.0] | **1.00** |

Oracle actions:

- no-replacement: `20000:[6,12,0]`, `20001:[2,12,4]`, `20002:[2,12,4]`,
  `20003:[4,12,8]`, `20004:[12,4,8]`.
- replacement: `20000:[6,12]`, `20001:[6,13]`, `20002:[6,7]`,
  `20003:[6,14]`, `20004:[14,6]`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 replacement oracle | replacement oracle ≥ no-replacement oracle + 10 | **pass**, +20 |
| H2 handoff gain | replacement best scripted ≥ no-replacement best + 10 | **fail**, −38 |
| H3 coordination | replacement best ≥ no-replacement single/noop + 10 | **pass**, +286 |
| H4 oracle gap | report replacement oracle vs best scripted | **pass**, +90 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **The handoff opportunity exists.** The oracle finds a +20 improvement and a
  90-point gap over the best scripted replacement.
- **The scripted replacement policies are the blocker.** They choose pairs that
  are worse than the no-replacement sequential A-only policy. The replacement
  action requires a different rule or a learned policy.
- **No-replacement recall-aware is strong.** It reaches 424/1.00, so the
  baseline is not weak; the replacement policies fail to beat a good two-crew
  policy.
- **This is not a promoted benchmark.** H2 fails; the task is a boundary and a
  candidate for a learned replacement policy.
- **The P2 review’s third-crew recommendation is only partially resolved.**
  Immediate replacement at B's base is not enough for scripted handoff.

## Caveats

- Five formal seeds; CIs are wide.
- C reuses B's base; a new base or delayed arrival is untested.
- One replacement pair; no full three-agent initial coordination.
- Scripted policies only; no Q.
- Not part of frozen `factory-v0.1`.

## Next

1. **A better replacement policy:** pair-aware rule using bridge value,
  distance, and remaining time; or a compact/learned policy.
2. **Full third crew:** three crews at the initial decision, not a slot swap.
3. **If neither adds a scripted gain:** P2 is near its practical ceiling; move
  to random topology or P3.

## Artifacts

- Mechanic: RFC 0019, ADR 0030
- Env: `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_replacement.py`
- CLI: `python -m fabline crew-replacement`
- Raw results: `results/crew-replacement/` (ignored)
- Task card: `docs/tasks/crew-replacement.md`
- Prior: [`../0055-crew-triage/summary.md`](../0055-crew-triage/summary.md)
- Coverage review: [`../../coverage-review-p2.md`](../../coverage-review-p2.md)
