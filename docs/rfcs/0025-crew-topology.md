# Mechanic RFC 0025 — Random-topology triage

- **Status:** pilot accepted for formal test
- **Author:** FABLINE
- **Date:** 2026-11-23
- **Related:** ADR 0036, RFC 0017, ADR 0028, experiment 0067

## Summary

Add an opt-in 48×24 random-topology layout for the three-bridge survivor
triage. Three production lines are placed at random y rows and full-width
random x starts; each line has one extra belt. The wire graph is the existing
seeded spanning tree. The task keeps the 0055 triage rules: warnings 40,
failures 90/110/130, failure and recall 100, two survivor jobs, success ≥ 300.

## Motivation

The twin-line 0055 and spread 0059 layouts are controlled. The P2 review lists
larger/random topology as the remaining structural gap. A 5-seed pilot on
27,000–27,004 compared spread and random layouts:

- spread: per-seed oracle over best scripted = 0, 90, 0, 0, 0; mean +18;
- random: 0, 50, 50, 30, 40; mean +34.

The random layout is harder in absolute score and the gap is present on 4/5
seeds. The paired difference is +16 on average, with one negative seed. The
formal test uses fresh seeds 28,000–28,004.

## Rules

- 48×24 map, three production lines.
- Random line rows (at least two apart) and full-width random x starts.
- One extra belt per line; no band constraint.
- Existing seeded wire graph, capacity 24, radius 8, redundancy 2.
- Triage: three positive bridges, warnings 40, failures 90/110/130.
- Failure and B recall at 100; A gets two survivor jobs.
- Random crew-B base at least eight cells from A.
- Reward: final production score; success ≥ 300.

## Observation and action impact

The action space and observation features are unchanged from 0055. Only the
layout generator scenario changes.

## Data impact

- New task preset `factory.power.crew-topology.v1`.
- New scenario `random_topology`; default scenarios are unchanged.
- Frozen `factory-v0.1` is unchanged.

## Tests

- Deterministic `random_topology` generation.
- Three miners and three depots.
- Non-empty wire graph.
- Existing scenario hashes unchanged.
- Frozen benchmark regression.

## Alternatives

- **Spread bands (0059).** Negative; greedy matched oracle.
- **Twin-line (0055).** Positive but controlled.
- **True random graph topology.** Larger mechanic; deferred until this layout
  shows a new decision.

## Decision

Pilot accepted for formal 0067. If the random layout does not beat the spread
control's per-seed gap by 10 points, close the P2 topology axis and move to P3.
