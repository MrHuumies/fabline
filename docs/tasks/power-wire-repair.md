# Task card — wire repair control

- **Task ID:** `factory.power.wire-repair.v1`
- **Version:** 0.1.0
- **Status:** P1 debug task; formal run complete; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

A wired power grid has failed segments. A repair crew can fix one segment per
decision interval, under a limited budget. Repairing a bridge restores a
downstream component; repairing a loop segment restores nothing. The agent must
prioritize repairs by restoration impact and save budget for the large fault.

## Contract

- **Observation:** 18 features — tick, score, budget, failed count, max/total
  outage, and three ranked slots with outage, bridge flag, age, and existence.
- **Actions:** noop; repair slot 1; repair slot 2; repair slot 3.
- **Budget:** 2 repairs per episode.
- **Faults:** tick 50 loop, tick 150 small bridge, tick 250 large bridge.
- **Reward:** `restored_consumers * 10 - 1 - 20 * 1[outage == 0]`.
- **Outcome:** final production score; success ≥ 150.
- **Episode:** 500 ticks; decision interval 10.
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
| random | uniform legal action |
| tabular Q | 300 training layouts, ε-greedy |

## Gates

| Gate | Threshold |
|---|---|
| H1 repair gain | repair_largest ≥ noop + 100 |
| H2 impact-aware gain | repair_largest ≥ repair_now + 100 |
| H3 Q quality | Q ≥ 0.70 × repair_largest |
| H4 Q success | ≥ 0.60 |
| H5 budget discipline | Q wasted ≤ 0.10 |

## Results (0033)

Seeds 100–104, 5 episodes each; budget 2; success ≥ 150.

| policy | mean score | wasted | success |
|---|---:|---:|---:|
| noop | 79.2 | 0.00 | 0.00 |
| repair_now | 121.6 | 1.00 | 0.00 |
| random | 118.4 | 1.00 | 0.00 |
| repair_largest | **260.0** | 0.00 | **1.00** |
| tabular Q | 212.0 | 0.00 | 0.68 |

All five gates pass. Q per-seed scores: 260, 178, 242, 232, 148. See
[`experiments/0033-wire-repair`](../experiments/0033-wire-repair/summary.md).

## Known pitfalls

- **The loop is a trap.** Repair-now and random waste a repair on it.
- **Production score is not the reward.** The reward is restored service; the
  score is the outcome metric.
- **Slots are ranked by impact.** The action abstraction hides wire identity;
  this is a prioritization task, not end-to-end graph control.
- **Training/evaluation seeds must be disjoint.** Q trains from seed 2000+;
  evaluation uses 100–104.
- **One generator and one inlet per consumer.** Multi-generator repair is a
  follow-up.
- **Repair is instant.** Repair time and crew travel are not modeled.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-21 — card created; environment, reward, and gates preregistered.
- 2026-11-21 — formal run: all gates pass; Q 212 vs repair_largest 260.
