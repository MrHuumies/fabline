# Experiment 0091 — Order planning

- **Status:** complete (positive)
- **Date:** 2026-11-26
- **Type:** 0.4.0 Phase 2 order-planning experiment
- **Task:** `factory.orders.plan.v1` (draft, not in a frozen benchmark)
- **Code:** `src/fabline/harness/order_planning.py`
- **CLI:** `python -m fabline order-planning`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**Order planning is a clean positive: CEM with the simulator matches the
exhaustive oracle.** On fresh seeds 74,000–74,004, CEM and oracle both score
**292.4** with success 1.00; EDF plan is **263.8/1.00**, value plan 232.0/0.80,
random 168.4/0.60, always-gear 111.4/0.40, and always-component 203.0/0.60.
H1–H5 pass. The five-block recipe plan is a real finite-horizon decision; the
next slice is deep/offline RL on online order control.

## Formal results

Five seeds, five blocks per plan:

| policy | mean value | success | seconds |
|---|---:|---:|---:|
| always_gear | 111.4 | 0.40 | 0.004 |
| always_component | 203.0 | 0.60 | 0.004 |
| value_plan | 232.0 | 0.80 | 0.004 |
| edf_plan | 263.8 | 1.00 | 0.004 |
| random_plan | 168.4 | 0.60 | 0.004 |
| **CEM** | **292.4** | **1.00** | 0.294 |
| **oracle** | **292.4** | **1.00** | 0.144 |

CEM matches the oracle on every formal seed; per-seed plans are in the JSON.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 planning gap | oracle ≥ best scripted + 10 | **pass**, +28.6 |
| H2 CEM over random | CEM ≥ random + 10 | **pass**, +124.0 |
| H3 CEM quality | CEM within 10 of oracle | **pass**, equal |
| H4 success | CEM success ≥ 0.60 | **pass**, 1.00 |
| H5 frozen benchmark | `factory-v0.2` unchanged | **pass** |

## Interpretation

- **The block plan is a real decision.** EDF is strong but not oracle; the
  oracle gap is +28.6.
- **CEM is exact at this plan size.** Five bits are small enough for CEM to find
  the best plan on every seed.
- **Random and fixed plans are weak.** Always-gear and random are far below;
  always-component is better but not enough.
- **This is a planning benchmark, not a learned world model.** CEM uses the
  simulator; the 0083/0085/0086 learned-model line remains closed.
- **Order control and order planning share the mechanic.** The online task has
  Q at 280.2/1.00; planning has CEM at 292.4/1.00.

## Caveats

- Five bits, 32 plans; the oracle is small.
- Orders are known at reset, not revealed online.
- One order/value/deadline regime.
- No deep/offline RL or learned model in this slice.
- `factory-v0.2` is unchanged.

## Next

1. Deep/offline RL baselines on order control (PPO/SAC/BC).
2. Demand calibration and causal variants if the control/planning pair remains
   stable.
3. A `factory-v0.3` freeze only after the pilots pass.
4. Keep `factory-v0.2` and `v0.3.0` unchanged.

## Artifacts

- Task card: [`../../tasks/order-planning.md`](../../tasks/order-planning.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/order_planning.py`
- Raw results: `results/order-planning/` (ignored)
