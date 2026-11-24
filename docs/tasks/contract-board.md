# Task card — gear-contract board

- **Task ID:** `factory.production.contract-board.v1`
- **Version:** 0.1.0
- **Status:** P3 debug task; formal run positive; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in recipe switch
- **Owner:** FABLINE
- **Date:** 2026-11-24

## Phenomenon

The factory offers three gear contracts with different targets, deadlines, and
rewards. The agent chooses one, then controls the fast/slow recipe. The best
feasible contract changes by board; a fixed contract or highest-reward policy
fails on some seeds.

## Contract

- **Observation:** 22 recipe features plus 19 board features.
- **Actions:** choose phase 0–2; control phase 0 fast, 1 slow.
- **Boards:** three seeded variants, three contracts each.
- **Line:** 16×8 gear scenario, 500 ticks, decision interval 10.
- **Recipe:** fast 2 ingots/12 ticks; slow 1 ingot/20 ticks.
- **Initial buffer:** seeded 0–6 ingots.
- **Reward:** contract reward if target met by deadline; success > 0.

## Metrics

- mean reward and success;
- selected contract;
- oracle gap;
- best-fixed-contract gap.

## Baselines

| Baseline | Rule |
|---|---|
| contract0/1/2 | fixed contract, buffer-aware recipe |
| highest_reward | highest reward contract, buffer-aware recipe |
| board_aware | highest reward with `target × 16 ≤ deadline` |
| random | random contract, buffer-aware recipe |
| oracle | best fixed contract per seed |

## Gates

| Gate | Threshold |
|---|---|
| H1 choice gain | board-aware ≥ best fixed contract + 10 |
| H2 oracle gap | board-aware within 10 of oracle |
| H3 success | board-aware success ≥ 0.60 |
| H4 frozen benchmark | unchanged |

## Known pitfalls

- Three fixed boards, not arbitrary contracts.
- Board-aware uses a 16-tick/gear feasibility rule.
- The recipe controller is buffer-aware; contract selection is the decision.
- Not part of `factory-v0.1`.

## Results (0074)

Seeds 45,000–45,004.

| policy | mean reward | success |
|---|---:|---:|
| contract0 | 36.0 | 0.60 |
| contract1 | 76.0 | 0.80 |
| contract2 | 90.0 | 0.60 |
| highest reward | 90.0 | 0.60 |
| **board-aware** | **112.0** | **1.00** |
| random | 32.0 | 0.40 |
| oracle | 122.0 | 1.00 |

H1 +22, H2 gap 10, H3 1.00, H4 pass. See
[`experiments/0074-contract-board`](../experiments/0074-contract-board/summary.md).

## Changelog

- 2026-11-24 — task card created; boards and gates defined.
- 2026-11-24 — formal run positive; board-aware 112 vs best fixed 90.
