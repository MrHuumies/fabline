# Experiment 0086 — Two-step transition planning on triage

- **Status:** complete (mixed; see [summary](summary.md))
- **Date:** 2026-11-25
- **Type:** P3 planning/world-model follow-up
- **Task:** `factory.planning.triage.v1` (debug/P3, not in `factory-v0.2`)
- **Code:** `src/fabline/harness/planning_transition.py`
- **CLI:** `python -m fabline planning-transition-two-step`
- **Benchmark:** none; `factory-v0.2` unchanged

## Question

Does two-step transition supervision reduce compounding error enough to improve
CEM planning over the one-step model?

## Hypothesis

0083's one-step model was accurate but its three-step rollout was poor: CEM
162/0.20 vs true 454/1.00. The first two macro-actions account for most of the
compounding. A model trained on `(state, first action, second action) ->
two-step next state` should reduce that error. A one-step model handles the
final action. If pair error is lower, two-step CEM should beat the one-step
planner and approach true CEM.

## Model

- One-step model: 0083 ridge delta model (25-feature state, phase one-hot,
  20-way action one-hot, 25-feature delta + done).
- Two-step model: ridge delta over 25 state + 3 phase + 20 first-action + 20
  second-action one-hots (68 features), predicting the two-step 25-feature
  delta and done flag.
- Planner: two-step model for actions 0→1, one-step model for action 2.
- Ridge penalty 1.0; no nonlinear model, no ensemble, no beta.

## Data and seeds

- Train: seeds 52,000–52,007, all 256 sequences.
- Eval: seeds 53,000–53,001, all 256 sequences.
- Formal planning seeds: 49,000–49,004.
- Variable-length traces are included; pairs are collected only where two
  consecutive decisions exist.

## Conditions

| Condition | Planner |
|---|---|
| `cem_true` | CEM with the true simulator |
| `cem_single` | CEM with the one-step model |
| `cem_two_step` | CEM with two-step + one-step models |
| `scripted_greedy` | outage per service |
| `random_shooting_true` | 128 true-simulator samples |
| `oracle` | exhaustive 16×4×4 |

## Metrics

- one-step MSE and pair MSE vs copy;
- pair done accuracy;
- rollout final-score MSE;
- plan score with 95% bootstrap CI and success;
- planning latency.

## Gates

| Gate | Threshold |
|---|---|
| H1 pair quality | pair MSE < 0.5 × pair copy MSE |
| H2 planning improvement | two-step CEM ≥ one-step CEM + 10 |
| H3 model planning | two-step CEM ≥ true CEM − 10 |
| H4 success | two-step CEM success ≥ 0.60 |
| H5 frozen benchmark | `factory-v0.2` unchanged |

## Predictions

- Pair MSE 0.01–0.04 vs copy ~0.07–0.12; pair done accuracy >0.95.
- Two-step CEM 250–400, success 0.4–0.8.
- H2 may pass; H3/H4 are the real test.

## Kill criteria

- Pair MSE not better than copy: negative model result.
- Two-step CEM not better than one-step + 10: negative planning result.
- No post-hoc feature, ridge, seed, or pair-window tuning.

## Analysis plan

- Report one-step and pair model metrics.
- Report all planning conditions with CIs and success.
- Compare single vs two-step directly and against true CEM.

## Transparency note

A one-seed, eight-sequence smoke on seed 48,000 gave two-step CEM 250 vs
single 90, oracle 430. It is wiring-only and not a formal result. Formal seeds
49,000–49,004 are fresh and shared with 0083/0085.
