# Experiment 0016 — Power allocation control

- **Status:** complete
- **Date:** 2026-11-21
- **Type:** engineering milestone plus a debug control benchmark; not a
  pre-registered research experiment
- **World:** factory-0.1.0 + PowerConfig
- **Benchmark:** none; `factory-v0.1` unchanged

## Result in one paragraph

**Power allocation control works as a scheduling task.** With generator capacity
5, the furnace and assembler cannot run together. Fixed policies score 0–10;
a scripted alternator scores **130**, random scores **78.67**, and tabular Q
learns to score **116.67** with a 1.0 success rate. The task is easy for Q but
has the intended structure: build ingots, then assemble. The frozen benchmark,
macro control, and phase-1 power benchmark are unchanged.

## What was built

- `WorldState.power_priority` as canonical state, hashed only when nonzero.
- Allocation order: default id, furnace-first, or assembler-first.
- `PowerControlObservation` (18 features): power view plus assembler input,
  furnace output, craft progress, miner output, and score.
- `PowerAllocationEnv`: 3 actions, 500-tick gear line, capacity 5, decision
  interval 10, reward = score delta.
- Policies: default, furnace-first, assembler-first, scripted alternator,
  random, tabular Q.
- `fabline power-allocation` report.
- Tests for priority ordering, env step, observation, hash, policies, Q, runner.
- RFC 0005 / ADR 0015.

## Results

5 episodes per seed, seeds 0–2, capacity 5, success ≥ 100:

| policy | mean score | mean reward | success |
|---|---:|---:|---:|
| default | 0.00 [0.00, 0.00] | 0.00 | 0.00 |
| favor_furnace | 0.00 [0.00, 0.00] | 0.00 | 0.00 |
| favor_assembler | 10.00 [10.00, 10.00] | 10.00 | 0.00 |
| alternate | **130.00** [130.00, 130.00] | 130.00 | **1.00** |
| random | 78.67 [68.67, 87.33] | 78.67 | 0.13 |
| tabular Q | **116.67** [114.67, 119.02] | 116.67 | **1.00** |

## Interpretation

- **The trade-off is real.** Fixed furnace-first never assembles; fixed
  assembler-first drains the buffer and stalls. Alternation is necessary.
- **Q learns the scheduling pattern.** It reaches 116.67 and 1.0 success with
  100 training episodes. The gap to the scripted alternator is 13.33 score.
- **Random is a useful middle baseline.** It occasionally alternates and scores
  78.67, well above fixed policies.
- **Capacity matters.** At capacity 9 the line runs under every policy; at 5 the
  allocation problem is sharp. This is a scope condition, not a general claim.
- **The task is easy.** A hand-coded alternator and tabular Q both solve it. The
  value is the contract and the scheduling structure.

## Caveats

- One fixed gear line, generator layout, and budget.
- Priority is type-level, not per-entity.
- The scripted alternator is an oracle-style baseline.
- Faults are disabled; fault/power interaction is future work.
- The task is online-only; no dataset or replay is written.
- Small evaluation budget; CIs are wide.

## Next

1. **Power view-arrival:** treat the grid state as a new view over a production
   predictor; test insertion/retention.
2. **Fault + power interaction:** an allocation task where faults change demand
   and availability.
3. **Multi-agent workers or a second world:** the next larger expansion.

## Artifacts

- Env: `src/fabline/env/power_allocation.py`
- Harness: `src/fabline/harness/power_allocation.py`
- Observation: `PowerControlObservation` in `src/fabline/obs/power.py`
- Task card: `docs/tasks/power-allocation.md`
- Run: `make power-allocation`
- RFC/ADR: `docs/rfcs/0005-power-allocation.md`,
  `docs/decisions/0015-power-allocation.md`
