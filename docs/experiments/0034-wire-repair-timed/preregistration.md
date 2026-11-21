# Experiment 0034 — Wire repair scheduling with repair time

- **Status:** complete (H3 fails; see [`summary.md`](summary.md))
- **Date:** 2026-11-21
- **Type:** P1 phase 1B timing experiment; follow-up to
  [`0033`](../0033-wire-repair/summary.md)
- **Task:** `factory.power.wire-repair.v1` version 0.2.0
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a 60-tick repair time create a scheduling trade, and can tabular Q learn
it?

In 0033 repair was instant. Here the crew spends 60 ticks on the selected wire
and the wire stays failed until the repair completes. The small and large bridge
faults overlap (ticks 150 and 180), so repairing the small bridge immediately at
150 and the large bridge at 210 can beat waiting for the large fault at 180.

## Pilot amendment note

Seeds 100–104 were used as a calibration pilot, not formal evidence. They gave:

- noop 75.2; repair-now 75.2 with one wasted repair;
- outage-ranked repair 219.2, success 1.00;
- wait-for-large 182.8, success 0.92;
- Q 219.2, success 1.00, zero wasted repairs.

Formal evaluation uses fresh seeds 200–204 and Q training seeds from 5000+.

## Environment

- Gear line, wired power, one generator, capacity 12.
- Faults at tick 50 (loop), 150 (small bridge), 180 (large bridge).
- Repair budget 2; repair time 60 ticks; one repair at a time.
- A repair is atomic: the crew spends 60 ticks, the wire stays failed until the
  end, and the reward is returned on the repair step.
- Reward: `restored * 10 * remaining/episode - 1 - 20 * 1[outage == 0]`.
- Outcome: final production score; success ≥ 150.
- Observation: 18 features; ranked slots.
- Actions: noop or repair slot 1–3.

## Baselines

| Baseline | Rule |
|---|---|
| noop | never repair |
| repair_now | repair the first failed slot |
| repair_largest | repair slot 1 only if outage > 0 |
| wait_large | noop until tick 180, then repair the largest positive outage |
| random | uniform legal action |
| tabular Q | 300 training layouts from seed 5000 + 1000 × Q seed |

## Gates

| Gate | Threshold |
|---|---|
| H1 repair gain | repair_largest ≥ noop + 100 |
| H2 impact-aware gain | repair_largest ≥ repair_now + 100 |
| H3 timing trade | repair_largest ≥ wait_large + 10 |
| H4 Q quality | Q ≥ 0.70 × repair_largest; Q success ≥ 0.60 |
| H5 budget discipline | Q wasted repairs ≤ 0.10 |

## Predictions

- Noop and repair-now stay near 75; repair-now wastes a repair on the loop and
  loses the repair-time window.
- Outage-ranked repair scores about 220 and succeeds on every seed.
- Waiting for the large fault scores about 180–190; starting the small bridge at
  150 is better under the 60-tick delay.
- Q learns the outage-ranked schedule and scores about 210–220 with zero wasted
  repairs.

## Kill criteria

- Repair time does not change the ranking or score by at least 10.
- repair_largest does not beat repair_now by 50.
- Q is below 0.60 × repair_largest or succeeds below 0.5.
- The result is dominated by one seed.
- The task requires post-hoc changes to the schedule, reward, or gates.

## Analysis plan

- Report score, bootstrap CI, control reward, repairs, wasted repairs, and
  success for every policy.
- Report Q per-seed scores.
- Report the pilot separately from the formal seeds.
- Do not tune the fault schedule, repair time, reward, or gates after the formal
  run.
- Keep `factory-v0.1` frozen.

## Artifacts

- Env: `src/fabline/env/wire_repair.py`
- Harness: `src/fabline/harness/wire_repair.py`
- CLI: `python -m fabline wire-repair --repair-ticks 60`
- Task card: `docs/tasks/power-wire-repair.md`
- Raw results: `results/wire_repair_timed/` (ignored)
- Summary: `docs/experiments/0034-wire-repair-timed/summary.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
