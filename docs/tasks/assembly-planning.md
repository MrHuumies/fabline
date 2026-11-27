# Task card — assembly-edge planning

- **Task ID:** `factory.assembly.plan.v1`
- **Version:** 0.1.0
- **Status:** frozen in `factory-v0.5`
- **World:** `factory-0.1.0` + opt-in production tree
- **Owner:** FABLINE
- **Date:** 2026-11-27
- **RFC:** [`0031-assembly-edge.md`](../rfcs/0031-assembly-edge.md)
- **Code:** `src/fabline/harness/assembly_planning.py`
- **CLI:** `python -m fabline assembly-planning`

## Phenomenon

The assembly cell has a finite horizon. The planner chooses a binary recipe
plan — direct gear or assembly — for each block, then executes it without
feedback. Component supply, buffer fill, and switch timing make some plans much
better than others. The task tests finite-horizon planning on a production tree,
not online control.

## Contract

- **Plan:** five bits, one per 100-tick block; 500 ticks total.
- **Execution:** the plan is applied block by block; no replanning.
- **Observation:** the initial cell state (no online feedback in the plan).
- **Reward:** final depot score; success ≥ 100.
- **Baselines:** always gear, always assembly, alternate, batch-3, frontload,
  random plans, CEM with the true simulator, exhaustive 32-plan oracle.
- **Metrics:** mean score, 95% bootstrap CI, success; CEM/oracle gap.

## Gates

| Gate | Threshold |
|---|---|
| H1 planning gap | oracle ≥ best scripted + 10 |
| H2 CEM over random | CEM ≥ random + 10 |
| H3 CEM quality | CEM within 10 of oracle |
| H4 success | CEM success ≥ 0.60 |

Frozen v0.1–v0.4 hashes are enforced by the test suite and CI, not by the task
runner.

## Results (formal pilot, 5 seeds)

| Policy | Mean score | 95% CI |
|---|---:|---:|
| always_gear | 260.0 | [260, 260] |
| always_assembly | 360.0 | [360, 360] |
| alternate | 400.0 | [400, 400] |
| batch_3 | 350.0 | [350, 350] |
| frontload | 410.0 | [410, 410] |
| random | 372.9 | [363.9, 380.7] |
| **CEM** | **428.0** | [424.0, 430.0] |
| **oracle** | **430.0** | [430, 430] |

H1–H4 pass: oracle +20 over frontload, CEM +55.1 over random, CEM within 2 of
oracle, success 1.00.

## Known pitfalls

- **Five bits only.** CEM is exact-ish at 32 plans; this is not general planning
  evidence.
- **True-simulator CEM.** No learned model is used; the world-model line is
  still closed.
- **Scripted frontload is strong.** The plan space is coarse; report the
  oracle-scripted gap.
- **Do not add seeds after the formal block.**

## Changelog

- 2026-11-27 — task card created; formal pilot positive.
- 2026-11-27 — frozen in `factory-v0.5`; full suite reproduces CEM 428.
