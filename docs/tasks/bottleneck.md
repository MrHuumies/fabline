# Task card — bottleneck classification

- **Task ID:** `factory.bottleneck.classify.v1`
- **Version:** 0.1.0
- **Status:** benchmark candidate (`factory-v0.1`)
- **World:** factory-0.1.0
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Identify which entity type is the causal bottleneck: the type whose removal
reduces future depot score the most. This is a counterfactual label derived
from the simulator, not a hand-written heuristic.

## Contract

- **Observation:** `vector` (18 features).
- **Action:** none; offline classification over shared episodes.
- **Label:** for each non-depot entity, remove it in a clone and compare the
  next 30 ticks of depot score to the unmodified baseline. The entity type with
  the largest positive drop is the label. If no removal reduces score, the
  label is `none`.
- **Classes:** `miner`, `belt`, `furnace`, `assembler`, `none`.
- **Splits:** same scenario plan as throughput.
- **Metrics:** accuracy, balanced accuracy, macro F1 with 95% bootstrap
  confidence intervals.
- **Baselines:** majority, GBDT, MLP.

## Data — `factory-v0.1`

- 46 episodes, 852 samples.
- Class distribution: assembler 323, belt 101, furnace 428.
- No `none` samples in this benchmark; all recorded lines produce output.
- Test: 110 samples; shift: 110 samples.

## Results — `factory-v0.1`

Test:

| method | accuracy | balanced accuracy |
|---|---:|---:|
| majority | 0.127 | 0.333 |
| GBDT | **0.827** | **0.772** |
| MLP | 0.700 | 0.333 |

Shift:

| method | accuracy | balanced accuracy |
|---|---:|---:|
| majority | 0.182 | 0.333 |
| GBDT | **0.982** | **0.992** |
| MLP | 0.745 | 0.333 |

## Known pitfalls

- **Counterfactual label depends on the horizon and removal policy.** Removing
  an entity also destroys its buffered items; that is part of the intervention.
- **Class imbalance.** Furnace and assembler dominate; balanced accuracy is the
  honest metric. The MLP collapses to the majority class on balanced accuracy.
- **Small test split.** 110 samples; CIs are wide.
- **No `none` examples.** A broken-line variant should be added before claiming
  the `none` class works.
- **Entity type, not entity identity.** The task does not ask which specific
  belt is the bottleneck.

## Negative controls

- Majority should be weak on balanced accuracy.
- A model that predicts the most common class should not beat GBDT on balanced
  accuracy.

## Changelog

- 2026-11-21 — card created; M3 results added.
