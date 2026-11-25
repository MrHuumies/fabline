# Experiment 0083 — Transition-model planning on triage

- **Status:** complete (negative: one-step model does not survive rollout)
- **Date:** 2026-11-25
- **Type:** P3 planning/world-model follow-up
- **Task:** `factory.planning.triage.v1` (debug/P3, not in `factory-v0.2`)
- **Code:** `src/fabline/harness/planning_transition.py`
- **CLI:** `python -m fabline planning-transition`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**The one-step transition model is accurate but not useful for planning.**
One-step MSE is **0.0182** against a copy baseline of **0.0695**, and the done
classifier is perfect on the eval traces. Rollout MSE is still **7,877**
(RMSE ≈ 88.8), and CEM with model rollouts scores **162** with success **0.20**,
versus true CEM **454/1.00** and oracle **454/1.00**. H1 passes; H2, H3, and H4
fail. The result is a negative world-model result: one-step accuracy does not
survive three-step compounding error on this task. The model is not tuned after
the formal block.

## Model

Ridge delta model over the 25-feature crew-replan state, phase one-hot, and
20-way action one-hot; predicts the 25-feature delta plus a done flag.

| Metric | Value |
|---|---:|
| Train transitions | 5,380 |
| Eval transitions | 1,356 |
| One-step MSE | 0.0182 |
| Copy MSE | 0.0695 |
| One-step ratio | 0.262 |
| Done accuracy | 1.000 |
| Rollout MSE | 7,877.46 |

The transition count is lower than 6,144/1,536 because some sequences finish
after one or two decisions; those traces are included with their actual length.

## Planning results

Seeds 49,000–49,004:

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| scripted greedy | 398.00 | [300.95, 452.00] | 0.80 |
| scripted aware | 292.00 | [240.00, 352.00] | 0.40 |
| random shooting true | 454.00 | [419.90, 484.00] | 1.00 |
| CEM true | 454.00 | [419.90, 484.00] | 1.00 |
| **CEM transition** | **162.00** | **[72.00, 252.00]** | **0.20** |
| oracle | 454.00 | [419.90, 484.00] | 1.00 |

Per-seed CEM transition: `270, 60, 120, 300, 60`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 transition quality | one-step MSE < 0.5 × copy | **pass**, 0.262× |
| H2 planning over random | CEM transition ≥ random shooting + 10 | **fail**, 162 vs 454 |
| H3 model planning | CEM transition ≥ CEM true − 10 | **fail**, 162 vs 454 |
| H4 success | CEM transition success ≥ 0.60 | **fail**, 0.20 |
| H5 frozen benchmark | `factory-v0.2` unchanged | **pass** |

**H2 caveat:** on these seeds, 128-sample random shooting already reaches the
oracle (454), so H2 as written is not informative. The substantive failures are
H3 and H4.

## Interpretation

- **One-step accuracy is not rollout accuracy.** The model predicts the next
  state well on held-out transitions, but small errors compound over three
  macro-steps. The terminal score is especially sensitive.
- **CEM exploits the model.** The planner selects sequences with high predicted
  scores that are not high true scores; the best model sequences are
  `[11,12,12]`, `[7,12,12]`, and `[7,12,4]`, which are poor in the simulator.
- **This is a model/rollout negative, not a task negative.** True CEM and
  random shooting both reach 454; the task remains valid.
- **A one-step ridge model is a weak world model.** Multi-step training,
  uncertainty, or a transition model with a terminal-score head is a new
  experiment, not a fix to this one.

## Caveats

- One ridge delta model; no ensembling, uncertainty, or multi-step loss.
- One layout family and one planning block.
- Random shooting is at the oracle ceiling on these seeds; the 62k benchmark
  seeds had a wider random-shooting gap.
- Variable-length traces (1–3 decisions) are included; the model predicts a
  done flag.
- No post-hoc feature, ridge, or seed tuning.

## Next

1. **Maintenance calibration** is the cheap fallback: add Brier/NLL/ECE to the
   existing preventive-maintenance task.
2. A **new transition-model pre-registration** would need multi-step training
   or uncertainty; do not tune this ridge model.
3. Keep `factory-v0.2` and `v0.3.0` unchanged.

## Artifacts

- Task card: [`../../tasks/planning-triage.md`](../../tasks/planning-triage.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/planning_transition.py`
- Raw results: `results/planning-transition/` (ignored)
