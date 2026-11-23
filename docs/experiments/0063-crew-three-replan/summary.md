# Experiment 0063 — Three-crew recall and recovery

- **Status:** complete (H1, H2, H4, H5 pass; H3 shallow)
- **Date:** 2026-11-23
- **Type:** P2 third-crew/recovery experiment
- **Mechanic:** 64-action initial dispatch plus 16-action A/C recovery after B
  recall (RFC 0021, ADR 0032)
- **Task:** `factory.power.crew-three-replan.v1` (debug/P2, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/three_crew_replan.py`,
  `src/fabline/harness/crew_three_replan.py`
- **CLI:** `python -m fabline crew-three-replan`
- **Pre-registration:** [`preregistration.md`](preregistration.md) (see the
  transparency note)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The third crew absorbs the recall, but recovery is close to the scripted
ceiling.** On seeds 24000–24004, three greedy scores **516.0** against no-replan
**360.0** (**+156**); three nearest **500.0**, three aware **490.0**, single
**122.0**, and oracle **520.0**. The oracle gap is only **+4**, so H3 is
shallow. All recovery policies succeed on every seed. The task demonstrates
third-crew recovery, not a hard assignment decision.

## Environment

- 32×16 twin-line, three positive bridges.
- A at depot; B and C on seeded random bases.
- Warning 40; failures 100/130/160; recall 100.
- Initial 64-action A/B/C dispatch; B's unfinished job aborts.
- Recovery 16-action A/C pair; duplicate positive targets masked.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 23000–23002.
- Formal: seeds 24000–24004 (5 contiguous, all valid by reset-only check).
- No Q training.
- No dataset artifact.

## Results

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| noop | 110.0 | [104.0, 116.0] | 0.00 |
| single_edf | 122.0 | [116.0, 132.0] | 0.00 |
| three nearest | 500.0 | [478.0, 518.0] | 1.00 |
| **three greedy** | **516.0** | [508.0, 520.0] | **1.00** |
| three aware | 490.0 | [472.0, 508.0] | 1.00 |
| three no-replan | 360.0 | [216.0, 480.0] | 0.40 |
| **oracle** | **520.0** | [520.0, 520.0] | **1.00** |

Oracle actions (initial, recovery): `24000:[57,0]`, `24001:[12,6]`,
`24002:[1,11]`, `24003:[4,11]`, `24004:[18,3]`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 recovery gain | three best ≥ no-replan + 10 | **pass**, +156 |
| H2 coordination | three best ≥ single/noop + 10 | **pass**, +394 |
| H3 oracle gap | report oracle vs three best | **shallow**, +4 |
| H4 oracle success | oracle success ≥ 0.60 | **pass**, 1.00 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **The third crew absorbs the recall.** No-replan loses 156 points; the A/C
  recovery pair restores full coverage.
- **Triage is easy.** Three greedy is 4 points below oracle; nearest/aware are
  20–30 below. The recovery pair plus initial dispatch has a clear scripted
  ceiling.
- **The task is positive but shallow.** The value is coverage and recovery, not
  a hard assignment gap.
- **B's recall sometimes costs nothing.** If B completed before 100, the task is
  just the one-shot three-crew coverage; no-replan still scores 520 on those
  seeds.
- **No Q needed.** Scripted/oracle comparisons carry the result.

## Caveats

- Five formal seeds; CIs are wide for no-replan.
- One recall, one A/C pair; no sequential survivor work.
- B's base and deadlines are scope choices.
- The preregistration file was written after the formal run; see its note.
- Not part of frozen `factory-v0.1`.

## Next

1. **Sequential A/C recovery** with more than one pair, or a larger action /
   four-bridge task.
2. **Three crews plus visibility/communication** on the distributed layout.
3. If no new gap appears, the three-crew line is near its practical ceiling.

## Artifacts

- Mechanic: RFC 0021, ADR 0032
- Env: `src/fabline/env/three_crew_replan.py`
- Harness: `src/fabline/harness/crew_three_replan.py`
- CLI: `python -m fabline crew-three-replan`
- Raw results: `results/crew-three-replan/` (ignored)
- Task card: `docs/tasks/crew-three-replan.md`
- Prior: [`../0062-crew-three/summary.md`](../0062-crew-three/summary.md)
- Coverage review: [`../../coverage-review-p2.md`](../../coverage-review-p2.md)
