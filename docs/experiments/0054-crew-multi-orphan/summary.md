# Experiment 0054 — Sequential survivor dispatch

- **Status:** complete (H1, H2, H3, H5 pass; H4 shallow, no oracle gap)
- **Date:** 2026-11-23
- **Type:** P2 repeated-failure experiment
- **Mechanic:** double job failure plus sequential survivor recovery (RFC 0016,
  ADR 0027)
- **Task:** `factory.power.crew-multi-orphan.v1` (debug/P2, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/crew_replan.py`,
  `src/fabline/harness/crew_multi_orphan.py`
- **CLI:** `python -m fabline crew-multi-orphan`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Sequential survivor dispatch turns the one-shot collapse into a real recovery
task, but the task is shallow.** On seeds 11000–11004, both initial jobs abort
at tick 80 and leave two orphans. Crew A's two sequential recoveries lift the
score from no-replan **118.0** to greedy/recall-aware/oracle **460.0**
(**+342**). Nearest reaches **438.0**; success is 1.00 for every sequential
policy. The oracle sequence is the same on every seed, `[11, 12, 8]`, and greedy
matches it: the task demonstrates repeated recovery, not hard triage.

## Environment

- 32×16 twin-line layout, random crew-B base.
- Warnings 40; failures 90/110/130.
- Recall and job failure both at 80; both initial jobs abort.
- A has two survivor jobs; each starts from its current position.
- Action mask: noop or any remaining positive orphan.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 0–4. Greedy/aware/oracle 470–500; nearest 420–500; no-replan
  100–120.
- Formal: seeds 11000–11004 (5 contiguous, all valid by reset-only check).
- No Q training; scripted and exhaustive two-job oracle.
- No dataset artifact.

## Results

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| noop | 118.0 | [114.0, 120.0] | 0.00 |
| single_edf | 118.0 | [114.0, 120.0] | 0.00 |
| nearest | 438.0 | [412.0, 466.0] | 1.00 |
| **greedy** | **460.0** | [434.0, 482.0] | **1.00** |
| **recall-aware** | **460.0** | [434.0, 482.0] | **1.00** |
| no-replan | 118.0 | [114.0, 120.0] | 0.00 |
| **oracle** | **460.0** | [434.0, 482.0] | **1.00** |

Per-seed scores:

| seed | nearest | greedy | aware | no-replan | oracle |
|---:|---:|---:|---:|---:|---:|
| 11000 | 440 | 460 | 460 | 120 | 460 |
| 11001 | 440 | 460 | 460 | 120 | 460 |
| 11002 | 400 | 410 | 410 | 110 | 410 |
| 11003 | 420 | 480 | 480 | 120 | 480 |
| 11004 | 490 | 490 | 490 | 120 | 490 |

Oracle sequences: `[11, 12, 8]` on every seed — small A / large B initially,
then recover large, then small.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 recovery gain | best sequential ≥ no-replan + 10 | **pass**, +342 |
| H2 coordination gain | best sequential ≥ single/noop + 10 | **pass**, +342 |
| H3 nearest sensitivity | nearest < best sequential | **pass**, 438 < 460 |
| H4 oracle gap | report oracle vs best scripted; no hard gate | **shallow**, 0 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Sequential recovery is real.** One survivor can recover both orphans; the
  second decision is worth 342 points over no-replan.
- **Triage is easy.** The highest-outage bridge first, then the other, is
  optimal on every seed; greedy and recall-aware match oracle. The task does
  not test a hard ordering trade.
- **Nearest is separated.** It loses 22 points on average because its initial
  pair/order is not always the greedy order, but it still succeeds.
- **This is a positive but shallow repeated-failure slice.** Keep it as a
  debug/P2 recovery task, not a headline benchmark.
- **No Q needed.** The mechanic is visible in scripted baselines.

## Caveats

- Five formal seeds; CIs are wide.
- Both jobs fail at the same tick; no repeated failure over time.
- Two orphans, one survivor, two jobs; no third crew or replacement.
- Greedy matches oracle; no assignment gap.
- Not part of frozen `factory-v0.1`.

## Next

1. **Asymmetric multi-orphan trade-off:** make order matter by varying distances
   and deadlines, or by adding a third orphan with a tighter deadline.
2. **Third crew/replacement:** test handoff and parallel recovery.
3. **Private visibility on the distributed layout:** message budgets or
   per-crew policies, now that 0052 has a useful local block.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0016, ADR 0027
- Env: `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_multi_orphan.py`
- CLI: `python -m fabline crew-multi-orphan`
- Raw results: `results/crew-multi-orphan/` (ignored)
- Task card: `docs/tasks/crew-multi-orphan.md`
- Prior pilot: [`../0053-multi-orphan-pilot/summary.md`](../0053-multi-orphan-pilot/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
