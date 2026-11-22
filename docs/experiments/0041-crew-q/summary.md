# Experiment 0041 — Deadline-aware Q for crew scheduling

- **Status:** complete (all gates pass)
- **Date:** 2026-11-22
- **Type:** P1 learned-baseline experiment; follow-up to
  [`0040`](../0040-crew-schedule/summary.md)
- **Task:** `factory.power.crew-schedule.v1` (debug/P1, not in `factory-v0.1`)
- **Code:** `src/fabline/harness/crew_schedule.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**A deadline/role state with episodic Q closes the learned gap.** On fresh
seeds 900–904, deadline-aware Q scores **253.2** [248.8, 256.8] with success
**1.00**, versus **136.0** for the old tabular Q and **260.0** for EDF and the
oracle. The learned gain over the old Q is **+117.2**; deadline Q reaches 97.4%
of EDF. All five gates pass. The fix is representation and credit assignment,
not a change to the mechanic: include role distances and failure deadlines, and
use an undiscounted episodic update for the multi-tick service action.

## Data and seeds

- Evaluation: seeds 900–904, 5 episodes each.
- Training: 500 layouts from 20000 + 1500 × Q seed.
- Pilot: seeds 800–804 were used by 0040; formal seeds are fresh.
- No dataset artifact.

## Results

| policy | mean score | 95% CI | prevented | travel | success |
|---|---:|---:|---:|---:|---:|
| noop | 58.0 | [55.2, 61.0] | 0.00 | 0.0 | 0.00 |
| impact_only | 61.2 | [56.8, 66.0] | 1.00 | 20.6 | 0.00 |
| travel_aware | 61.2 | [56.8, 66.0] | 1.00 | 20.6 | 0.00 |
| random | 95.2 | [71.2, 122.8] | 1.16 | 17.4 | 0.16 |
| tabular_q (0040) | 136.0 | [105.2, 172.2] | 1.12 | 19.1 | 0.44 |
| nearest | 246.4 | [226.0, 260.0] | 1.92 | 17.3 | 0.92 |
| **deadline_q** | **253.2** | [248.8, 256.8] | 1.28 | 19.7 | **1.00** |
| earliest_deadline | **260.0** | [260.0, 260.0] | 2.00 | 17.6 | **1.00** |
| oracle | **260.0** | [260.0, 260.0] | 2.00 | 17.6 | **1.00** |

Deadline Q per-seed scores: 250, 258, 258, 250, 250; success 1.00 on every
seed.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 deadline Q quality | ≥ 0.85 × EDF; success ≥ 0.80 | **pass**, 97.4%; 1.00 |
| H2 learned gain | deadline_q ≥ tabular_q + 30 | **pass**, +117.2 |
| H3 learned success | ≥ 0.80 | **pass**, 1.00 |
| H4 per-seed | report | **pass** |
| H5 budget | 500 training episodes | **pass** |

## Interpretation

- **The task was solvable; the state was not.** Adding distances and failure
  deadlines gives the agent the information EDF uses.
- **Episodic updates matter for multi-tick service.** The old Q discounted a
  delayed, time-weighted return; gamma 1.0 removes that bias.
- **Deadline Q is competitive but not optimal.** It scores 6.8 below EDF and
  4.8 below the nearest seed; the quality gate is cleared, but the scripted
  policy remains the ceiling.
- **The spatial result from 0040 stands.** Impact-only still fails; deadline
  awareness is the binding variable.
- **No new mechanic.** The fix is a baseline/representation change.

## Caveats

- Deterministic layouts; Q seed variance is small here.
- Hand-designed buckets for distance and deadline; no learned encoder.
- 500 training episodes and one state discretization.
- EDF uses known failure deadlines; it is a forecast-aware scripted baseline.
- The service action is atomic; continuous crew movement is not modeled.
- Not part of frozen `factory-v0.1`.

## Next

P1 now has a learned spatial-scheduling result. The remaining choices are:

1. **Multi-crew scheduling** only if the single-crew result is worth extending.
2. **P2:** multi-agent workers or larger/random layouts, per the coverage
   review.
3. **Consolidation:** package the post-0.1.2 P1 additions in a later release.

Do not add another scripted layer before choosing one of these scopes.

## Artifacts

- Env: `src/fabline/env/crew_schedule.py`
- Harness: `src/fabline/harness/crew_schedule.py`
- CLI: `python -m fabline crew-schedule`
- Raw results: `results/crew_schedule_q/` (ignored)
- Task card: `docs/tasks/crew-scheduling.md`
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
