# Task card — wire repair control

- **Task ID:** `factory.power.wire-repair.v1`
- **Version:** 0.2.0 (timed repair); 0.1.0 instant is historical
- **Status:** P1 debug task; timed formal run complete; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

A wired power grid has failed segments. A repair crew can fix one segment per
action under a limited budget. Repairing a bridge restores a downstream
component; repairing a loop segment restores nothing. With repair time, the wire
stays failed while the crew works, so the repair order also affects production.

## Contract (0.2.0)

- **Observation:** 18 features — tick, score, budget, failed count, max/total
  outage, and three ranked slots with outage, bridge flag, age, and existence.
- **Actions:** noop; repair slot 1; repair slot 2; repair slot 3.
- **Budget:** 2 repairs per episode.
- **Repair time:** 60 ticks; a repair is atomic and the wire stays failed until
  completion.
- **Faults:** tick 50 loop, tick 150 small bridge, tick 180 large bridge.
- **Reward:** time-weighted restored consumers
  `restored * 10 * remaining/episode - 1 - 20 * 1[outage == 0]`.
- **Outcome:** final production score; success ≥ 150.
- **Episode:** 500 ticks; decision interval 10 for noop.
- **Power:** one generator; capacity 12; wired topology; redundancy 2.

## Metrics

- mean production score (bootstrap CI);
- mean control reward;
- mean repairs and wasted repairs;
- success rate.

## Baselines

| Baseline | Rule |
|---|---|
| noop | never repair |
| repair_now | repair the first failed slot |
| repair_largest | repair slot 1 only if outage > 0 |
| wait_large | noop until tick 180, then repair the largest positive outage |
| random | uniform legal action |
| tabular Q | 300 training layouts, ε-greedy, coarse outage state |

## Results

### 0034 — timed repair (current)

Seeds 200–204, 5 episodes each; success ≥ 150.

| policy | mean score | wasted | success |
|---|---:|---:|---:|
| noop | 73.2 | 0.00 | 0.00 |
| repair_now | 78.4 | 1.00 | 0.00 |
| random | 78.4 | 1.04 | 0.00 |
| repair_largest | **223.2** | 0.00 | **1.00** |
| wait_large | 220.8 | 0.00 | 1.00 |
| tabular Q | **223.2** | 0.00 | **1.00** |

H1, H2, H4, H5 pass; **H3 fails**: the +10 order gap is only +2.4. Repair time
lowers production (instant 0033: 260 → timed 223), but the small-vs-large order
is not robust. See
[`experiments/0034-wire-repair-timed`](../experiments/0034-wire-repair-timed/summary.md).

### 0033 — instant repair (historical)

Seeds 100–104: noop 79.2, repair_now 121.6 (wasted 1), repair_largest 260,
Q 212 (success 0.68). All gates passed. See
[`experiments/0033-wire-repair`](../experiments/0033-wire-repair/summary.md).

## Gates

| Gate | 0034 threshold | Result |
|---|---|---|
| H1 repair gain | repair_largest ≥ noop + 100 | pass |
| H2 impact-aware gain | repair_largest ≥ repair_now + 100 | pass |
| H3 timing trade | repair_largest ≥ wait_large + 10 | **fail** |
| H4 Q quality | Q ≥ 0.70 × repair_largest; success ≥ 0.60 | pass |
| H5 budget discipline | Q wasted ≤ 0.10 | pass |

## Known pitfalls

- **The loop is a trap.** Repair-now and random waste a repair on it.
- **The repair-order effect is not robust.** Waiting for the large fault is
  nearly tied on formal seeds; do not tune the fault spacing to recover it.
- **Production score is not the reward.** The reward is time-weighted restored
  service; the score is the outcome.
- **Slots are ranked by impact.** This is a prioritization task, not end-to-end
  graph control.
- **Training/evaluation seeds must be disjoint.** Q trains from seed 5000+;
  evaluation uses 200–204.
- **One generator and one inlet per consumer.** Multi-generator repair is a
  follow-up.
- **Repair is atomic.** Crew travel and spatial scheduling are not modeled.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-21 — card created; environment, reward, and gates preregistered.
- 2026-11-21 — instant formal run: all gates pass; Q 212 vs repair_largest 260.
- 2026-11-21 — timed version 0.2.0: Q matches repair_largest 223.2; H3 order
  effect fails.
