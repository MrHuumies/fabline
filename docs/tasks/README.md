# Task cards

Each task has a card describing its phenomenon, contract, data, metrics,
baselines, and pitfalls. A task is not part of a frozen benchmark until its card
is complete and its splits are audited.

Current tasks:

- [Throughput prediction](throughput.md) — supervised regression over vector,
  grid, and entity views.
- [Next-state prediction](next-state.md) — passive self-supervised observation
  prediction (saturated).
- [Masked grid prediction](masked-grid.md) — spatial self-supervised
  reconstruction.
- [Bottleneck classification](bottleneck.md) — counterfactual entity-type
  classification.
- [Line expansion control](control.md) — constrained sequential construction.
- [Control dynamics](control-dynamics.md) — action-conditioned next-observation
  prediction.
- [Fault prediction](fault-prediction.md) — fault-within-horizon classification
  over the opt-in fault mechanic.
- [Fault recovery](fault-recovery.md) — two-action noop/repair control under a
  repair cost.
- [Fault onset](fault-onset.md) — 1-tick recent-onset detection over dynamic
  diagnostic views.
- [Brownout prediction](power-brownout.md) — brownout-within-horizon over
  opt-in power views.
- [Partial throughput](partial-throughput.md) — masked-feature future-score
  prediction with a single-frame and a 4-frame window view.
- [Reliability contract](power-contract.md) — choose a delivery target under
  stochastic power; mean and CVaR objectives separate.
- [Wired cascade](power-cascade.md) — predict which entities lose power after a
  marked wire fault on a graph with loops and bridges.
- [Wire repair](power-wire-repair.md) — prioritize budgeted wire repairs by
  restoration impact and skip zero-impact loops.
- [Preventive wire maintenance](power-wire-maintenance.md) — start repair from a
  degradation warning before the wire fails; late jobs abort.
- [Preventive machine maintenance](fault-preventive.md) — maintain a worn machine
  before the fault threshold; Q is unstable at the delayed trade.
- [Maintenance-threshold selection](fault-preventive-threshold.md) — choose the
  wear threshold once per episode; threshold bandit beats per-step Q.
- [Crew repair scheduling](crew-scheduling.md) — one crew, travel + repair time,
  and a choice among loop/small/large wires; preregistered.
- [Power allocation](power-allocation.md) — three-action priority scheduling
  under a tight generator budget.
- [Fault + power interaction](fault-power.md) — four-action repair and priority
  scheduling under faults and a tight power budget.

These are benchmark candidates for `factory-v0.1`, not public releases. Some
tasks have headroom; next-state is saturated and throughput is still easy on
the vector view.

## Adding a task

1. Copy [`../templates/task-card.md`](../templates/task-card.md).
2. Define the observation adapter(s), label/reward, termination, and split.
3. Add a trivial baseline and one strong baseline.
4. Add a test that the label/reward is deterministic and the split is disjoint.
5. Run the task on a small debug dataset and record the result.
6. Only then add it to a benchmark suite.
