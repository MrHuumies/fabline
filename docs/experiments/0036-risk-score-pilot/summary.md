# Pilot 0036 — Risk-score noise for preventive wire repair

- **Status:** pilot negative; not promoted to a formal experiment
- **Date:** 2026-11-22
- **Type:** exploratory pilot
- **Mechanic:** preventive wire maintenance (RFC 0008, ADR 0018)
- **Code:** `experiments/wired_power/risk_wire.py`,
  `experiments/wired_power/risk_pilot.py`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does the quality of a failure-risk score change the preventive repair decision?

Experiment 0035 showed a perfect warning is actionable. This pilot adds a risk
score and noise: two equal-outage bridges are degraded, exactly one will fail,
and the score estimates which one. The agent has one repair budget and chooses
bridge A, bridge B, or noop.

## Setup

- Two bridges with equal positive outage; A and B.
- True failure probability `p ~ Uniform(0.05, 0.95)`; A fails with probability
  `p`, otherwise B.
- Observed score `clip(p + N(0, sigma), 0, 1)`.
- Warning at 60; failure at 220; repair 140 ticks; budget 1.
- Policies: noop, always A, always B, threshold 0.5, oracle, random.
- 10 seeds per condition.

## Results

| noise | policy | score | prevented | false alarms |
|---:|---|---:|---:|---:|
| 0.00 | noop | 116.0 | 0 | 0 |
| 0.00 | always A | 215.0 | 7 | 3 |
| 0.00 | always B | 161.0 | 3 | 7 |
| 0.00 | threshold 0.5 | **233.0** | **8** | 2 |
| 0.00 | oracle | 260.0 | 10 | 0 |
| 0.25 | threshold 0.5 | 230.0 | 8 | 2 |
| 0.50 | threshold 0.5 | 230.0 | 8 | 2 |
| 2.00 | threshold 0.5 | 203.0 | 6 | 4 |

Always-A, always-B, noop, oracle, and random are unchanged across noise levels.

## Why it is not promoted

- **The prediction effect is small.** The threshold policy beats always-A by 18
  score points, and the oracle ceiling is 45 points above it.
- **Noise barely matters until it is extreme.** At sigma 0.25 and 0.5 the
  threshold score is unchanged (230); only sigma 2.0 degrades it to 203.
- **The decision is dominated by the prior.** With equal outages and uniform
  `p`, always-A is already a reasonable policy; the score only shifts a few
  choices.
- **The action structure is too simple.** One repair, two wires, and symmetric
  costs do not create a sharp precision/recall trade.

A formal run would not have a meaningful gate. Do not add it to the benchmark
surface.

## Next

- **Normal machine-wear prevention:** use the existing wear signal and a
  maintenance action; this is the other half of the preventive-repair idea.
- **Multi-wire preventive scheduling:** several warnings, one crew, asymmetric
  outage costs.
- **Noisy prediction with multiple true failures:** a task where a false alarm
  can miss a different real failure, not just spend a repair.

## Artifacts

- Code: `experiments/wired_power/risk_wire.py`,
  `experiments/wired_power/risk_pilot.py`
- Raw output: not committed
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
