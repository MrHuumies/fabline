# Task card — triage planning

- **Task ID:** `factory.planning.triage.v1`
- **Version:** 0.1.0
- **Status:** P3 planning task; formal true planning positive; learned value
  model and transition model negative; included in `factory-v0.2`
- **World:** factory-0.1.0, 32×16 twin-line triage
- **Owner:** FABLINE
- **Date:** 2026-11-24

## Phenomenon

Three bridges fail on a staggered schedule. The agent plans an initial A/B pair
and two A survivor actions, then executes the sequence. The task tests whether a
planner can improve on scripted triage and whether a learned score model can
support the same planning.

## Contract

- **Observation:** 25 crew-replan features.
- **Plan:** `(initial 0..15, replan1 in 0/4/8/12, replan2 in 0/4/8/12)`.
- **Execution:** wait for warning 40, apply the initial pair, then apply the two
  replan actions in phase.
- **Reward:** final production score; success ≥ 300.
- **Environment:** the existing 0055 triage settings (failures 90/110/130,
  recall 100, two survivor jobs).

## Baselines

| Baseline | Rule |
|---|---|
| scripted greedy | outage per service |
| scripted aware | earliest deadline / outage survivor |
| random | random legal sequence |
| random shooting (true) | 128 sampled sequences |
| CEM (true) | categorical CEM with the simulator |
| CEM (learned) | CEM with a ridge score model |
| oracle | exhaustive 16×4×4 sequences |

## Metrics

- true score, CI, success;
- planning seconds;
- learned-model MSE;
- best sequence.

## Gates

| Gate | Threshold |
|---|---|
| H1 planning over random | CEM true ≥ random + 10 |
| H2 learned planning | CEM learned ≥ random + 10 |
| H3 model quality | CEM learned within 10 of CEM true |
| H4 success | CEM true success ≥ 0.60 |
| H5 frozen benchmark | unchanged |

The score model is a **value model**, not a transition world model. H3 tests
whether the value model is sufficient; a failure is a world-model result, not a
planning-task failure.

## Known pitfalls

- Scripted aware is near oracle on some seeds.
- The exhaustive oracle is small (256 sequences).
- A score model is not a transition model; do not overclaim.
- Not part of `factory-v0.1`.

## Results (0076)

Seeds 49,000–49,004.

| policy | mean score | success |
|---|---:|---:|
| random | 188.0 | 0.20 |
| scripted aware | 292.0 | 0.40 |
| scripted greedy | 398.0 | 0.80 |
| random shooting true | 422.0 | 0.80 |
| **CEM true** | **454.0** | **1.00** |
| **oracle** | **454.0** | **1.00** |
| CEM learned (ridge) | 166.0 | 0.20 |

H1/H4/H5 pass; H2/H3 fail. See
[`experiments/0076-planning-triage`](../experiments/0076-planning-triage/summary.md).

On the `factory-v0.2` seeds (62,000–62,004), CEM true is 462 = oracle, random
108, and CEM learned 232. H2 passes there, but H3 still fails: the learned value
model is far below the true planner. The value model remains a negative
baseline; do not treat H2 as a world-model success.

## Follow-up (0083)

Experiment 0083 preregisters a true transition model:

- ridge delta model over the 25-feature decision state, phase one-hot, and
  20-way action one-hot;
- predicts the 25-feature delta plus a done flag;
- trained on 8 seeds × 256 sequences (52,000–52,007);
- CEM rolls out the model over the three macro-actions;
- gates: one-step MSE < 0.5 × copy; model CEM ≥ random shooting + 10, within
  10 of true CEM, and success ≥ 0.60.

See
[`experiments/0083-transition-planning/preregistration.md`](../experiments/0083-transition-planning/preregistration.md).

### Results (0083)

Seeds 49,000–49,004; 8 training seeds and 2 eval seeds:

| policy | mean score | success |
|---|---:|---:|
| CEM true | 454 | 1.00 |
| random shooting true | 454 | 1.00 |
| CEM transition (ridge delta) | 162 | 0.20 |
| oracle | 454 | 1.00 |

One-step MSE 0.0182 vs copy 0.0695; done accuracy 1.000; rollout MSE 7,877.
H1 passes; H2/H3/H4 fail. One-step accuracy does not survive the three-step
rollout. See
[`experiments/0083-transition-planning/summary.md`](../experiments/0083-transition-planning/summary.md).

## Follow-up (0085)

Experiment 0085 preregisters an uncertainty-aware transition ensemble:

- 8 bootstrap ridge delta models;
- CEM objective `mean − 1.0 × std` over member terminal scores;
- same task, train/eval data, and formal seeds as 0083;
- gates: uncertainty Spearman > 0.20, ensemble CEM ≥ single CEM + 10,
  ensemble CEM ≥ true CEM − 10, success ≥ 0.60.

See
[`experiments/0085-transition-ensemble/preregistration.md`](../experiments/0085-transition-ensemble/preregistration.md).

### Results (0085)

8 bootstrap members, beta 1.0:

| policy | mean score | success |
|---|---:|---:|
| CEM single model | 166 | 0.20 |
| CEM ensemble | 184 | 0.40 |
| CEM true | 442 | 1.00 |
| oracle | 454 | 1.00 |

One-step MSE 0.0191; uncertainty Spearman 0.320. H3 passes (+18 over single),
but H4/H5 fail: the ensemble is still far below true CEM and success 0.60.
See
[`experiments/0085-transition-ensemble/summary.md`](../experiments/0085-transition-ensemble/summary.md).

## Changelog

- 2026-11-24 — task card created; planning baselines and gates defined.
- 2026-11-24 — formal run: CEM true 454 = oracle; learned value model 166
  (negative).
