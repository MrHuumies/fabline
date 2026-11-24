# Experiment 0074 — Gear-contract board

- **Status:** preregistered (formal run pending)
- **Date:** 2026-11-24
- **Type:** P3 contract-selection experiment
- **Mechanic:** three-contract board plus recipe control (RFC 0028, ADR 0040)
- **Task:** `factory.production.contract-board.v1` (debug/P3, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/contract_board.py`,
  `src/fabline/harness/contract_board.py`
- **CLI:** `python -m fabline contract-board`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does an explicit contract choice create a real decision beyond the queue-aware
recipe policy?

## Pilot

Seeds 44,000–44,004:

| policy | mean reward |
|---|---:|
| contract0 | 48 |
| contract1 | 58 |
| contract2 | 60 |
| highest reward | 60 |
| random | 74 |
| **board-aware** | **94** |
| oracle | 104 |

Board-aware beats the best fixed contract by +34 and is within 10 of the oracle.
Selected contracts: board-aware `0,1,2,0,1`; oracle `0,2,2,0,1`.

## Design

- Three fixed boards, selected by `seed % 3`.
- Each board has three `(target, deadline, reward)` contracts.
- Choose phase: 3 actions; control phase: fast/slow.
- 16×8 gear line, 500 ticks, furnace 8, no power.
- Initial buffer seeded 0–6.
- Buffer-aware recipe controller; contract selection is the decision.
- Success: any reward.

## Data and seeds

- Pilot: 44,000–44,004.
- Formal: 45,000–45,004 (5 fresh seeds).
- No training; scripted baselines only.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| contract0/1/2 | fixed contract |
| highest_reward | highest reward |
| board_aware | highest reward with `target × 16 ≤ deadline` |
| random | random contract |
| oracle | best fixed contract per seed |

## Gates

| Gate | Threshold |
|---|---|
| H1 choice gain | board-aware ≥ best fixed + 10 |
| H2 oracle gap | board-aware within 10 of oracle |
| H3 success | board-aware success ≥ 0.60 |
| H4 frozen benchmark | unchanged |

## Predictions

- Board-aware 90–105; best fixed 50–65; oracle 100–110.
- H1 pass; H2 pass by 0–15; success 1.00.
- If H1 fails, the board is not a real choice; close contracts.

## Kill criteria

- H1 under +10: negative; close contracts.
- H2 gap over 10: report shallow; do not tune the feasibility rate after the
  formal block.
- No post-hoc board or rate tuning.

## Transparency note

The pilot used seeds 44,000–44,004. The formal block is fresh
45,000–45,004. The pilot's +34 is not a confirmation.
