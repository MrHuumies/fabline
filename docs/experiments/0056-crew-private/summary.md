# Experiment 0056 — Private crew views versus shared reports

- **Status:** complete (all gates pass)
- **Date:** 2026-11-23
- **Type:** P2 multi-agent communication experiment
- **Task:** `factory.power.crew-visibility.v1` (0052)
- **Mechanic:** private per-crew policies versus shared local/delayed views
- **Code:** `src/fabline/harness/crew_private.py`,
  `src/fabline/env/crew_visibility.py`
- **CLI:** `python -m fabline crew-private`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Private views cost real score, and shared reports recover most of it.** On
seeds 14000–14004, global oracle is **762.0**; shared-local oracle **614.0**;
shared-delayed60 oracle **648.0**; private best (greedy) **574.0**. Sharing
views beats private by **+40** at local and **+74** with the delayed report;
the report adds **+34** over local. Private nearest/aware collapse to **296.0**
with zero success because each crew sees only its own radius and has no
communication. All five gates pass.

## Conditions

| Condition | What each crew sees | Communication |
|---|---|---|
| global | full state | centralized |
| shared local | own radius; dispatcher sees union | instantaneous |
| shared delayed60 | own radius; dispatcher sees union with 60-tick report memory | delayed |
| private | own radius only | none |

## Data and seeds

- Pilot: seeds 13000–13002. Shared local 673; private greedy 570; private
  nearest/aware 440; global 720.
- Formal: seeds 14000–14004 (5 contiguous, all valid by reset-only check).
- No Q training.
- No dataset artifact.

## Results

| condition | policy | mean score | 95% CI | success |
|---|---|---:|---:|---:|
| global | nearest | 658.0 | [510.9, 746.0] | 0.80 |
| global | greedy | 762.0 | [756.0, 768.0] | 1.00 |
| global | aware | 638.0 | [552.0, 726.0] | 0.60 |
| global | **oracle** | **762.0** | [756.0, 768.0] | **1.00** |
| shared local | nearest | 518.0 | [326.0, 702.0] | 0.40 |
| shared local | greedy | 606.0 | [480.0, 731.0] | 0.60 |
| shared local | aware | 518.0 | [326.0, 702.0] | 0.40 |
| shared local | **oracle** | **614.0** | [490.0, 731.0] | **0.60** |
| shared delayed60 | nearest | 620.0 | [486.0, 726.0] | 0.60 |
| shared delayed60 | greedy | 640.0 | [482.0, 768.0] | 0.60 |
| shared delayed60 | aware | 620.0 | [486.0, 726.0] | 0.60 |
| shared delayed60 | **oracle** | **648.0** | [490.0, 768.0] | **0.60** |
| private | nearest | 296.0 | [180.0, 452.0] | 0.00 |
| private | greedy | **574.0** | [456.0, 690.0] | **0.40** |
| private | aware | 296.0 | [180.0, 452.0] | 0.00 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 shared-local gain | shared local ≥ private best + 10 | **pass**, +40 |
| H2 shared-delayed gain | shared delayed60 ≥ private best + 10 | **pass**, +74 |
| H3 private success | reported; expected below shared | **confirmed**, 0.40 vs 0.60 |
| H4 global/local ordering | global ≥ shared ≥ private | **pass**, 762 ≥ 648 ≥ 574 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Communication is worth 40–74 points.** Shared local beats private best by
  40; the delayed report adds another 34.
- **Private nearest/aware collapse.** Each crew independently chooses its nearest
  or earliest target; with only a local radius, both often fail to cover the
  critical bridge. The duplicate fallback (B noops) is a floor, not an optimal
  decentralized protocol.
- **Private greedy is surprisingly strong.** It reaches 574 and 0.40 success,
  but still trails shared local (606/0.60) and delayed (640/0.60).
- **The report is useful on this seed block.** Delayed60 beats local by 34,
  unlike the 3-seed pilot where they were equal; the formal 5 seeds resolve it.
- **The information axis is real.** The distributed layout plus visibility and
  reports produces a graded communication effect without Q.

## Caveats

- Five formal seeds; CIs are wide.
- Private collision handling is a simple B-noop fallback; a real decentralized
  protocol could do better.
- No explicit message budget; the delayed report is a memory window.
- Radius and report age are fixed at 16/60.
- Not part of frozen `factory-v0.1`.

## Next

1. **Message budget/one-report-per-crew** to test bandwidth rather than only
   age.
2. **A stronger decentralized protocol** than the duplicate fallback.
3. **Spread-layout triage** or a third crew for repeated failure.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Harness: `src/fabline/harness/crew_private.py`
- Env: `src/fabline/env/crew_visibility.py`
- CLI: `python -m fabline crew-private`
- Raw results: `results/crew-private/` (ignored)
- Task card: `docs/tasks/crew-visibility.md`
- Prior: [`../0052-crew-visibility/summary.md`](../0052-crew-visibility/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
