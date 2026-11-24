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
  vs single-crew 60; the formal assignment is easy. See 0044 for the 40-seed
  robustness check.
- [0043 — Partial-view pilot](0043-partial-view-pilot/summary.md) — pilot
  negative; visibility is binary on the current layout.
- [0044 — Crew seed robustness](0044-crew-robustness/summary.md) — 40 seeds:
  nearest 255.5, greedy 245, Q 225.5, oracle 260; the gain is robust but the
  five-seed block was mildly optimistic.
- [0045 — Crew recall and replanning](0045-crew-replan/summary.md) — recovery
  +154 over no-replan; nearest 254, greedy 259, Q 144.0 fails H4.
- [0046 — Twin-line crew layouts](0046-crew-layouts/summary.md) — oracle 441,
  greedy 419, nearest 361, Q 217; the layout adds a real assignment gap.
- [0047 — Recall/replanning on twin lines](0047-crew-replan-layouts/summary.md)
  — recovery +240, but oracle-greedy +9 misses H3; Q fails; not promoted.
- [0048 — Compact layout-aware Q](0048-crew-layout-q/summary.md) — 422 vs old
  Q 233 and oracle 442; mean gate passes, success 0.50 misses 0.60.
- [0049 — Margin-aware Q pilot](0049-margin-q-pilot/summary.md) — pilot
  negative; slack bins fragment the table; not promoted.
- [0050 — Compact Q ensemble](0050-crew-layout-ensemble/summary.md) — 430 vs
  oracle 448; success 0.50 misses 0.60; one aliased seed remains.
- [0051 — Visibility pilot](0051-visibility-pilot/summary.md) — pilot
  negative on twin-line; radius still binary, delayed reports add nothing.
- [0052 — Distributed visibility](0052-crew-visibility/summary.md) — spread
  layout: local cost +98, delayed60 +54, all gates pass.
- [0053 — Multi-orphan pilot](0053-multi-orphan-pilot/summary.md) — pilot
  negative; simultaneous job aborts collapse to a one-bridge task; not
  promoted.
- [0054 — Sequential survivor](0054-crew-multi-orphan/summary.md) — recovery
  +342; nearest 438, greedy/aware/oracle 460; shallow, greedy matches oracle.
- [0055 — Three-bridge triage](0055-crew-triage/summary.md) — oracle 456,
  greedy 378, nearest 284; all gates pass.
- [0056 — Private views](0056-crew-private/summary.md) — shared local +40 and
  delayed60 +74 over private best; private nearest/aware 296.
- [0057 — Report budget](0057-crew-budget/summary.md) — 2 reports match shared;
  1 report −42; private −32 more; all gates pass.
- [0058 — Report-rule pilot](0058-report-rule-pilot/summary.md) — pilot
  negative; no K=1 rule recovers the bandwidth loss; not promoted.
- [0059 — Spread-triage pilot](0059-spread-triage-pilot/summary.md) — pilot
  negative; greedy matches oracle (600); not promoted.
- [0060 — Replacement handoff](0060-crew-replacement/summary.md) — oracle +20,
  best scripted −38; H2 fails; not promoted.
- [0061 — Pair-policy pilot](0061-pair-policy-pilot/summary.md) — pilot
  negative; no pair rule beats greedy; not promoted.
- [0062 — Three-crew assignment](0062-crew-three/summary.md) — three greedy
  476, oracle 520, two oracle 320; all gates pass.
- [0063 — Three-crew recall](0063-crew-three-replan/summary.md) — recovery
  +156; three greedy 516, oracle 520; shallow.
- [0066 — Asymmetric repair-cost triage](0066-crew-costs/summary.md) — negative;
  greedy matches oracle on fresh seeds; the pilot's +52 did not replicate.
- [0067 — Random-topology triage](0067-crew-topology/summary.md) — negative;
  random gap +4 vs spread +18; the topology axis is retired.
- [0070 — Assembler recipe choice](0070-recipe-choice/summary.md) — positive;
  buffer-aware 318 vs fast 278; myopic lookahead 278.
- [0071 — Recipe under power](0071-recipe-power/summary.md) — robust;
  buffer-aware 314 vs fast 272; power state adds no decision.
- [0072 — Byproduct queue](0072-recipe-byproduct/summary.md) — positive;
  purge-aware 302 vs fast 274; the purge action is the decision.
- [0074 — Contract board](0074-contract-board/summary.md) — positive;
  board-aware 112 vs best fixed 90; oracle 122.

The frozen benchmark is documented separately in
[`benchmarks/factory-v0.1/card.md`](../../benchmarks/factory-v0.1/card.md).
