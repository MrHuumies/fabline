# Coverage review — FABLINE 0.3.0

- **Status:** complete; post-release review (updated with 0081)
- **Date:** 2026-11-25
- **Scope:** experiments 0075–0079, `factory-v0.2`, the wizard, and the
  `v0.3.0` surface
- **Related:** [coverage map](coverage-map.md), frozen
  [`factory-v0.2` card](../benchmarks/factory-v0.2/card.md), and the public
  [`v0.3.0` release](https://github.com/MrHuumies/fabline/releases/tag/v0.3.0)

## Verdict

0.3.0 delivered three positive task-level results and one unfinished
multi-agent gate:

- **true-simulator planning** is positive; the learned value model is not;
- **fault-onset calibration** is meaningful once the model has skill;
- **counterfactual entity removal** shows a clean intervention signal;
- **decentralized triage** has a large local/global gap, but the learned
  policy still misses the 0.60 success gate.

`factory-v0.2` is frozen at 10 headline tasks. The next slice should close the
decentralized reliability gate, not add another calibration or planning sweep.

## Experiment map

| # | Slice | Result | Read |
|---|---|---|---|
| 0075 | Build planning | sparse; CEM 0 vs scripted 140 | negative; removed |
| 0076 | Triage planning | CEM true 454 = oracle; ridge 166 | true planning positive; value model negative |
| 0077 | Decentralized triage | global 748; local greedy 460; Q 582, success 0.47 | task positive; Q reliability open |
| 0078 | Fault calibration | top-4 GBDT balanced 0.950, ECE 0.008 | positive on a skilled view |
| 0079 | Causal removal | target GBDT R² 0.910 vs type-only −0.300 | positive intervention signal |
| 0081 | Compact decentralized Q | compact 616/0.40 vs old 616/0.40 | negative representation/ensemble |
| 0082 | CTDE | 248/0.00 vs local greedy 532/0.20 | negative; local-policy line retired |
| 0083 | Transition planning | one-step MSE 0.0182 vs copy 0.0695; CEM 162/0.20 | negative: rollout error |
| 0084 | Maintenance calibration | diagnostics GBDT ECE 0.0054; full view 0.0929 | mixed; H2 fails on full view |
| 0085 | Transition ensemble | single 166/0.20; ensemble 184/0.40; true 442 | mixed; improvement, gate miss |
| 0086 | Two-step transition | single 162/0.20; two-step 188/0.40; true 442 | mixed; linear ceiling |
| 0087 | Generative feasibility | 7 unique line sequences; diversity 0.080 | negative; content too constrained |
| 0088 | Efficiency table | 45k ticks/s; 10 model rows | complete; descriptive |
| — | `factory-v0.2` | 10 tasks, 159 core episodes | frozen |
| — | Wizard | stdlib command runner + summary | shipped |

On the frozen benchmark seeds, the point estimates are: planning CEM true 462 =
oracle, CEM learned 232; top-4 calibration GBDT balanced 0.923, ECE 0.0118;
causal target GBDT R² 0.987 vs type-only −0.074. The ordering is the same as
the pilots.

## What 0.3.0 established

### Planning and world models

- A finite triage plan with a true simulator is a real planning task: CEM
  reaches the exhaustive oracle, and scripted/random policies are below it.
- A ridge **value** model is not a world model. It is far below true CEM.
- A ridge **delta transition** model fits one-step transitions well (MSE 0.0182
  vs copy 0.0695, done accuracy 1.000) but fails in rollout: CEM transition
  162/0.20 vs true 454/1.00. Compounding error is the binding problem.
- An 8-member bootstrap ensemble has an informative uncertainty signal
  (Spearman 0.320) and improves pessimistic CEM from 166/0.20 to 184/0.40, but
  remains far below true CEM 442/1.00. Pessimism helps; it does not solve
  rollout error.
- A two-step transition model also improves CEM from 162/0.20 to 188/0.40, but
  still misses true CEM 442/1.00. Two different fixes converge at 0.40 success;
  the linear transition family is at its practical ceiling.
- Build planning (0075) was too sparse under the current reward; removing it
  was correct.

### Calibration

- Calibration must be reported with discrimination skill. The base context +
  thermal/vibration views are at majority; their low ECE is not evidence of a
  useful probability model.
- The top-4 entity sensor view is skilled and calibrated on fault onset. The
  benchmark seeds reproduce the ordering with balanced 0.923 and ECE 0.0118.
- Maintenance-risk calibration is mixed: the diagnostics view is skilled and
  calibrated (GBDT ECE 0.0054), but adding maintenance state features makes
  GBDT miscalibrated (ECE 0.0929). The registered full-view H2 gate fails.
- Fault prediction at 50 ticks is saturated and remains a diagnostic, not a
  frozen task.

### Causal intervention

- Same-type entity pairs remove the type shortcut. Target position/buffer
  features predict the counterfactual removal effect; type-only does not.
- This is task-level interventional prediction, not causal graph recovery.

### Decentralized multi-agent

- Private radius-16 views create a large local/global gap (+288 on the 0077
  seeds; +232 on the 0081 seeds).
- Independent Q improves on local greedy (+122 on 0077; +84 on 0081) but
  succeeds only 0.47 / 0.40.
- Compact relative-geometry Q and a three-policy ensemble do not change the
  learned policy: both score 616 with success 0.40, exactly matching the old
  state at equal budget.
- A tabular centralized critic with count-based decentralized actors collapses
  to noop-like behavior: 248/0.00, below local greedy. The local-policy line is
  retired.
- The local scripted success gate also fails (0.20–0.40), so the task is hard
  for both scripted and learned local policies.
- The task is a valid debug oracle/scripted surface, but it is not freeze-ready.

### Benchmark and tooling

- `factory-v0.2` freezes the seven core tasks plus planning, calibration, and
  causal removal.
- `factory-v0.1` is unchanged; `factory-v0.2` has a compact expected summary and
  a CI check.
- The wizard is a stdlib-only command runner and result summarizer. The replay
  browser and task-card viewer remain optional QoL work.

## Negative and saturated results

- **Build planning (0075):** sparse reward; not promoted.
- **Learned value model (0076):** fails the model-quality gate.
- **Decentralized Q (0077):** success 0.47, below 0.60.
- **Fault prediction:** saturated; diagnostic only.
- **Stochastic power:** near majority; diagnostic only.
- **Next-state:** saturated by copy/linear; diagnostic only.
- **Decentralized local success:** 0.40, below the task's 0.60 local baseline
  gate.

## Remaining gaps

1. **Decentralized reliability.** Compact Q and tabular CTDE are both negative;
   the local-policy line is retired. Keep the task as oracle/scripted-only.
2. **Transition world models.** True planning works. The linear family is
   closed: one-step 162/0.20, uncertainty ensemble 184/0.40, two-step 188/0.40,
   true CEM 442/1.00. A nonlinear model is a new pre-registration, not a tune
   of 0083/0085/0086.
3. **Maintenance calibration.** Delivered as a mixed result (0084): the
   diagnostics view is calibrated, the full maintenance view is not. The
   calibration line is closed; do not add another view.
4. **Generative layout/recipe.** Feasibility audit (0087) is negative: only 7
   unique line sequences and diversity 0.080. The current content cannot
   support a meaningful generative task; a richer grammar is a new mechanic.
5. **Deep/offline RL.** Still absent as baseline families.
6. **Efficiency table.** Delivered in [`efficiency.md`](efficiency.md); descriptive
   and machine-dependent, not a leaderboard.
7. **Viewer QoL.** Complete: replay browser, task-card viewer, and result
   summary are in the wizard and as standalone CLI commands.

## Recommended next slice

**A 0.4.0 scope decision.** All 0.3.0 research and release-quality lines are
closed: decentralized (0081/0082), calibration (0084), linear transitions
(0083/0085/0086), generative feasibility (0087), efficiency (0088), and viewer
QoL (replay browser/task-card viewer). There is no remaining cheap pilot.

Options for 0.4.0:

1. **Nonlinear transition model.** A new pre-registration; the cleanest
   world-model follow-up.
2. **Deep/offline RL.** A larger baseline track; needs a new scope decision.
3. **Richer generative grammar.** A new mechanic/RFC, not a model tweak.

Do not add another calibration view, decentralized variant, linear transition
model, beta/K sweep, or generative model on seven lines.

## What not to do next

- another compact-state Q or CTDE variant on this task;
- tuning the 0083 ridge model, 0085 beta/K ensemble, or 0086 pair window;
- another maintenance-calibration view or horizon;
- another Q variant trained only on `factory-v0.2` seeds;
- another visibility radius or report-budget sweep;
- another fault/power calibration threshold;
- a generative model on the seven current line grammars;
- a new world before the content/question is justified.

## Release state

- Public `v0.3.0` is published; `factory-v0.2` is tagged and immutable.
- `factory-v0.1` remains frozen; its hash is unchanged.
- Private and public CI are green.
- The next experiment is a new pre-registration; `factory-v0.2` is not modified.

## Map maintenance

Update the [coverage map](coverage-map.md) and the roadmap when the
decentralized follow-up passes or fails. Do not add a new benchmark version
until the gate result is known.
