# Experiment 0055 — Three-bridge survivor triage

- **Status:** complete (all gates pass)
- **Date:** 2026-11-23
- **Type:** P2 repeated-failure/triage experiment
- **Mechanic:** three positive bridges, job failure at 100, two survivor jobs
  (RFC 0017, ADR 0028)
- **Task:** `factory.power.crew-triage.v1` (debug/P2, not in `factory-v0.1`)
- **Code:** `src/fabline/env/crew_replan.py`,
  `src/fabline/harness/crew_multi_orphan.py`
- **CLI:** `python -m fabline crew-triage`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Moving the failure to tick 100 makes the first assignment matter and creates
a real triage gap.** On seeds 12000–12004, the oracle scores **456.0** against
best-scripted greedy **378.0** (**+78**); nearest is **284.0**, recall-aware
**326.0**, and no-replan **92.0**. Oracle success is **1.00**; all scripted
sequential policies succeed on 4/5 seeds. The oracle sequences vary across seeds
(`[13,8,0]`, `[3,4,8]`, `[8,12,4]`, `[12,4,8]`, `[9,12,0]`), so the initial
pair and the two recovery choices both matter.

## Environment

- 32×16 twin-line layout, random crew-B base.
- Three positive bridges; internal `loop` = medium bridge.
- Warnings 40; failures 90/110/130.
- Job failure and B recall at 100; active jobs abort.
- A has two survivor jobs; all unresolved positive bridges are eligible.
- Reward: final production score; success ≥ 300.

## Data and seeds

- Pilot: seeds 0–4. Oracle 440/460/510/480/410; nearest mean 434; aware 374;
  greedy 332; no-replan ~100.
- Formal: seeds 12000–12004 (5 contiguous, all valid by reset-only check).
- No Q training; scripted and exhaustive two-job oracle.
- No dataset artifact.

## Results

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| noop | 90.0 | [84.0, 98.0] | 0.00 |
| single_edf | 90.0 | [84.0, 98.0] | 0.00 |
| nearest | 284.0 | [202.0, 338.0] | 0.80 |
| **greedy** | **378.0** | [290.0, 461.1] | **0.80** |
| recall-aware | 326.0 | [268.0, 394.0] | 0.80 |
| no-replan | 92.0 | [86.0, 98.0] | 0.00 |
| **oracle** | **456.0** | [424.0, 485.1] | **1.00** |

Per-seed scores:

| seed | nearest | greedy | aware | no-replan | oracle |
|---:|---:|---:|---:|---:|---:|
| 12000 | 310 | 310 | 300 | 100 | 490 |
| 12001 | 340 | 430 | 370 | 90 | 430 |
| 12002 | 350 | 220 | 220 | 80 | 400 |
| 12003 | 300 | 480 | 430 | 100 | 480 |
| 12004 | 120 | 450 | 310 | 90 | 480 |

Oracle sequences:

| seed | initial | replan1 | replan2 |
|---:|---:|---:|---:|
| 12000 | 13 | 8 | 0 |
| 12001 | 3 | 4 | 8 |
| 12002 | 8 | 12 | 4 |
| 12003 | 12 | 4 | 8 |
| 12004 | 9 | 12 | 0 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 oracle gap | oracle ≥ best scripted + 10 | **pass**, +78 |
| H2 coordination gain | best scripted ≥ single/noop + 10 | **pass**, +288 |
| H3 nearest sensitivity | nearest < oracle | **pass**, 284 < 456 |
| H4 oracle success | oracle success ≥ 0.60 | **pass**, 1.00 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **The initial assignment matters again.** Moving the failure to 100 lets some
  jobs finish; the oracle initial action varies from noop to specific pairs.
- **Triage order is non-trivial.** The oracle sequences differ across seeds;
  greedy/aware are inconsistent (greedy wins two seeds, fails one; aware is
  middle).
- **The oracle gap is large.** +78 over greedy, +172 over nearest, +364 over
  no-replan.
- **The task is a real repeated-failure/triage slice.** It complements 0052
  (local information) and 0054 (shallow sequential recovery).
- **No Q needed.** Scripted/oracle differences are the headline.

## Caveats

- Five formal seeds; CIs are wide.
- The internal `loop` role is the medium positive bridge; docs must state it.
- One survivor, two jobs, three bridges; one bridge remains unresolved.
- Some seeds are hard for every scripted policy (12004 nearest 120).
- Not part of frozen `factory-v0.1`.

## Next

1. **Private per-crew policies or message budgets** on the 0052 distributed
   visibility task.
2. **Spread-layout triage** or a third crew/replacement for repeated failure.
3. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0017, ADR 0028
- Env: `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_multi_orphan.py`
- CLI: `python -m fabline crew-triage`
- Raw results: `results/crew-triage/` (ignored)
- Task card: `docs/tasks/crew-triage.md`
- Prior: [`../0054-crew-multi-orphan/summary.md`](../0054-crew-multi-orphan/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
