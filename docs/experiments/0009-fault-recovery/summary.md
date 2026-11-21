# Experiment 0009 — Repair action and fault recovery

- **Status:** complete
- **Date:** 2026-11-21
- **Type:** engineering milestone plus a debug control benchmark; not a
  pre-registered research experiment
- **World:** factory-0.1.0 + FaultConfig
- **Benchmark:** none; `factory-v0.1` unchanged

## What was built

- `repair(x, y)` as op 4 in the grid action contract; action mask shape is now
  `(5, 5, H, W, 4)`.
- `FactoryWorld.repair_entity`: clears fault, repair progress, and wear.
- `FaultRecoveryEnv`: two actions, `noop` and `repair`, with a repair cost.
- Policies: noop, repair-now, random, tabular Q.
- `fabline fault-recovery` report.
- Tests for the repair op, masks, index round-trip, env, policies, and runner.
- RFC 0002 and ADR 0012.

## Results

Fault recovery, 5 episodes per seed, seeds 0–2:

| policy | mean score | mean reward | mean repairs | success |
|---|---:|---:|---:|---:|
| noop | 230.00 [230.00, 230.00] | 230.00 | 0.00 | 0.00 |
| repair_now | 260.00 [260.00, 260.00] | 257.00 | 3.00 | 1.00 |
| random | 248.67 [243.33, 253.33] | 246.20 | 2.47 | 0.67 |
| tabular Q | 260.00 [260.00, 260.00] | 257.00 | 3.00 | 1.00 |

## Interpretation

- **Repair is worth it at this cost.** Repair-now gains 30 score over noop for
  three repairs (cost 3 total).
- **The task is easy.** Repair-now is optimal; tabular Q learns it. The value is
  the control loop and the action contract, not a hard RL benchmark.
- **The action change is additive.** The frozen `factory-v0.1` benchmark is
  action-free and its hashes are unchanged.
- **The existing control task is untouched.** Fault recovery is a separate
  two-action environment, not a change to line-building control.

## Caveats

- Only two actions; no diagnosis or choice of which entity to repair.
- One fixed gear line, threshold, and repair cost.
- Auto-repair still exists; repair accelerates recovery.
- Small evaluation budget; CIs are wide.

## Next

1. **Fault view-arrival:** treat thermal, vibration, and acoustic as separate
   views and test insertion/retention.
2. **Repair choices:** which entity, repair charge/budget, multi-tick repair.
3. **Stochastic faults and sensor noise.**
4. **Power or multi-agent mechanics.**

## Artifacts

- Task card: `docs/tasks/fault-recovery.md`
- RFC: `docs/rfcs/0002-fault-recovery.md`
- ADR: `docs/decisions/0012-repair-action.md`
- Code: `src/fabline/env/fault_recovery.py`,
  `src/fabline/harness/fault_recovery.py`
- Run: `make fault-recovery`
