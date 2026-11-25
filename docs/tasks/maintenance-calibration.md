# Task card — maintenance-risk calibration

- **Task ID:** `factory.fault.maintenance_calibration.v1`
- **Version:** 0.1.0
- **Status:** P3 calibration task; formal mixed; not in `factory-v0.2`
- **World:** factory-0.1.0 + opt-in faults, preventive-maintenance environment
- **Owner:** FABLINE
- **Date:** 2026-11-25

## Phenomenon

Preventive maintenance depends on fault risk. A probabilistic model should say
when a fault is likely, not just classify a deterministic threshold. The task
samples a lightly maintained line and asks for the probability of a fault in the
next 10 ticks under no further maintenance.

## Contract

- **Observation:** 15 features: 13 diagnostics + maintenance count + remaining
  maintenance time.
- **Behavior:** 5% random maintenance, 95% noop, seeded per episode.
- **Label:** `fault_started` within 10 ticks under no further maintenance.
- **Episode:** 500 ticks; sample every 10 ticks after 100 warmup.
- **Splits:** episode-grouped 70/20/10.
- **Models:** majority, GBDT, MLP probabilistic classifiers.
- **Metrics:** accuracy/balanced accuracy, Brier, NLL, ECE.

## Gates

| Gate | Threshold |
|---|---|
| H1 skill | GBDT balanced accuracy ≥ 0.75 |
| H2 calibration | GBDT ECE ≤ 0.05 |
| H3 view relevance | GBDT balanced ≥ majority + 0.20 |
| H4 base caveat | report positive/majority |
| H5 frozen benchmark | unchanged |

## Results (0084)

60 episodes, seeds 61,000–61,059; 2,400 samples; positive rate 0.575.

| view | model | balanced | ECE |
|---|---|---:|---:|
| diagnostics | GBDT | 0.9969 | 0.0054 |
| diagnostics + maintenance | GBDT | 0.8925 | 0.0929 |
| diagnostics + maintenance | MLP | 0.8977 | 0.0272 |

H1/H3 pass; **H2 fails** for the registered full-view GBDT (ECE 0.0929). The
diagnostics-only view is calibrated but was not the registered primary view.
The pilot ECE 0.014 did not replicate. See
[`experiments/0084-maintenance-calibration`](../experiments/0084-maintenance-calibration/summary.md).

## Known pitfalls

- The full view's maintenance features can make GBDT overconfident.
- The diagnostics-only view is near the skill ceiling.
- The 5% behavior policy is a state-distribution generator, not a deployment
  policy.
- The label is counterfactual (no further maintenance), not the behavior
  policy's realized outcome.
- Test split is 240 samples / 6 episodes.
- Do not tune the view or horizon after the formal block.

## Changelog

- 2026-11-25 — task card created; pilot and gates defined.
- 2026-11-25 — formal mixed: diagnostics GBDT ECE 0.0054; full-view GBDT ECE
  0.0929, H2 fails.
