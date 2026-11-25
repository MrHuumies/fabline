# Experiment 0083 — Transition-model planning on triage

- **Status:** complete (negative; see [summary](summary.md))
- **Date:** 2026-11-25
- **Type:** P3 planning/world-model follow-up
- **Task:** `factory.planning.triage.v1` (debug/P3, not in `factory-v0.2`)
- **Code:** planned `src/fabline/harness/planning_transition.py`
- **CLI:** planned `python -m fabline planning-transition`
- **Benchmark:** none; `factory-v0.2` unchanged

## Question

Can a learned one-step transition model support CEM planning on three-bridge
triage, or is the true simulator still required?

## Hypothesis

0076 showed that a ridge **value** model is not a world model. A transition
model that predicts the next decision state can be rolled out through the
three macro-actions. If the one-step model is accurate enough, CEM with model
rollouts should recover most of true CEM and beat random shooting.

## Environment and plan

Same task as 0076:

- 32×16 random gear layout, three positive bridges;
- warnings 40; failures 90/110/130; recall 100; job failure 100;
- two replan jobs; success ≥ 300;
- plan `(initial 0..15, replan1 in 0/4/8/12, replan2 in 0/4/8/12)`.

The plan has three macro-transitions:

1. state at the warning + initial pair → state before replan 1;
2. state before replan 1 + first survivor action → state before replan 2;
3. state before replan 2 + second survivor action → terminal state.

## Transition model

A ridge delta model predicts the next 25-feature crew-replan observation from:

- the current 25-feature state;
- a 3-way phase one-hot;
- a 20-way action one-hot (16 initial actions, 4 replan actions).

The target is `next_state - state`. Inputs and deltas are standardized. At
rollout, the model applies the predicted delta, clips the state to [0, 1], and
reads the normalized production score (feature 1) at the terminal state.

## Data and seeds

- Train: seeds 52,000–52,007, all 256 sequences each → 6,144 transitions.
- Eval: seeds 53,000–53,001, all 256 sequences each → 1,536 transitions.
- Formal planning seeds: 49,000–49,004, the same as 0076 for comparison.
- Ridge penalty 1.0.
- No model ensembling and no state augmentation in this slice.

## Conditions

| Condition | Planner |
|---|---|
| `random_shooting_true` | 128 true-simulator samples |
| `cem_true` | CEM with the true simulator |
| `cem_transition` | CEM with the learned transition model |
| `scripted_greedy` | outage per service |
| `scripted_aware` | earliest deadline / outage |
| `oracle` | exhaustive 16×4×4 |

## Metrics

- one-step transition MSE;
- copy baseline MSE (predict no state change);
- rollout final-score MSE on eval sequences;
- plan score with 95% bootstrap CI and success;
- planning latency.

## Gates

| Gate | Threshold |
|---|---|
| H1 transition quality | one-step MSE < 0.5 × copy MSE |
| H2 planning over random | CEM transition ≥ random shooting true + 10 |
| H3 model planning | CEM transition ≥ CEM true − 10 |
| H4 success | CEM transition success ≥ 0.60 |
| H5 frozen benchmark | `factory-v0.2` unchanged |

## Predictions

- One-step MSE well below the copy baseline; the delta model captures score,
  outage, and state changes.
- CEM transition 350–450, success 0.6–1.0.
- H1/H2 likely pass; H3 is the real test. If H3 fails, the world-model gap is
  about rollout error, not planner search.

## Kill criteria

- H1 fails: the transition model is not better than copy; report a negative
  model result.
- H2 fails: model planning is not better than random; report negative.
- No post-hoc feature, phase, action, or seed tuning after the formal block.
- Do not replace the transition model with a value model to rescue H3; 0076
  already closed that shortcut.

## Analysis plan

- Report train/eval one-step MSE and copy MSE.
- Report rollout final-score MSE.
- Report all plan scores with CIs and success.
- Report per-seed CEM transition scores and the best sequences.
- Compare with the 0076 true-planning block.

## Transparency note

The true-simulator and oracle branches reuse the 0076 task definition; only the
planner's model changes. No transition-model pilot has been run yet. A one-seed
smoke on seed 48,000 is allowed after implementation for wiring checks only;
formal seeds 49,000–49,004 are fresh and shared with 0076.
