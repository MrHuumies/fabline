# Pilot 0075 — Line-build planning

- **Status:** pilot negative; not promoted; exploratory code removed
- **Date:** 2026-11-24
- **Type:** P3 planning/world-model pilot
- **Task:** 12-tile build sequence on the existing control path
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Can CEM with a true or learned model plan a 12-tile line from the control
environment?

## Pilot

One seed (46,000), 12-tile path, 300 ticks, success ≥ 100:

| policy | score |
|---|---:|
| scripted 12-tile line | 140 |
| random | 0 |
| random shooting (200) | 0 |
| CEM true (40×8) | 0 |
| CEM learned (ridge) | 0 |

The scripted sequence is a valid line and scores 140. Random/CEM sequences
almost never form a valid line, and the score stays 0 until the entire path is
connected. A warm-start CEM based on the scripted line can match 140 but not
exceed it.

## Why it is not promoted

- **The reward is too sparse.** There is no partial credit until the line
  reaches the depot, so CEM has no gradient from 0 to a valid line.
- **The scripted line is a ceiling.** Planning can match it but not improve it.
- **The task is a construction puzzle, not a planning benchmark.** It does not
  distinguish true-simulator planning from a fixed script.

The exploratory planning harness, CLI, task card, and pre-registration were
removed. The next planning slice uses triage repair, where each repair yields
dense production credit and the greedy policy is below the oracle.

## Next

- Pivot to repair planning on the three-bridge triage task.
- Require dense score, a real oracle gap, and a learned model that is compared
  with a true-simulator planner.
