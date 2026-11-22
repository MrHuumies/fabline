# Coverage review — FABLINE 0.1.2

- **Status:** complete; post-release review
- **Date:** 2026-11-22
- **Scope:** P0 (0022–0031) and P1 (0032–0039), plus the public `v0.1.2`
  surface
- **Related:** [coverage map](coverage-map.md),
  [benchmark card](../benchmarks/factory-v0.1/card.md), and the public
  [`v0.1.2` release](https://github.com/MrHuumies/fabline/releases/tag/v0.1.2)

## Verdict

P0 is complete and P1 has a working wired-power and preventive-maintenance
surface. The strongest P1 result is **preventive wire maintenance**; the weakest
is **per-step repair Q**, which fails on delayed credit. The threshold bandit
fixes the representation but is a deterministic seven-arm check, not a
sequential-control benchmark. Further repair layers are showing diminishing
returns: timing changed scores, order did not; forecast noise did not change
decisions; context did not separate fixed from contextual policies.

The next credible step is **spatial scheduling**, not another repair variant:
one crew, several components, travel time, and a choice of what to service.

## What is covered now

### Task families

| Family | Tasks | Read |
|---|---|---|
| Supervised tabular | throughput-vector, partial throughput, bottleneck | strong; some saturation |
| Spatial | throughput-grid, masked-grid, grid CNN/fog | partial; small fixed layouts |
| Relational | throughput-entities, wired cascade, MPNN | partial; `graph_mp` strong |
| Temporal / sequence | next-state, control-dynamics, masked window | partial; short horizons |
| Control / RL | expand-control, fault recovery, power allocation, fault+power, wire repair, preventive maintenance | partial; tabular/scripted |
| Calibration / risk | power calibration, reliability contract | covered for power |
| Robustness / OOD | scenario splits, stochastic power, fog | partial |
| Planning / world models | — | absent |
| Multi-agent | — | absent |
| Generative | — | absent |

### Model families

Implemented baselines now include:

- mean, persistence, linear, GBDT, MLP;
- CNN (grid/fog);
- GRU, Transformer, temporal CNN (masked window);
- `graph_mp` message-passing features and an end-to-end MPNN;
- calibration (Brier, NLL, ECE);
- tabular Q, scripted policies, epsilon-greedy and UCB bandits;
- CVaR/risk-sensitive selection.

Still missing: deep RL, offline RL beyond behavior cloning, world models,
multi-agent RL, and generative models.

### Mechanics

- opt-in machine faults, sensors, repair, recovery;
- opt-in power grid, stochastic power, allocation control;
- opt-in wired power, cascade prediction, budgeted repair, timed repair;
- preventive wire maintenance from a degradation warning;
- preventive machine maintenance and maintenance-threshold selection.

## Diagnostic outcomes

| Experiment | Result | Read |
|---|---|---|
| 0022 calibration | GBDT discriminates; MLP calibrates | calibration is not skill |
| 0023 delay pilot | saturated | periodic line identifies phase |
| 0024 masked window | window recovers ~70% for linear/GBDT | partial observability is real |
| 0025 sequence | Transformer +0.078, below gate | small task favors GBDT |
| 0026 grid CNN | clear 0.997, fog 0.509 | spatial bias, fog fragility |
| 0027 MPNN | 0.258 vs `graph_mp` 0.348 | relational transfer, scale boundary |
| 0028–0031 contract | +13.55 / +17.05 CVaR | risk trade replicated after sampler fix |
| 0032 wired cascade | `graph_mp` 0.431 vs vector 0.264 | graph cut is learnable |
| 0033 wire repair | 260 vs noop 79; Q 212 | budgeted prioritization works |
| 0034 timed repair | 223.2; order gate fails | timing matters, order not |
| 0035 preventive wire | 260 vs reactive 185.6 | warning makes prediction actionable |
| 0036 risk noise pilot | +5 context gain; noise-insensitive | not promoted |
| 0037 preventive machine | threshold 250 vs noop 200; Q 178 | delayed credit breaks Q |
| 0038 threshold selection | 250, +72 over per-step Q | representation fix |
| 0039 contextual pilot | +5 over best fixed | not promoted |

## Saturation and negative results

- **Next-state is saturated** by copy/linear.
- **Fault and power GBDT tasks are easy**; keep them as controls, not headlines.
- **Sequence models do not beat GBDT** on the small masked-window task.
- **The grid CNN is less fog-robust** than the flattened MLP.
- **The end-to-end MPNN trails `graph_mp`**; scale and sample size are binding.
- **Per-step repair Q is unstable** on delayed credit; Q(λ) and Monte Carlo did
  not fix it in the pilot.
- **Risk-score noise does not change decisions** at the tested scale.
- **Contextual thresholds do not separate** from the best fixed threshold; the
  0.8–0.9 plateau is too robust.

## Coverage gaps

1. **Spatial planning and crew scheduling.** Repair tasks choose among ranked
   wires or a single watched wire; no task uses positions, travel, and one crew
   as the decision.
2. **Multi-agent coordination.** Still absent; the largest orthogonal addition.
3. **Larger/random layouts.** The grid tasks are small and fixed; no scale or
   layout-shift split for spatial models.
4. **Long-horizon temporal structure.** Sequence tasks are short; event timing
   is not a headline benchmark.
5. **Planning/world models.** No rollout or model-based planning task.
6. **Uncertainty beyond power.** Calibration exists for power only; maintenance
   and repair forecasts are not calibrated.
7. **Efficiency.** P1 cost is not benchmarked publicly.
8. **Deep RL / offline RL.** Control is tabular/scripted; no deep or offline RL
   baseline.

## P1 verdict

What worked:

- wired topology creates a genuine graph-cut label;
- budgeted repair prioritization is learnable and interpretable;
- a degradation warning makes prevention actionable;
- threshold selection fixes the representation failure of per-step Q.

What did not:

- timed repair order (0034) is not robust;
- per-step Q on delayed maintenance (0037) collapses;
- risk-score noise (0036) and contextual thresholds (0039) are weak pilots;
- the threshold task is deterministic and easy.

The line is not exhausted, but the **next layer must add spatial structure**, not
another threshold or reward tweak.

## Recommended next slice

**Per-entity maintenance scheduling with one crew and travel time.**

- 3–4 failed or degraded components at different positions;
- one crew with a position; service time = travel + repair;
- a budget smaller than the number of components;
- the agent chooses which component to service, not a ranked slot;
- compare impact-only, nearest-first, travel-aware, oracle order, random, Q;
- gates: travel-aware/oracle beats impact-only by a meaningful margin, or the
  task is retired.

This is the smallest mechanic that makes context spatial and makes the choice
non-trivial. If the travel-aware gain is under 5 points, stop P1 and move to P2
(multi-agent or larger/random layouts) rather than adding another repair layer.

## What not to do next

- another threshold arm or reward shaping on the same maintenance task;
- another risk-score noise sweep without multiple true failures;
- a context task whose best fixed policy is already within 5 points of oracle;
- more content without a named model weakness.

## Map maintenance

Update the [coverage map](coverage-map.md) and the private roadmap when this
review's recommendations are accepted or rejected. Keep the public
`v0.1.2` release frozen; new mechanics go on `main` and wait for the next
release.


## Postscript — experiment 0040

The recommended crew slice ran. Earliest-deadline-first scores **260** vs
impact-only **62.4**; nearest scores 223.2; the oracle is 260. The travel kill
rule does **not** trigger. Tabular Q scores 156.4 and fails H4, so the remaining
blocker was the learned baseline, not the spatial mechanic. Experiment 0041
fixes it with a deadline/role state and episodic updates: deadline Q scores
253.2 with success 1.00, +117 over the old Q and 97.4% of EDF. P1 now has a
learned spatial-scheduling result.
