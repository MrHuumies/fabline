# Experiment 0085 — Uncertainty-aware transition ensemble on triage

- **Status:** complete (mixed: uncertainty helps, but planning gate fails)
- **Date:** 2026-11-25
- **Type:** P3 planning/world-model follow-up
- **Task:** `factory.planning.triage.v1` (debug/P3, not in `factory-v0.2`)
- **Code:** `src/fabline/harness/planning_transition.py`
- **CLI:** `python -m fabline planning-transition-ensemble`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**Ensemble uncertainty is informative and improves the planner, but not nearly
enough.** Eight bootstrap ridge models have one-step MSE **0.0191** against copy
**0.0695**, and the ensemble std correlates with rollout error at Spearman
**0.320**. Pessimistic CEM improves the single-model planner from **166/0.20**
to **184/0.40**, passing the +10 improvement gate. But it is still far below true
CEM **442/1.00** and misses the 0.60 success gate. H1/H2/H3/H6 pass; H4/H5 fail.
Do not tune beta, member count, or the model after this block.

## Model

- 8 bootstrap ridge delta models; ridge 1.0.
- One-step MSE 0.0191; copy 0.0695; done accuracy 0.997.
- Ensemble rollout MSE 7,801.
- Uncertainty Spearman 0.320 (std vs absolute rollout error).

## Planning results

Seeds 49,000–49,004:

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| scripted greedy | 398.00 | [300.95, 452.00] | 0.80 |
| scripted aware | 292.00 | [240.00, 352.00] | 0.40 |
| random shooting true | 454.00 | [419.90, 484.00] | 1.00 |
| CEM true | 442.00 | [410.00, 476.00] | 1.00 |
| CEM single model | 166.00 | [76.00, 256.00] | 0.20 |
| **CEM ensemble** | **184.00** | **[72.00, 300.00]** | **0.40** |
| oracle | 454.00 | [419.90, 484.00] | 1.00 |

Per-seed ensemble: `380, 60, 120, 300, 60`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 transition quality | one-step MSE < 0.5 × copy | **pass**, 0.275× |
| H2 uncertainty signal | Spearman > 0.20 | **pass**, 0.320 |
| H3 ensemble improvement | ensemble ≥ single + 10 | **pass**, +18 |
| H4 model planning | ensemble ≥ true CEM − 10 | **fail**, 184 vs 442 |
| H5 success | ensemble success ≥ 0.60 | **fail**, 0.40 |
| H6 frozen benchmark | `factory-v0.2` unchanged | **pass** |

## Interpretation

- **Pessimism works directionally.** The ensemble avoids one bad sequence and
  doubles success from 0.20 to 0.40.
- **Uncertainty is only partially informative.** Spearman 0.32 means std
  separates some bad rollouts, but not enough to rank plans reliably.
- **Rollout error is still the binding problem.** Mean rollout MSE 7,801;
  ensemble planning remains 258 below true CEM.
- **This is a model/rollout negative, not a task negative.** True CEM and
  random shooting are at 442–454; the task remains valid.
- **Do not tune the ensemble.** A multi-step or nonlinear model is a new
  pre-registration, not a beta/K sweep.

## Caveats

- Eight linear ridge members; no nonlinear members or learned dynamics.
- One beta (1.0) and one ensemble seed.
- One layout family and planning block.
- Random shooting is at the oracle ceiling on these seeds.
- The 0083 single-model reference is 162/0.20; the paired rerun here is
  166/0.20, so the improvement is measured against 166.

## Next

1. The uncertainty ensemble is a positive mechanism but not a usable planner.
2. A **multi-step or nonlinear transition model** is the next world-model
   pre-registration; do not tune 0085.
3. Alternatively, take the optional generative pilot or build the public
   efficiency table.
4. Keep `factory-v0.2` and `v0.3.0` unchanged.

## Artifacts

- Task card: [`../../tasks/planning-triage.md`](../../tasks/planning-triage.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/planning_transition.py`
- Raw results: `results/planning-transition-ensemble/` (ignored)
