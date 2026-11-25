# Experiment 0085 — Uncertainty-aware transition ensemble on triage

- **Status:** complete (mixed; see [summary](summary.md))
- **Date:** 2026-11-25
- **Type:** P3 planning/world-model follow-up
- **Task:** `factory.planning.triage.v1` (debug/P3, not in `factory-v0.2`)
- **Code:** planned additions to `src/fabline/harness/planning_transition.py`
- **CLI:** planned `python -m fabline planning-transition-ensemble`
- **Benchmark:** none; `factory-v0.2` unchanged

## Question

Does bootstrap ensemble disagreement fix the model-exploitation failure of the
one-step transition planner?

## Hypothesis

0083 showed high one-step accuracy but poor rollout: CEM selected sequences with
high predicted scores and low true scores. An ensemble of transition models can
estimate predictive uncertainty; penalizing high-disagreement sequences should
make CEM choose safer plans. If uncertainty is meaningful, ensemble CEM should
beat the single-model CEM and approach true CEM.

## Environment and plan

Same as 0083:

- 32×16 random gear layout, three positive bridges;
- warnings 40; failures 90/110/130; recall 100; job failure 100;
- two replan jobs; success ≥ 300;
- plan `(initial 0..15, replan1 0/4/8/12, replan2 0/4/8/12)`.

## Model ensemble

- Base model: ridge delta transition model from 0083 (25-feature state, phase
  one-hot, 20-way action one-hot, 25-feature delta + done flag).
- Train **8 bootstrap members** on the 0083 training transition set (8 seeds ×
  all 256 sequences; 5,380 variable-length transitions).
- Each member sees a bootstrap sample of transitions; ridge penalty 1.0.
- Rollout score: mean terminal score across members.
- Planning objective: `mean − 1.0 × std` across member terminal scores.
- No per-member architecture changes and no beta/K tuning after the formal run.

## Data and seeds

- Train: seeds 52,000–52,007, all 256 sequences.
- Eval: seeds 53,000–53,001, all 256 sequences.
- Formal planning seeds: 49,000–49,004.
- Ensemble seed: 20261125.
- Single-model reference: 0083's `cem_transition` (162/0.20).

## Conditions

| Condition | Planner |
|---|---|
| `cem_true` | CEM with the true simulator |
| `cem_single` | CEM with the 0083 single transition model |
| `cem_ensemble` | CEM with mean − std ensemble rollouts |
| `scripted_greedy` | outage per service |
| `random_shooting_true` | 128 true-simulator samples |
| `oracle` | exhaustive 16×4×4 |

## Metrics

- one-step MSE and copy MSE;
- ensemble mean rollout MSE;
- Spearman correlation between ensemble std and absolute rollout error;
- plan score with 95% bootstrap CI and success;
- planning latency.

## Gates

| Gate | Threshold |
|---|---|
| H1 transition quality | one-step MSE < 0.5 × copy MSE |
| H2 uncertainty signal | Spearman(std, absolute error) > 0.20 |
| H3 ensemble improvement | ensemble CEM ≥ single CEM + 10 |
| H4 model planning | ensemble CEM ≥ true CEM − 10 |
| H5 success | ensemble CEM success ≥ 0.60 |
| H6 frozen benchmark | `factory-v0.2` unchanged |

## Predictions

- H1 passes; one-step MSE remains around 0.018.
- H2 uncertain: bootstrap std may be weakly correlated with error.
- Ensemble CEM 250–400, success 0.4–0.8.
- H3/H4 are the real test; if H2 is weak, pessimism cannot help.

## Kill criteria

- H2 fails: uncertainty is not informative; report a negative ensemble result.
- H3 fails: ensemble does not improve planning.
- H4/H5 fail: model planning remains below true CEM.
- No post-hoc beta, member count, feature, or seed tuning.

## Analysis plan

- Report model metrics and ensemble uncertainty calibration.
- Report all planning conditions with CIs and success.
- Report per-seed ensemble CEM and best sequences.
- Compare single vs ensemble directly.

## Transparency note

The ensemble uses the same transition data and task as 0083; only uncertainty and
the planning objective change. No ensemble pilot has been run yet. A one-seed
smoke on seed 48,000 is allowed for wiring only; formal seeds 49,000–49,004 are
fresh and shared with 0083.
