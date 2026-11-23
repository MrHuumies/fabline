# Experiment 0052 — Distributed-layout visibility and reports

- **Status:** complete (all gates pass)
- **Date:** 2026-11-23
- **Type:** P2 multi-agent information experiment
- **Mechanic:** per-crew visibility plus shared report age on the spread layout
  (RFC 0015, ADR 0026)
- **Task:** `factory.power.crew-visibility.v1` (debug/P2, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/crew_visibility.py`,
  `src/fabline/harness/crew_visibility.py`
- **CLI:** `python -m fabline crew-visibility`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The distributed layout makes local visibility useful, and a delayed report
recovers part of the gap.** On seeds 10000–10004, global oracle scores **778.0**;
local radius-16 oracle scores **680.0** (local cost **98**); delayed-30 is
identical to local; delayed-60 rises to **734.0** (**+54** over local, **56%**
of the global gap). Nearest and greedy show the same pattern (global 772/778,
local 650/656, delayed-60 728/734), and delayed-60 succeeds on 4/5 seeds.
All five gates pass.

## Environment

- 48×24 map, three gear lines spread across independent x bands and rows.
- One generator, capacity 48; per-crew Manhattan radius 16.
- Random crew-B base at least eight cells from A.
- Warnings 40; failures 90 (loop), 110 (small), 130 (large); recall 100.
- Existing pair action space; the mask excludes targets a crew neither sees nor
  has a report for.
- Shared report memory: age 0 (local), 30, or 60 ticks.
- Success ≥ 600.

## Data and seeds

- Pilot: seeds 0–2 on the spread layout.
- Formal evaluation: seeds 10000–10004 (5 contiguous, all valid by reset-only
  check; one episode each).
- No Q training; scripted and oracle baselines.
- No dataset artifact.

## Results

| condition | policy | mean score | 95% CI | success |
|---|---|---:|---:|---:|
| global | nearest | 772.0 | [760.0, 780.0] | 1.00 |
| global | greedy | 778.0 | [774.0, 780.0] | 1.00 |
| global | aware | 654.0 | [552.0, 750.0] | 0.60 |
| global | **oracle** | **778.0** | [774.0, 780.0] | **1.00** |
| local | nearest | 650.0 | [568.0, 730.0] | 0.60 |
| local | greedy | 656.0 | [568.0, 744.0] | 0.60 |
| local | aware | 666.0 | [573.0, 750.0] | 0.60 |
| local | **oracle** | **680.0** | [592.0, 768.0] | **0.60** |
| delayed30 | nearest | 650.0 | [568.0, 730.0] | 0.60 |
| delayed30 | greedy | 656.0 | [568.0, 744.0] | 0.60 |
| delayed30 | aware | 666.0 | [573.0, 750.0] | 0.60 |
| delayed30 | **oracle** | **680.0** | [592.0, 768.0] | **0.60** |
| delayed60 | nearest | 728.0 | [643.0, 778.0] | 0.80 |
| delayed60 | greedy | 734.0 | [646.0, 780.0] | 0.80 |
| delayed60 | aware | 666.0 | [573.0, 750.0] | 0.60 |
| delayed60 | **oracle** | **734.0** | [646.0, 780.0] | **0.80** |

Oracle actions (initial, replan): global `14/8, 11/0, 14/8, 14/8, 14/8`;
local `11/12, 11/0, 12/0, 12/0, 14/8`; delayed-60
`14/8, 11/0, 12/0, 14/8, 14/8`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 local cost | global oracle ≥ local + 10 | **pass**, +98 |
| H2 communication gain | delayed60 ≥ local + 10 | **pass**, +54 |
| H3 report-age sensitivity | delayed60 > delayed30 | **pass**, +54 |
| H4 delayed success | delayed60 oracle success ≥ 0.60 | **pass**, 0.80 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **The distributed layout fixes the binary visibility problem.** Radius 16 is
  a real information block: global nearest improves 122 points over local, and
  global oracle improves 98.
- **Report age is the active variable.** Age 30 is indistinguishable from local;
  age 60 recovers 56% of the gap. The 20-tick window between 30 and 60 is where
  the useful report arrives.
- **Scripted nearest/greedy follow the oracle.** Local 650/656, delayed-60
  728/734; the communication effect is not oracle-only.
- **Recall-aware does not use the report well.** It is 654 global, 666 local,
  and 666 delayed-60; its fixed earliest-bridge rule misses the assignment
  change.
- **The task is useful without Q.** The information cost and communication gain
  are visible in scripted baselines; a learned model is optional.

## Caveats

- Five formal seeds; CIs are wide.
- One fixed radius (16) and two report ages; the radius sweep is still
  stepwise on this layout.
- Manhattan visibility ignores walls/occlusion.
- The shared report is a memory window, not a message schedule or bandwidth
  limit.
- Private per-crew policies are not tested; the dispatcher still chooses the
  pair.
- Not part of frozen `factory-v0.1`.

## Next

1. **Repeated failure/multiple orphans on the twin-line layout.** The user
   priority; independent of visibility.
2. **Private per-crew policies or a message budget** for the visibility task.
3. **A radius/age sweep** on the spread layout if a smoother regime is needed.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0015, ADR 0026
- Env: `src/fabline/env/crew_visibility.py`
- Harness: `src/fabline/harness/crew_visibility.py`
- CLI: `python -m fabline crew-visibility`
- Raw results: `results/crew-visibility/` (ignored)
- Task card: `docs/tasks/crew-visibility.md`
- Pilot: [`../0051-visibility-pilot/summary.md`](../0051-visibility-pilot/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
