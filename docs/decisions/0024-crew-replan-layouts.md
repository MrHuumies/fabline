# ADR 0024 — Recall/replanning on twin-line layouts

- **Status:** accepted
- **Date:** 2026-11-22
- **Related:** RFC 0014, RFC 0012, ADR 0022, RFC 0013, ADR 0023, experiment 0047

## Context

The crew recall task is positive on the 16×8 layout but nearest is within 6
points of oracle. The twin-line layout makes assignment non-trivial (oracle 441
vs greedy 419, nearest 361), but does not include crew loss. Combining the two
accepted mechanics tests recovery under a harder spatial assignment.

## Decision

1. Define `factory.power.crew-replan-layouts.v1` as the twin-line layout with
   the recall/replanning contract.
2. Reuse `CrewReplanEnv`; no new action or observation semantics.
3. Set 32×16, twin lines, random crew B (min distance 8), generator capacity 24,
   warning 40, failures 90/110/130, recall 100, success 400.
4. Compare noop, single EDF, nearest, greedy, recall-aware, no-replan, random,
   oracle, and tabular Q.
5. Keep the task opt-in and outside frozen `factory-v0.1`.

## Alternatives considered

- **Recall on 16×8 only.** Already 0045; nearest is near-ceiling.
- **Twin-line assignment only.** Already 0046; no recovery decision.
- **Full random topology.** Deferred.

## Consequences

- The first assignment and the survivor's recovery are both nonlocal.
- The task is harder and has wider score variance than 0045.
- If recovery does not add 10 points over no-replan, the recall mechanic does
  not survive the larger layout.
- If the oracle does not beat the best scripted policy by 10, the layout
  combination is not adding assignment difficulty.
- Q may fail; report it without tuning on evaluation seeds.

## Follow-ups

- [ ] Implement the CLI preset and task card.
- [ ] Pilot and experiment 0047.
- [ ] Keep `factory-v0.1` frozen.
