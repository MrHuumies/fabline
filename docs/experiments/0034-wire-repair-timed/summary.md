# Experiment 0034 — Wire repair scheduling with repair time

- **Status:** complete (H3 fails; timing effect present, order effect not robust)
- **Date:** 2026-11-21
- **Type:** P1 phase 1B timing experiment; follow-up to
  [`0033`](../0033-wire-repair/summary.md)
- **Task:** `factory.power.wire-repair.v1` version 0.2.0
- **Code:** `src/fabline/env/wire_repair.py`,
  `src/fabline/harness/wire_repair.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Repair time lowers production and Q learns the optimal schedule, but the
small-vs-large order trade does not replicate.** With 60-tick repairs and
overlapping small/large faults, outage-ranked repair scores **223.2** with
success 1.00, noop 73.2, repair-now 78.4 (one wasted repair), and Q **223.2**
with success 1.00 and zero wasted repairs. Waiting for the large fault scores
**220.8**, only 2.4 below outage-ranked repair, so **H3 fails** the +10
ordering gate. H1, H2, H4, and H5 pass. The robust timing effect is the drop from
instant repair (0033: 260) to 60-tick repair (223); the order in which the two
bridges are repaired is not distinguishable on the formal seeds.

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

## Formal data and seeds

- Evaluation: seeds 200–204, 5 episodes each = 25 episodes.
- Q training: 300 layouts from seed 5000 + 1000 × Q seed; disjoint.
- Pilot seeds 100–104 are reported separately and are not formal evidence.

## Results

| policy | mean score | 95% CI | reward | repairs | wasted | success |
|---|---:|---:|---:|---:|---:|---:|
| noop | 73.2 | [71.6, 75.2] | 0.0 | 0.00 | 0.00 | 0.00 |
| repair_now | 78.4 | [74.0, 83.6] | −16.2 | 2.00 | 1.00 | 0.00 |
| random | 78.4 | [74.0, 83.6] | −17.4 | 2.00 | 1.04 | 0.00 |
| repair_largest | **223.2** | [216.8, 230.0] | **22.0** | 2.00 | 0.00 | **1.00** |
| wait_large | 220.8 | [214.4, 226.6] | 19.9 | 2.00 | 0.00 | 1.00 |
| tabular Q | **223.2** | [216.8, 230.0] | 22.0 | 2.00 | 0.00 | **1.00** |

Q per-seed scores: 224, 224, 224, 222, 222; success 1.00 on every seed.

Pilot seeds 100–104: noop 75.2, repair_largest 219.2, wait_large 182.8, Q 219.2.
The pilot’s +36 order gap did not replicate.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 repair gain | repair_largest ≥ noop + 100 | **pass**, +150.0 |
| H2 impact-aware gain | repair_largest ≥ repair_now + 100 | **pass**, +144.8 |
| H3 timing trade | repair_largest ≥ wait_large + 10 | **fail**, +2.4 |
| H4 Q quality | Q ≥ 0.70 × repair_largest; success ≥ 0.60 | **pass**, 100%; 1.00 |
| H5 budget discipline | Q wasted ≤ 0.10 | **pass**, 0.00 |

## Interpretation

- **Repair time matters.** Instant outage-ranked repair scored 260 in 0033;
  the 60-tick crew scores 223. The production cost of delay is real.
- **The repair-order trade is not robust.** Waiting for the large fault is
  nearly as good as starting the small bridge at 150 on the formal seeds. The
  pilot’s large gap was layout-dependent.
- **Q learns the optimal policy.** It matches outage-ranked repair on every
  formal seed with zero wasted repairs.
- **The loop trap remains.** Repair-now and random waste a repair on the loop
  and fail the success threshold.
- **Do not tune the schedule to recover H3.** The order effect is not stable;
  a different fault spacing would be a new experiment.

## Caveats

- One deterministic fault schedule and one repair time (60 ticks).
- Ranked-slot action abstraction; wire identity is hidden.
- One generator and one inlet per consumer.
- Q matches a scripted outage-ranked policy; the task is easy for a
  restoration-aware heuristic.
- The order effect is seed-dependent; H3 fails.
- Production score is the outcome; the reward is time-weighted restored service.
- Not part of frozen `factory-v0.1`.

## Next

1. **Crew travel or spatial repair scheduling:** make the order depend on
   distance, not just impact.
2. **Multi-generator repair:** alternate paths and redundancy.
3. **Wire capacity/overload trips:** a second failure mechanism.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Env: `src/fabline/env/wire_repair.py`
- Harness: `src/fabline/harness/wire_repair.py`
- CLI: `python -m fabline wire-repair --repair-ticks 60`
- Raw results: `results/wire_repair_timed/` (ignored)
- Task card: `docs/tasks/power-wire-repair.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
