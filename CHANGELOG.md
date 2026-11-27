# Changelog

All notable changes to FABLINE are recorded here. World and benchmark versions
are pinned separately; see [`benchmarks/factory-v0.3/card.md`](benchmarks/factory-v0.3/card.md).

## [Unreleased]

- Freeze `factory-v0.4`, the 0.5.0 coverage suite: eight tasks, public
  structured baselines, expected summary, and full CI check. Seven tasks pass;
  wired-cascade remains a diagnostic.
- Add the opt-in assembly-edge production tree: per-assembler recipe state,
  component logistics, and `INGOT + COMPONENT -> GEAR` (2 gears in the task).
  Add a two-feed assembly cell and `factory.assembly.control.v1`; the formal
  pilot is positive (Q 460 vs random 429, always gear 260). Add
  `factory.assembly.plan.v1`; CEM 428 vs oracle 430, frontload 410, random 373.
- Add `factory.assembly.bom.v1`, a short-horizon gear-output forecast under
  decision noise; GBDT R² 0.503 vs linear 0.343, all gates pass.
- Add `factory.assembly.recipe_intervention.v1`, a paired counterfactual
  recipe-switch task; GBDT R² 0.944 and +1.62 of +2.00 oracle decision gain.
- Freeze `factory-v0.5`, the 0.6.0 assembly suite: four tasks, `assembly-suite`
  CLI, expected summary, zero-mismatch check, and full CI workflow. Demand
  uncertainty, layout splits, and logged-data causal identification are
  documented follow-ups.

## [0.4.0] — 2026-11-26

0.4.0 adds demand-driven production, seeded orders, order control/planning,
and freezes `factory-v0.3`. `factory-v0.2` remains immutable.

- Add a compact relative-geometry Q baseline for decentralized triage. It is
  negative: compact Q, the old state, and the ensemble all score 616/0.40
  against oracle 764/1.00 (0081).

- Add a tabular centralized-critic, decentralized-actor baseline. It is also
  negative: CTDE scores 248/0.00, below local greedy 532/0.20 (0082). The
  local-policy line is retired; the task remains an oracle/scripted debug
  surface.

- Add a ridge delta transition model for triage planning. It fits one-step
  transitions (MSE 0.0182 vs copy 0.0695) but fails in rollout: CEM 162/0.20
  vs true CEM 454/1.00 (0083).

- Add maintenance-risk calibration. It is mixed: diagnostics GBDT ECE 0.0054,
  but the full maintenance view is miscalibrated at ECE 0.0929 (0084). The
  calibration line is closed.

- Add an uncertainty-aware transition ensemble. Ensemble disagreement is
  informative (Spearman 0.320) and improves CEM from 166/0.20 to 184/0.40, but
  remains far below true CEM 442/1.00 (0085).

- Add a two-step transition model. It improves CEM from 162/0.20 to 188/0.40,
  but still misses true CEM 442/1.00 (0086). The linear transition line is
  closed.

- Add a generative layout/recipe feasibility audit. It is negative: only 7
  unique line sequences and diversity 0.080 across 1,300 lines (0087). The
  current content cannot support a meaningful generative pilot.

- Add a reproducible cross-task efficiency table: 45k world ticks/s, with
  fit/predict time, artifact size, and peak memory for 10 model rows (0088).
  It is descriptive, not a leaderboard.

- Add headless viewer QoL: `fabline replay-browser` and `fabline task-cards`,
  plus both paths in `fabline wizard`. Read-only and no new dependency.

- Start the 0.4.0 demand-driven production scope. The opt-in production mix
  produces gear or component; the pilot is mixed (component 186 vs gear 150,
  no schedule gap), so the order stream is next (0089).

- Add seeded order control: value 289.8, tabular Q 280.2, random 226.4; all
  gates pass on fresh seeds (0090).

- Add order planning: CEM matches the oracle at 292.4, EDF 263.8; all gates
  pass on fresh seeds (0091).

- Add BC/PPO baselines on order control: negative at 10k steps (BC 249.8,
  PPO 169.0 vs random 243.2); scripted value 272.5 and Q 259.5 remain stronger
  (0092).

- Draft the `factory-v0.3` freeze review: 12 proposed headline tasks (v0.2 core
  plus order control and order planning); production mix and RL are diagnostics.

- Freeze `factory-v0.3`: 12 headline tasks, full expected-summary check with zero
  mismatches. `factory-v0.2` remains immutable.

- Add the 0.4.0 coverage review: orders supply the decision the recipe mix
  lacked; standalone production mix and BC/PPO are diagnostics/negative. The
  Phase 1b assembly edge is the leading 0.5.0 candidate.

## [0.3.0] — 2026-11-24

0.3.0 adds the planning, calibration, and causal decision surfaces, freezes
`factory-v0.2`, and adds a stdlib wizard. `factory-v0.1` remains immutable.

- Freeze `factory-v0.2`: 10 headline tasks on 159 core episodes plus triage
  planning, fault-onset calibration, and causal entity removal.

- Add a stdlib `fabline wizard` for smoke, dataset, shared-suite, benchmark,
  and result-summary workflows. It previews commands and supports `--dry-run`.

- Add counterfactual entity-removal prediction: target GBDT R² 0.910 vs
  type-only −0.300 (0079).

- Add fault calibration: top-4 GBDT balanced 0.950, ECE 0.008; base views at
  majority (0078).

- Add decentralized private-view triage as a debug task: global 748, local
  greedy 460, private Q 582; success 0.47 (0077). It is deferred from the
  frozen benchmark because the local-success gate is open.

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
