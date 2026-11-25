# Experiment 0086 — Two-step transition planning on triage

- **Status:** complete (mixed: two-step improves CEM, but gate fails)
- **Date:** 2026-11-25
- **Type:** P3 planning/world-model follow-up
- **Task:** `factory.planning.triage.v1` (debug/P3, not in `factory-v0.2`)
- **Code:** `src/fabline/harness/planning_transition.py`
- **CLI:** `python -m fabline planning-transition-two-step`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**Two-step supervision improves the model planner, but not enough.** Pair MSE is
**0.0556** against pair copy **0.1228** (H1 passes narrowly), and two-step CEM
improves the single-model planner from **162/0.20** to **188/0.40** (H2 passes).
But it remains far below true CEM **442/1.00** and misses the 0.60 success gate.
H1/H2/H5 pass; H3/H4 fail. Together with 0085 (184/0.40), this suggests a
practical ceiling for this linear transition-model family on the task. Do not
tune the pair window or model after this block.

## Model

- One-step ridge delta model (0083).
- Two-step ridge delta model over state + phase + first/second action (68
  features), predicting the two-step delta and done flag.
- Planner: two-step model for actions 0→1, one-step model for action 2.

| Metric | Value |
|---|---:|
| Train transitions / pairs | 5,380 / 3,332 |
| Eval transitions / pairs | 1,356 / 844 |
| One-step MSE | 0.0182 |
| Pair MSE | 0.0556 |
| Pair copy MSE | 0.1228 |
| Pair done accuracy | 0.986 |
| Rollout MSE | 31,652.61 |

## Planning results

Seeds 49,000–49,004:

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| scripted greedy | 398.00 | [300.95, 452.00] | 0.80 |
| scripted aware | 292.00 | [240.00, 352.00] | 0.40 |
| random shooting true | 454.00 | [419.90, 484.00] | 1.00 |
| CEM true | 442.00 | [394.00, 480.00] | 1.00 |
| CEM single model | 162.00 | [72.00, 252.00] | 0.20 |
| **CEM two-step** | **188.00** | **[76.00, 300.00]** | **0.40** |
| oracle | 454.00 | [419.90, 484.00] | 1.00 |

Per-seed two-step: `380, 60, 140, 300, 60`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 pair quality | pair MSE < 0.5 × copy | **pass**, 0.453× |
| H2 planning improvement | two-step ≥ single + 10 | **pass**, +26 |
| H3 model planning | two-step ≥ true CEM − 10 | **fail**, 188 vs 442 |
| H4 success | two-step success ≥ 0.60 | **fail**, 0.40 |
| H5 frozen benchmark | `factory-v0.2` unchanged | **pass** |

## Interpretation

- **Two-step training reduces compounding somewhat.** The planner improves
  +26 over the one-step model and doubles success to 0.40.
- **The improvement is shallow and converges with the ensemble.** 0085's
  uncertainty ensemble is 184/0.40; two-step is 188/0.40. Two different fixes
  hit the same range.
- **The linear transition family is likely at its ceiling here.** The terminal
  score remains too sensitive to compounding and model bias.
- **This is a model-class result, not a task failure.** True CEM and oracle are
  442–454; the task remains valid.
- **Do not add another pair window or linear variant.** A nonlinear model or a
  different state representation is a new pre-registration.

## Caveats

- One ridge two-step model; no nonlinear model, ensemble, or uncertainty.
- One pair window (actions 0→1).
- Variable-length traces; pair data are fewer than transitions.
- Random shooting is at the oracle ceiling on these seeds.
- No post-hoc tuning.

## Next

1. Close the linear transition-model line: one-step 162, ensemble 184,
   two-step 188, true 442.
2. Either take the optional generative pilot or build the public efficiency
   table.
3. A nonlinear transition model is a new pre-registration, not a tune of
   0083/0085/0086.
4. Keep `factory-v0.2` and `v0.3.0` unchanged.

## Artifacts

- Task card: [`../../tasks/planning-triage.md`](../../tasks/planning-triage.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/planning_transition.py`
- Raw results: `results/planning-transition-two-step/` (ignored)
