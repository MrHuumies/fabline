# Task card — preventive machine maintenance

- **Task ID:** `factory.fault.preventive.v1`
- **Version:** 0.1.0
- **Status:** P1 debug task; formal run complete; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in faults
- **Owner:** FABLINE
- **Date:** 2026-11-22

## Phenomenon

A machine accumulates wear with each craft. At the fault threshold it fails and
auto-repairs after 60 ticks. Preventive maintenance takes the machine offline
for 10 ticks and resets wear. The agent must decide when planned downtime is
worth avoiding a longer fault.

## Contract

- **Observation:** diagnostics (13 features) plus maintenance count and
  remaining time (2 features).
- **Actions:** noop; maintain the most worn non-faulted machine.
- **Wear threshold:** 20; wear per craft 1.
- **Fault repair:** 60 ticks (auto).
- **Maintenance:** 10 ticks.
- **Reward:** production score delta.
- **Outcome:** final score; success ≥ 240.
- **Episode:** 500 ticks; decision interval 10.

## Metrics

- mean production score (bootstrap CI);
- maintenance count;
- fault count;
- success rate.

## Baselines

| Baseline | Rule |
|---|---|
| noop | never maintain |
| maintain_0.5 | maintain at 10 wear |
| maintain_0.7 | maintain at 14 wear |
| maintain_0.9 | maintain at 18 wear |
| always | maintain whenever wear > 0 |
| random | uniform legal action |
| tabular Q | wear-bucket state; 500 training layouts |

## Gates

| Gate | Threshold |
|---|---|
| H1 prevention gain | best threshold ≥ noop + 30 |
| H2 Q quality | Q ≥ 0.95 × best; success ≥ 0.80 |
| H3 timing | maintain_0.5 ≤ best − 5 |
| H4 seed consistency | report |
| H5 budget | report maintenance/fault counts |

## Results (0037)

Seeds 400–404, 5 episodes each; success ≥ 240.

| policy | score | maintenance | faults | success |
|---|---:|---:|---:|---:|
| noop | 200.0 | 0.0 | 3.0 | 0.00 |
| always | 130.0 | 37.0 | 0.0 | 0.00 |
| random | 179.6 | 22.4 | 0.0 | 0.00 |
| maintain_0.5 | 240.0 | 6.0 | 0.0 | 1.00 |
| maintain_0.7 | **250.0** | 4.0 | 0.0 | **1.00** |
| maintain_0.9 | **250.0** | 3.0 | 0.0 | **1.00** |
| tabular Q | 178.0 | 23.8 | 0.0 | 0.40 |

H1 and H3 pass; **H2 fails** because Q collapses to always-maintain on three of
five seeds. See
[`experiments/0037-preventive-fault`](../experiments/0037-preventive-fault/summary.md).

## Known pitfalls

- **Deterministic line.** Seed variance is low; scores may repeat.
- **Most-worn target only.** The agent does not choose a specific machine.
- **Maintenance blocks work.** The 10-tick downtime is the cost.
- **Faults auto-repair.** Explicit repair is not part of this task.
- **Q is unstable at the delayed trade.** Three seeds collapse to always-maintain.
- **Not part of `factory-v0.1`.**

## Changelog

- 2026-11-22 — card created; maintenance mechanic and gates preregistered.
- 2026-11-22 — formal run: threshold 250; Q 178, H2 fails.
