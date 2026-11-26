# Experiment 0090 — Order control

- **Status:** complete (positive)
- **Date:** 2026-11-26
- **Type:** 0.4.0 Phase 2 order-control experiment
- **Task:** `factory.orders.control.v1` (draft, not in a frozen benchmark)
- **Code:** `src/fabline/env/orders.py`,
  `src/fabline/harness/order_control.py`
- **CLI:** `python -m fabline order-control`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**The seeded order stream creates a real recipe-switching decision, and tabular
Q beats random comfortably.** On fresh seeds 72,000–72,004, the value policy
scores **289.8** with success 1.00 and EDF **289.0/1.00**; tabular Q reaches
**280.2/1.00**, +53.8 over random 226.4/0.88. Always-gear is 119.6/0.40 and
always-component 222.3/0.56. H1/H2/H3/H4 pass. The task is a valid order-control
candidate; the next slice is order planning and deep/offline RL baselines.

## Formal results

Five seeds, five episodes per seed:

| policy | value | 95% CI | failed | wasted | switches | success |
|---|---:|---:|---:|---:|---:|---:|
| always_gear | 119.6 | — | 13.5 | 8.1 | 0.0 | 0.40 |
| always_component | 222.3 | — | 8.5 | 19.1 | 1.0 | 0.56 |
| edf | 289.0 | — | 4.9 | 5.2 | 2.3 | 1.00 |
| **value** | **289.8** | — | 5.0 | 5.4 | 4.6 | **1.00** |
| random | 226.4 | — | 8.0 | 10.9 | 14.7 | 0.88 |
| **tabular Q** | **280.2** | — | 5.2 | 7.2 | 12.1 | **1.00** |

CIs are in the JSON report; the table keeps the point estimates.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 order effect | best scripted ≥ always_gear + 10 | **pass**, +170.2 |
| H2 learned policy | Q ≥ random + 10 | **pass**, +53.8 |
| H3 success | Q success ≥ 0.60 | **pass**, 1.00 |
| H4 frozen benchmark | `factory-v0.2` unchanged | **pass** |

## Interpretation

- **Orders make the mix decision real.** Always-gear fails most orders; EDF and
  value policies switch to components when deadlines demand it.
- **Q is reliable at 100 training episodes.** It is +53.8 over random and
  succeeds on every formal episode, though scripted value is slightly higher.
- **The task is positive but scripted-easy.** Value/EDF reach 1.00; the learned
  baseline is the useful part, and deep RL is the next test.
- **Order state is task-layer state.** The default world hash is unchanged.

## Caveats

- 16×8 gear line, 4 orders, one value/deadline regime.
- Orders are known at reset; no arrival uncertainty yet.
- Component→gear assembly edge is not implemented.
- Tabular Q is the only learned baseline; no PPO/SAC/BC yet.
- CIs are in the raw JSON; five seeds.

## Next

1. Add order planning with a known order set.
2. Add PPO/SAC/BC baselines on order control.
3. Add demand calibration/causal variants if the planning task is stable.
4. Keep `factory-v0.2` and `v0.3.0` unchanged.

## Artifacts

- Task card: [`../../tasks/order-control.md`](../../tasks/order-control.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/order_control.py`
- Raw results: `results/order-control/` (ignored)
