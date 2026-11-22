# Experiment 0035 — Preventive wire maintenance

- **Status:** complete (all gates pass)
- **Date:** 2026-11-22
- **Type:** P1 phase 1C predictive-maintenance experiment
- **Mechanic:** degraded-wire warning and early repair (RFC 0008, ADR 0018)
- **Task:** `factory.power.wire-maintenance.v1` (debug/P1, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/preventive_wire.py`,
  `src/fabline/harness/preventive_wire.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**A warning makes a failure prediction actionable.** With a degraded-wire
warning at tick 60, a scheduled failure at 220, and a 140-tick repair,
preventive repair scores **260** and prevents the outage on every seed.
Reactive repair scores **185.6**, noop and late repair score **113.6**, and
tabular Q scores **260** with prevention on every seed. All five gates pass.
Starting early is worth **+74.4** over waiting for failure and **+146.4** over
noop; starting 40 ticks late aborts the job and is worth only noop. This is the
first P1 control task where a prediction has a direct, timing-sensitive action.

## Environment

- Gear line, wired power, one generator, capacity 12.
- Target: the wire with the largest positive outage.
- Warning at tick 60; failure at tick 220; repair takes 140 ticks.
- Repair budget 1; repair action is atomic.
- A preventive repair that completes before failure cancels it.
- A late repair aborts when the wire fails mid-job; the budget is spent.
- Reward:
  - preventive: `outage * 15 - 1`;
  - reactive: `outage * 10 * remaining/episode - 1`;
  - aborted: 0.
- Outcome: final production score; success ≥ 150.
- Observation: 8 features — tick, score, outage, degraded, failed,
  time-to-failure, budget, repaired.

## Data and seeds

- Evaluation: seeds 300–304, 5 episodes each = 25 episodes.
- Q training: 200 layouts from seed 6000 + 500 × Q seed.
- Layouts without a single-wire bridge are skipped in training; they have no
  preventive task.
- No dataset artifact.

## Results

| policy | mean score | 95% CI | reward | prevented | aborted | success |
|---|---:|---:|---:|---:|---:|---:|
| noop | 113.6 | [110.0, 117.2] | 0.0 | 0.0 | 0.0 | 0.00 |
| late | 113.6 | [110.0, 117.2] | 0.0 | 0.0 | 1.0 | 0.00 |
| reactive | 185.6 | [181.6, 190.0] | 12.0 | 0.0 | 0.0 | 1.00 |
| random | 231.2 | [207.2, 250.4] | 57.4 | 0.8 | 0.2 | 0.80 |
| preventive | **260.0** | [260.0, 260.0] | **68.6** | **1.0** | 0.0 | **1.00** |
| tabular Q | **260.0** | [260.0, 260.0] | **68.6** | **1.0** | 0.0 | **1.00** |

Q per-seed score: 260 on all five seeds, with prevention and success 1.00.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 prevention gain | preventive ≥ noop + 100 | **pass**, +146.4 |
| H2 prediction value | preventive ≥ reactive + 30 | **pass**, +74.4 |
| H3 timing value | preventive ≥ late + 100 | **pass**, +146.4 |
| H4 Q quality | Q ≥ 0.85 × preventive; success ≥ 0.90 | **pass**, 100%; 1.00 |
| H5 budget discipline | Q prevented ≥ 0.90 | **pass**, 1.00 |

## Interpretation

- **The prediction is now actionable.** A degraded warning gives the agent a
  repair target before the outage; the timing determines whether the job
  finishes.
- **Early repair is worth more than fast reactive repair.** Reactive repair
  restores the wire but loses the 140-tick downtime window.
- **Late starts are punished.** Starting 40 ticks after the warning aborts at
  the failure tick, spends the budget, and scores like noop.
- **Q learns the warning policy.** It repairs at the warning on every seed and
  matches the scripted preventive baseline.
- **This answers the design gap in 0033/0034.** Those tasks only repaired
  failed wires; a prediction could rank failures but could not prevent one.

## Caveats

- The warning is perfect: no false positives, false negatives, or noise.
- One watched wire and one repair job; multi-wire preventive scheduling is a
  follow-up.
- One generator; no crew travel or spatial repair time.
- The preventive reward is a shaped objective; production score is the outcome.
- Random already scores well because the warning is deterministic and the
  action space is two actions.
- Layouts without a single-wire bridge are skipped.
- Not part of frozen `factory-v0.1`.

## Next

1. **Noisy warnings:** precision/recall trade-offs and false-alarm cost.
2. **Multi-wire preventive scheduling:** which warning to act on first under a
   budget.
3. **Preventive maintenance for machine wear:** the same pattern on the normal
   fault mechanic.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0008, ADR 0018
- Env: `src/fabline/env/preventive_wire.py`
- Harness: `src/fabline/harness/preventive_wire.py`
- CLI: `python -m fabline wire-maintenance`
- Raw results: `results/wire_maintenance/` (ignored)
- Task card: `docs/tasks/power-wire-maintenance.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
