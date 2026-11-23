# Experiment 0066 — Asymmetric repair-cost triage

- **Status:** complete (negative; H1 fails, cost axis retired)
- **Date:** 2026-11-23
- **Type:** P2 asymmetric-triage experiment
- **Mechanic:** role-specific repair durations on the three-bridge survivor
  triage (RFC 0024, ADR 0035)
- **Task:** `factory.power.crew-triage-costs.v1` (debug/P2, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/multi_crew.py`,
  `src/fabline/env/crew_replan.py`,
  `src/fabline/harness/crew_multi_orphan.py`
- **CLI:** `python -m fabline crew-costs`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The pilot's cost gap did not replicate on fresh seeds.** On seeds
25000–25004, greedy scores **386.0** and the exhaustive oracle also scores
**386.0**; the gap is **0**. Greedy matches the oracle on every seed
(`380, 380, 400, 380, 390`). Aware is 346.0, nearest 352.0, single 100.0, noop
84.0, and no-replan 102.0. H1 fails; H2, H4, and H5 pass. Repair-cost asymmetry
alone does not create a new triage order beyond the existing outage-per-service
rule. The positive pilot (+52 on 0055 seeds) was optimistic.

## Pilot vs formal

Pilot (0055 seeds 12000–12004):

| policy | mean score | success |
|---|---:|---:|
| greedy | 336.0 | 0.80 |
| aware | 334.0 | 0.80 |
| oracle | 388.0 | 1.00 |

Formal (fresh seeds 25000–25004):

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| noop | 84.0 | [76.0, 90.0] | 0.00 |
| single_edf | 100.0 | [88.0, 111.0] | 0.00 |
| nearest | 352.0 | [328.0, 376.0] | 1.00 |
| **greedy** | **386.0** | [380.0, 394.0] | **1.00** |
| aware | 346.0 | [294.0, 388.0] | 0.80 |
| no-replan | 102.0 | [92.0, 112.0] | 0.00 |
| **oracle** | **386.0** | [380.0, 394.0] | **1.00** |

Per-seed greedy and oracle are identical: `380, 380, 400, 380, 390`.

## Environment

- 32×16 twin-line layout, three positive bridges.
- Roles: `loop` = medium, `small` = smallest outage, `large` = largest.
- Warnings 40; failures 90/110/130; failure and B recall 100.
- Repair: loop 20, small 40, large 100; travel 2 × Manhattan.
- Initial 16 A/B pairs; A gets two survivor jobs; all positive bridges eligible.
- Reward: final production score; success ≥ 300.
- Observation: 31 features (25 crew-replan + 6 service-time features).

## Oracle sequences

| seed | initial | replan 1 | replan 2 |
|---:|---:|---:|---:|
| 25000 | 4 | 12 | 8 |
| 25001 | 4 | 12 | 8 |
| 25002 | 1 | 12 | 8 |
| 25003 | 1 | 12 | 8 |
| 25004 | 1 | 12 | 8 |

Greedy chooses the same sequence on every seed, so the cost asymmetry does not
move it off the optimum.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 oracle gap | oracle ≥ best scripted + 10 | **fail**, +0 |
| H2 coordination | best scripted ≥ single/noop + 10 | **pass**, +286 |
| H3 cost sensitivity | best scripted below oracle | **fail**, equal |
| H4 oracle success | ≥ 0.60 | **pass**, 1.00 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Greedy already accounts for repair cost.** It ranks by outage per service
  time, and service time includes the role-specific repair duration. Making the
  large repair slower changes the numbers but not the ranking on these seeds.
- **The pilot was optimistic.** The +52 gap on the 0055 seeds came from seeds
  where the initial pair or survivor order was harder; fresh seeds collapse it.
  This is the same pilot/formal lesson as 0042/0044.
- **Cost asymmetry is not a new coordination axis.** It is a parameter change to
  an existing rule, not a decision that the current policies miss.
- **Do not tune the cost tuple.** A larger gap could be manufactured by changing
  20/40/100 after seeing the formal block; that would be post-hoc.

## Caveats

- Five formal seeds; CIs are wide for aware.
- One layout and one cost tuple.
- The pilot reused 0055 seeds; it is not a confirmation.
- The task adds service-time observation features, but no learned baseline was
  trained.
- Not part of frozen `factory-v0.1`.

## Next

1. **Retire the asymmetric-cost axis.** The P2 review's asymmetric-triage gap is
   answered negatively for repair cost.
2. **Random topology** is the remaining P2 layout gap; it is a larger mechanic.
3. If random topology does not add a decision, the P2 multi-agent line is near
   its practical ceiling; move to P3.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0024, ADR 0035
- Env: `src/fabline/env/multi_crew.py`, `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_multi_orphan.py`
- CLI: `python -m fabline crew-costs`
- Raw results: `results/crew-costs/` (ignored)
- Task card: [`../../tasks/crew-triage-costs.md`](../../tasks/crew-triage-costs.md)
- Prior: [`../0055-crew-triage/summary.md`](../0055-crew-triage/summary.md)
