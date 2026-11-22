# Selected experiments

These are selected experiment records from the FABLINE research log. They show
how the testbed is used for mechanics, tasks, and controls. Experiment IDs are
retained for provenance.

- [0008 — Opt-in machine faults](0008-fault-mechanic/summary.md) — wear, downtime,
  diagnostic sensors, and a fault-prediction debug task.
- [0009 — Repair and recovery](0009-fault-recovery/summary.md) — repair action and
  a two-action recovery environment.
- [0015 — Power grid](0015-power-grid/summary.md) — generators, brownouts, power
  views, and brownout prediction.
- [0016 — Power allocation](0016-power-allocation/summary.md) — priority
  scheduling under a tight generator budget.
- [0022 — Calibration on stochastic power](0022-calibration-stochastic-power/summary.md)
  — Brier, NLL, and ECE; calibration is not skill.
- [0024 — Masked feature window](0024-masked-window/summary.md) — 60% feature
  dropout; a 4-frame window recovers most of the lost R² for linear/GBDT.
- [0025 — Sequence baselines](0025-sequence-baselines/summary.md) — Transformer
  +0.078 over flat MLP, below the gate; GBDT remains strongest.
- [0026 — Grid CNN](0026-grid-cnn/summary.md) — CNN nearly solves the clear
  grid but is less fog-robust than the flattened MLP.
- [0027 — End-to-end MPNN](0027-graph-mpnn/summary.md) — relational structure
  transfers on the held-out combination; MPNN trails `graph_mp` by 0.09.
- [0028 — Reliability contract](0028-risk-contract/summary.md) — mean and CVaR
  select different targets; a sampling defect was later corrected in 0030.
- [0029 — Failure-dense contract](0029-risk-contract-dense/summary.md) — a harsher
  regime; it shares the sampling defect corrected in 0030.
- [0030 — Contract evaluation design](0030-contract-eval-design/summary.md) —
  unique interleaved seeds fix the train/test shift; clean CVaR gain +13.55
  [10.50, 16.95].
- [0031 — Contract confirmation](0031-contract-confirm/summary.md) — fresh-seed
  replication passes all gates: +17.05 CVaR [13.25, 21.15].
- [0032 — Wired cascade](0032-wired-cascade/summary.md) — graph_mp R² 0.431 vs
  vector 0.264 on wired-power cascade size.
- [0033 — Wire repair](0033-wire-repair/summary.md) — outage-ranked repair 260
  vs noop 79; Q 212 with zero wasted repairs.
- [0034 — Timed wire repair](0034-wire-repair-timed/summary.md) — Q matches
  outage-ranked repair 223.2; the repair-order gate fails.
- [0035 — Preventive wire maintenance](0035-wire-maintenance/summary.md) —
  early repair 260 vs reactive 185.6; Q learns prevention.
- [0036 — Risk-score pilot](0036-risk-score-pilot/summary.md) — pilot negative;
  score noise barely changes the preventive decision; not promoted.
- [0037 — Preventive machine maintenance](0037-preventive-fault/summary.md) —
  threshold 250 vs noop 200; Q is unstable and H2 fails.
- [0038 — Maintenance-threshold selection](0038-preventive-threshold/summary.md)
  — threshold bandit 250 vs per-step Q 178.
- [0039 — Contextual threshold pilot](0039-context-threshold-pilot/summary.md) —
  pilot negative; only +5 over the best fixed arm.
- [0040 — Crew scheduling](0040-crew-schedule/summary.md) — deadline-aware
  repair 260 vs impact-only 62; the original Q fails (156).
- [0041 — Deadline-aware Q](0041-crew-q/summary.md) — 253.2, 1.00 success,
  +117 over the old Q.
- [0042 — Two-crew coordination](0042-multi-crew/summary.md) — two crews 260
  vs single-crew 60; the formal assignment is easy.
- [0043 — Partial-view pilot](0043-partial-view-pilot/summary.md) — pilot
  negative; visibility is binary on the current layout.

The frozen benchmark is documented separately in
[`benchmarks/factory-v0.1/card.md`](../../benchmarks/factory-v0.1/card.md).
