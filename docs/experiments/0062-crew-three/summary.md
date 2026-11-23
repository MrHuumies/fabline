# Experiment 0062 — Three-crew initial assignment

- **Status:** complete (all gates pass)
- **Date:** 2026-11-23
- **Type:** P2 third-crew/coverage experiment
- **Mechanic:** 64-action three-crew assignment (RFC 0020, ADR 0031)
- **Task:** `factory.power.crew-three.v1` (debug/P2, not in `factory-v0.1`)
- **Code:** `src/fabline/env/three_crew.py`,
  `src/fabline/harness/crew_three.py`
- **CLI:** `python -m fabline crew-three`
- **Pre-registration:** [`preregistration.md`](preregistration.md) (see the
  transparency note on timing)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**A full third crew adds a large coverage gain.** On seeds 22000–22004, three
crews with greedy assignment score **476.0** against the two-crew oracle
**320.0** (**+156**); three-crew nearest is **400.0**, three-aware **390.0**, and
the three-crew oracle **520.0** (**+44** over greedy, success 1.00). Single-crew
EDF is **110.0** and noop **104.0**. All five gates pass. The third crew is a
real coverage axis; scripted nearest/aware leave a 76–120 point gap to oracle.

## Environment

- 32×16 twin-line, three positive bridges.
- Crews A (depot), B and C (seeded random bases at least eight cells from A and
  each other).
- Warning 40; failures 100/130/160.
- One-shot 64-action assignment; duplicate positive targets masked.
- Travel = 2 × Manhattan; service 40 ticks.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 21000–21002. The first deadline set was unsolvable; the final
  100/130/160 set was used.
- Formal: seeds 22000–22004 (5 contiguous, all valid by reset-only check).
- No Q training.
- No dataset artifact.

## Results

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| noop | 104.0 | [90.0, 114.0] | 0.00 |
| single_edf | 110.0 | [92.0, 127.0] | 0.00 |
| two nearest | 282.0 | [194.0, 336.0] | 0.00 |
| two greedy | 320.0 | [306.0, 336.0] | 0.00 |
| **two oracle** | **320.0** | [306.0, 336.0] | **0.00** |
| three nearest | 400.0 | [312.0, 486.0] | 0.40 |
| **three greedy** | **476.0** | [388.0, 520.0] | **0.80** |
| three aware | 390.0 | [302.0, 478.0] | 0.40 |
| **three oracle** | **520.0** | [520.0, 520.0] | **1.00** |

Oracle actions:

- two-crew: `22000:12`, `22001:28`, `22002:52`, `22003:28`, `22004:12`.
- three-crew: `22000:45`, `22001:27`, `22002:39`, `22003:27`, `22004:45`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 third-crew gain | three best ≥ two best + 10 | **pass**, +156 |
| H2 coordination | three best ≥ single/noop + 10 | **pass**, +366 |
| H3 oracle gap | three oracle ≥ three best + 10 | **pass**, +44 |
| H4 oracle success | three oracle success ≥ 0.60 | **pass**, 1.00 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Third-crew coverage is real.** Two crews can cover at most two of three
  bridges; three crews reach the full score.
- **The task is not saturated for learned/assignment quality.** Greedy is 44
  points below oracle; nearest and aware are 76–120 below.
- **Three greedy is the strongest scripted policy.** It reaches 476/0.80; the
  oracle action varies across seeds, so assignment matters.
- **The task is a one-shot coverage test, not a failure/replanning test.**
  Recall and sequential recovery remain separate tasks (0054/0055).
- **The 64-action space is manageable** with scripted matching and an exhaustive
  oracle; no Q is needed.

## Caveats

- Five formal seeds; CIs are wide.
- One-shot only; no recall, no replanning, no crew failure.
- C's base and the widened 100/130/160 deadlines are scope choices.
- Three-crew nearest/aware are weaker than greedy; the oracle gap is the
  non-saturated signal.
- The preregistration file was written after the formal run; see its
  transparency note.
- Not part of frozen `factory-v0.1`.

## Next

1. **Three crews plus recall/replanning.** Combine the full third crew with the
   0055 triage contract.
2. **Larger action spaces / four bridges.** Test scaling and assignment.
3. **Learned assignment** on the 64-action task, if a non-scripted baseline is
   needed.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0020, ADR 0031
- Env: `src/fabline/env/three_crew.py`
- Harness: `src/fabline/harness/crew_three.py`
- CLI: `python -m fabline crew-three`
- Raw results: `results/crew-three/` (ignored)
- Task card: `docs/tasks/crew-three.md`
- Prior: [`../0061-pair-policy-pilot/summary.md`](../0061-pair-policy-pilot/summary.md)
- Coverage review: [`../../coverage-review-p2.md`](../../coverage-review-p2.md)
