# Experiment 0076 — Triage planning

- **Status:** preregistered (formal run pending)
- **Date:** 2026-11-24
- **Type:** P3 planning/world-model experiment
- **Task:** `factory.planning.triage.v1` (debug/P3, not in `factory-v0.1`)
- **Code:** `src/fabline/harness/planning_triage.py`
- **CLI:** `python -m fabline planning-triage`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Can a planner improve on scripted triage, and can a learned score model support
the same planning?

## Pilot

Seeds 48,000–48,004, population 16/elites 4/iterations 4/40 samples, model
trained on 2 exhaustive seeds:

| policy | mean score | success |
|---|---:|---:|
| random | 234 | 0.00 |
| scripted greedy | 336 | 0.40 |
| scripted aware | 390 | 0.80 |
| random shooting true | 414 | 0.80 |
| **CEM true** | **418** | **0.80** |
| **oracle** | **418** | **0.80** |
| CEM learned (ridge) | 302 | 0.40 |

True planning reaches the oracle; scripted aware is 28 below and loses one seed
by 140. The ridge model does not plan well. An exploratory GBDT score model was
also poor (CEM learned 90/410/220/100/140 across the five seeds).

## Environment

- 32×16 twin-line triage, random crew-B base.
- Warning 40; failures 90/110/130; failure and recall 100.
- Two survivor jobs; success ≥ 300.
- Sequence: initial 0..15, replan 0/4/8/12, replan 0/4/8/12.
- Oracle: 256 sequences.

## Data and seeds

- Pilot: 48,000–48,004.
- Formal: 49,000–49,004 (fresh).
- Model training: 8 exhaustive seeds from a disjoint block (2,048 sequences).
- Model eval: 300 random held-out sequences.
- No dataset artifact.

## Gates

| Gate | Threshold |
|---|---|
| H1 planning over random | CEM true ≥ random + 10 |
| H2 learned planning | CEM learned ≥ random + 10 |
| H3 model quality | CEM learned within 10 of CEM true |
| H4 success | CEM true success ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Predictions

- CEM true 410–430; oracle equal; scripted aware 380–400.
- H1/H4 pass; H3 fails (score model).
- If CEM true equals oracle, report a planning ceiling; the learned model is the
  open world-model problem.

## Analysis plan

- Report all baselines with score/CI/success and planning seconds.
- Report model MSE and best sequences.
- No post-hoc changes to the path, action encoding, or seeds.

## Kill criteria

- CEM true under random +10: planning task not diagnostic.
- CEM learned under random +10: model planning fails.
- No post-hoc model or CEM tuning.

## Transparency note

The pilot used 48,000–48,004 and a smaller CEM budget. The formal block is fresh
49,000–49,004 with the default budget. The pilot's +28 over aware is not a
confirmation.
