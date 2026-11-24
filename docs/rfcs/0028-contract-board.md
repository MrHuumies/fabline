# Mechanic RFC 0028 — Gear-contract board

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-24
- **Related:** ADR 0040, RFC 0026, experiment 0074

## Summary

Add a seeded three-contract board on the gear line. The agent chooses one
contract at reset, then controls the fast/slow recipe. Contracts differ in
target, deadline, and reward; the feasible best contract changes by board.

## Motivation

The single revealed contract (0073) was not a decision: deadline-aware tied the
queue policy and random. The board adds an explicit choice. The control policy
is the queue-aware recipe from 0070; the new decision is which contract to
accept.

Pilot on seeds 44,000–44,004:

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

## Rules

- Three seeded boards, each with three `(target gears, deadline, reward)`
  contracts.
- Board 0: `(14,250,60), (20,350,100), (33,500,150)`.
- Board 1: `(16,200,50), (18,350,90), (30,500,150)`.
- Board 2: `(14,250,60), (24,350,100), (34,500,150)`.
- The agent chooses one contract, then controls fast/slow each interval.
- Reward: contract reward if the target is delivered by the deadline.
- Success: reward > 0.

## Observation and action impact

The observation is the 22-feature recipe view plus 19 board features (phase,
selection, active contract, and all three contract targets/deadlines/rewards).
The action space is 3 in the choose phase and 2 in the control phase.

## Data impact

- New task `factory.production.contract-board.v1`.
- Default recipe/world hashes unchanged; the task is opt-in.
- No new item.

## Tests

- Choose-then-control phase transition and mask.
- Observation shape.
- Board validation.
- Frozen benchmark regression.

## Decision

Accepted. See ADR 0040 and experiment 0074. If board-aware does not beat the
best fixed contract by 10 on fresh seeds, close the contract line.
