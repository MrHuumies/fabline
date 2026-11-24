# Coverage review — FABLINE 0.3.0

- **Status:** complete; post-release review
- **Date:** 2026-11-24
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
- A ridge **value** model is not a world model. It is far below true CEM; the
  world-model gap remains open.
- Build planning (0075) was too sparse under the current reward; removing it
  was correct.

### Calibration

- Calibration must be reported with discrimination skill. The base context +
  thermal/vibration views are at majority; their low ECE is not evidence of a
  useful probability model.
- The top-4 entity sensor view is skilled and calibrated on fault onset. The
  benchmark seeds reproduce the ordering with balanced 0.923 and ECE 0.0118.
- Fault prediction at 50 ticks is saturated and remains a diagnostic, not a
  frozen task.

### Causal intervention

- Same-type entity pairs remove the type shortcut. Target position/buffer
  features predict the counterfactual removal effect; type-only does not.
- This is task-level interventional prediction, not causal graph recovery.

### Decentralized multi-agent

- Private radius-16 views create a large local/global gap (+288 on the 0077
  seeds).
- Independent Q improves on local greedy (+122) but succeeds only 0.47.
- The local scripted success gate also fails (0.40), so the task is hard for
  both scripted and learned local policies.
- The task is a valid debug task, but it is not freeze-ready.

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

1. **Decentralized reliability.** Compact state and/or centralized training
   with decentralized execution is the smallest credible fix.
2. **Transition world models.** True planning works; learning
   `(state, action) -> next state` and rolling it out is still open.
3. **Maintenance calibration.** The 0.3.0 RFC named fault and maintenance
   calibration; only fault onset was delivered.
4. **Generative layout/recipe.** Optional pilot did not run.
5. **Deep/offline RL.** Still absent as baseline families.
6. **Efficiency table.** Cost is reported per experiment but not as a public
   cross-task table.
7. **Viewer QoL.** Result summary is in the wizard; a replay browser and task
   card viewer are not.

## Recommended next slice

**Compact relative-geometry Q with a small ensemble on decentralized triage.**
See the [0081 pre-registration](experiments/0081-decentralized-compact-q/preregistration.md).

- Keep the existing task, radius, seeds, and joint action space.
- Replace absolute tick/distance buckets with relative service, deadline slack,
  and visibility features.
- Train independent per-crew Q at an equal budget to the old private Q.
- Evaluate a three-policy ensemble (mean action value).
- Gate: success ≥ 0.60, mean ≥ best local scripted + 10, and ensemble no worse
  than the best single compact Q.

If compact Q still misses 0.60, the next pre-registration is centralized
training with decentralized execution, not another compact-state variant.

## What not to do next

- another Q variant trained only on `factory-v0.2` seeds;
- another visibility radius or report-budget sweep;
- another fault/power calibration threshold;
- a generative task without a concrete validity/diversity question;
- a new world before the decentralized gate is resolved.

## Release state

- Public `v0.3.0` is published; `factory-v0.2` is tagged and immutable.
- `factory-v0.1` remains frozen; its hash is unchanged.
- Private and public CI are green.
- The next experiment is a new pre-registration; `factory-v0.2` is not modified.

## Map maintenance

Update the [coverage map](coverage-map.md) and the roadmap when the
decentralized follow-up passes or fails. Do not add a new benchmark version
until the gate result is known.
