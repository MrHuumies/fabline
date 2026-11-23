# Experiment 0071 — Recipe choice under power constraints

- **Status:** preregistered (formal run pending)
- **Date:** 2026-11-24
- **Type:** P3 robustness experiment
- **Mechanic:** recipe choice (RFC 0026 / ADR 0037) under a tight opt-in power
  budget (ADR 0038)
- **Task:** `factory.production.recipe-choice.v1`, power capacity 10
- **Code:** `src/fabline/env/recipe.py`, `src/fabline/harness/recipe.py`
- **CLI:** `python -m fabline recipe-choice --power-capacity 10`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a tight power budget change the best recipe policy, or is the queue state
still the dominant decision?

## Pilot

Seeds 38,000–38,002, power capacity 10, success 300:

| policy | mean score |
|---|---:|
| fast | 273.3 |
| slow | 180.0 |
| buffer-aware | 316.7 |
| power-aware (headroom) | 196.7 |
| power-saver (brownout) | 316.7 |
| random | 216.7 |
| one-step lookahead | 273.3 |

Buffer-aware is unchanged from 0070 (318.0 without power). The tight budget
punishes slow and random, but a brownout-aware policy only ties buffer-aware.
Capacity 10 is the interesting regime; 8 is too tight (all policies 146.7), 12+
is not binding (same as 0070).

## Design

- Five fresh seeds: 39,000–39,004.
- 16×8 gear scenario, 500 ticks, decision interval 10.
- Power: one generator, capacity 10, radius 8, radius topology.
- Fast recipe 2 ingots/12 ticks; slow 1/20.
- Initial ingot buffer seeded 0–6.
- Success ≥ 300.

## Gates

| Gate | Threshold |
|---|---|
| H1 queue gain | buffer-aware ≥ fast + 10 |
| H2 power decision | power-saver ≤ buffer-aware + 5 (no new decision) |
| H3 success | buffer-aware success ≥ 0.60 |
| H4 other baselines | buffer-aware ≥ slow/random + 10 |
| H5 robustness | buffer-aware gain within 10 of 0070's +40 (≥ +30) |
| H6 frozen benchmark | unchanged |

H2 is a **negative-interaction** gate: if power-saver beats buffer-aware by 10,
power adds a new decision; otherwise the queue state dominates.

## Predictions

- Buffer-aware 310–325; fast 265–285; slow 180; power-saver 310–325;
  power-aware 190–205; random 200–230.
- H1, H3, H4, H5 pass; H2 shows no new decision.
- If H1 or H5 fails, the power condition is too disruptive; retire it.

## Kill criteria

- Queue gain under +10: negative.
- Buffer-aware gain under +30 (vs 0070): power condition invalid.
- No post-hoc capacity or threshold tuning.

## Transparency note

The pilot used seeds 38,000–38,002 and a capacity sweep. The formal block is
fresh 39,000–39,004 at capacity 10. The pilot is not a confirmation.
