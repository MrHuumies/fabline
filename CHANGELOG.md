# Changelog

All notable changes to FABLINE are recorded here. World and benchmark versions
are pinned separately; see [`benchmarks/factory-v0.1/card.md`](benchmarks/factory-v0.1/card.md).

## [Unreleased]

- Add decentralized private-view triage: global 748, local greedy 460, private
  Q 582; success 0.47 (0077).

- Add triage planning: true CEM 454 = oracle; learned value model 166;
  planning positive, world-model negative (0076).

## [0.2.0] — 2026-11-24

P3 production decisions and the public multiview contract. The frozen
`factory-v0.1` benchmark is unchanged.

- Add the 0.1.2 coverage review and next-slice recommendation.
- Add crew repair scheduling with travel: earliest-deadline-first 260 vs
  impact-only 62.4; the original Q fails (156.4).
- Add deadline-aware Q: 253.2, 1.00 success, +117 over the old Q (0041).
- Add two-crew parallel repair coordination: 260 vs single-crew 60; Q 260;
  the formal assignment is easy (0042).
- Document a negative partial-view pilot: visibility is binary on the current
  layout (0043).
- Add a 40-seed robustness run for two-crew coordination: nearest 255.5,
  greedy 245, pooled Q 225.5, oracle 260; the coordination gain is robust, but
  the five-seed 0042 block was mildly optimistic (0044).
- Add crew recall and replanning: the survivor's recovery dispatch is worth
  +154 over no-replan (254 vs 100); nearest 254, greedy 259, tabular Q 144.0
  fails the 0.85 gate (0045).
- Add twin-line randomized crew layouts: oracle 441, greedy 419, nearest 361,
  tabular Q 217; the layout adds a real assignment gap but Q fails H4 (0046).
- Document a negative combination: recall/replanning on twin lines keeps the
  recovery gain (+240) but the oracle-greedy gap is +9, missing the +10 gate;
  Q fails; not promoted (0047).
- Add a compact layout-aware Q: 422 vs old Q 233 and oracle 442; mean gate
  passes, success 0.50 misses 0.60 (0048).
- Document a negative margin-aware Q pilot: slack bins fragment the table and
  drop to 340-384; not promoted (0049).
- Add a compact-Q ensemble: 430 vs oracle 448; success 0.50 misses 0.60; one
  aliased seed remains (0050).
- Document a negative visibility/communication pilot: radius is still binary on
  the twin-line layout and delayed reports add nothing; not promoted (0051).
- Add distributed-layout visibility/report task: local cost +98, delayed60 +54,
  all gates pass on the 48×24 spread layout (0052).
- Document a negative simultaneous multi-orphan pilot: both jobs aborting
  collapses to a one-bridge task; not promoted (0053).
- Add sequential survivor dispatch: recovery +342; nearest 438,
  greedy/aware/oracle 460; shallow, greedy matches oracle (0054).
- Add three-bridge survivor triage: oracle 456, greedy 378, nearest 284; all
  gates pass (0055).
- Add private-view comparison: shared local +40 and delayed60 +74 over private
  best; private nearest/aware 296 (0056).
- Add report-budget comparison: two reports match shared; one costs 42;
  private costs 32 more (0057).
- Document a negative one-report selection pilot: no scripted rule recovers the
  K=1 loss; bandwidth is binding (0058).
- Document a negative spread-layout triage pilot: greedy matches oracle (600);
  not promoted (0059).
- Document a mixed replacement handoff: oracle +20, best scripted −38; not
  promoted (0060).
- Document a negative pair-aware replacement pilot: no rule beats greedy
  (0061).
- Add three-crew initial assignment: three greedy 476, oracle 520, two oracle
  320; all gates pass (0062).
- Add three-crew recall/recovery: +156 over no-replan, three greedy 516,
  oracle 520; shallow (0063).
- Add asymmetric repair-cost triage: negative; greedy 386 matches oracle 386
  on fresh seeds (0066).
- Add random-topology triage: negative; random gap +4 vs spread +18; topology
  axis retired (0067).
- Add assembler recipe choice: buffer-aware 318 vs fast 278; myopic lookahead
  278; all gates pass (0070).
- Add recipe choice under a tight power budget: buffer-aware 314 vs fast 272;
  power-saver ties, headroom gating is worse; power adds no decision (0071).
- Add a blocking byproduct queue: purge-aware 302 vs fast 274; the purge action
  is the new decision (0072).
- Add a gear-contract board: board-aware 112 vs best fixed 90; oracle 122;
  all gates pass (0074).
- Add the multiview observation contract and view-arrival task interface:
  named views, view masks, fixed-width flatten, and episode-grouped splits.
- Add the P2 coverage review: coordination, visibility, and triage results;
  Q and visibility lines near saturation; third crew/replacement recommended.

## [0.1.2] — 2026-11-22

P1 wired power and preventive maintenance. The frozen `factory-v0.1` benchmark is
unchanged.

### Wired power

- opt-in wire-edge topology with loops, bridge/loop faults, and cascade-size
  prediction (0032);
- budgeted wire repair (0033) and timed repair (0034);
- preventive wire maintenance from a degradation warning (0035).

### Preventive maintenance

- machine-wear maintenance before the fault threshold (0037);
- maintenance-threshold selection (0038);
- pilot negatives for risk-score noise (0036) and contextual thresholds (0039).

### Tooling and docs

- new CLI commands: `wire-repair`, `wire-maintenance`, `preventive-fault`, and
  `preventive-threshold`;
- RFCs 0007–0009, ADRs 0017–0019, task and dataset cards.

## [0.1.1] — 2026-11-21

P0 model coverage after 0.1.0. The frozen `factory-v0.1` benchmark is unchanged.

### Prediction and calibration

- Brier, NLL, and ECE calibration metrics for the stochastic power benchmark.

### Partial observability

- deterministic feature-dropout, grid-fog, and delayed-observation adapters;
- masked feature-window throughput task with a single-frame and four-frame view.

### Architecture baselines

- sequence models on the masked-window task;
- grid CNN on clear and moving-fog views;
- end-to-end MPNN on the entity graph, against flattened and `graph_mp`
  baselines.

### Risk-sensitive control

- reliability-contract task under stochastic power;
- corrected episode sampling and a unique, interleaved evaluation design;
- replicated CVaR gain of roughly 13–17 points for a roughly 5-point mean
  premium. The task is a P0 benchmark candidate outside frozen `factory-v0.1`.

### Docs

- coverage map and P0 experiment summaries;
- Apache-2.0 code; CC-BY-4.0 docs, cards, and synthetic data.

## [0.1.0] — 2026-11-21

First public release candidate.

### Core

- deterministic factory world with fixed tick order, stable entity IDs, seeded
  generation, canonical state hashing, and exact replay validation;
- headless-first core with optional Torch, scikit-learn, and pygame extras;
- `factory-v0.1` frozen benchmark: 46 shared episodes, scenario splits,
  throughput, next-state, masked-grid, bottleneck, control, and
  control-dynamics tasks.

### Mechanics

- opt-in machine faults with wear, downtime, auto-repair, diagnostic sensors,
  fault prediction, repair, and recovery control;
- opt-in power grid with pre-placed generators, activity-gated demand,
  brownouts, power views, brownout prediction, and allocation control;
- seeded stochastic power variation for uncertain prediction and control.

### Tooling and docs

- `fabline` CLI for smoke, datasets, benchmarks, suites, rendering, demos,
  behavior cloning, faults, power, allocation, and replay validation;
- make targets for the same paths;
- task cards, dataset cards, ADRs, RFCs, and selected experiment summaries.

### License

Code: Apache-2.0. Documentation, benchmark cards, and synthetic datasets:
CC-BY-4.0. See `LICENSE`, `LICENSE-docs`, and `NOTICE`.

### Known limitations

- The frozen benchmark is small: 6 test and 6 shift episodes. CIs are wide.
- Some tasks are saturated; do not present them as hard benchmarks.
- Faults and power are opt-in and do not change `factory-v0.1`.
- The viewer is functional, not polished.
