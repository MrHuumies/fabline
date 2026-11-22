# ADR 0025 — Compact layout-aware Q baseline

- **Status:** accepted
- **Date:** 2026-11-22
- **Related:** experiment 0048, task `factory.power.crew-layouts.v1`

## Context

The twin-line crew assignment task (0046) has a real oracle gap, but the old
tabular Q over tick/wire/absolute-distance state scores 217 with zero success.
The learned baseline, not the mechanic, is the blocker.

## Decision

1. Add a compact tabular Q state that encodes only relative crew-target
   geometry and reachability:
   - which crew is closer to each positive bridge;
   - whether each crew can finish before the relevant deadline or recall.
2. Keep the action space, reward, and task contract unchanged.
3. Add `CompactQPolicy` and a `crew-layout-q` CLI that compares it with the old
   tabular Q and the scripted/oracle baselines.
4. Report both pooled per-run success and per-seed mean score; do not
   reinterpret the pre-registered success gate after seeing results.

## Consequences

- The compact state lifts the twin-line mean from 233 to 422 against oracle 442
  (95.5%) and passes the mean quality gate.
- Success is 0.50, below the 0.60 gate; one Q seed matches oracle (442/0.60),
  the other two score 424/0.50 and 400/0.40.
- The representation is the active ingredient, but Q-seed variance and state
  aliasing remain.
- The baseline is diagnostic, not a full H4 closure; no world or benchmark
  behavior changes.

## Follow-ups

- [x] Try a compact-state ensemble or value averaging. Experiment 0050: ensemble
  430 vs oracle 448, success 0.50; variance is reduced, one aliased seed remains.
- [x] Add coarse margin/slack features to reduce aliasing. Negative pilot 0049:
  729 states fragment the table; do not promote.
- [ ] Split A-deadline and B-recall limits before applying the state to 0047.
- [ ] Keep `factory-v0.1` frozen.
