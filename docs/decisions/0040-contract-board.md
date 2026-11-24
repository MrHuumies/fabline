# ADR 0040 — Gear-contract board

- **Status:** accepted
- **Date:** 2026-11-24
- **Related:** RFC 0028, RFC 0026, experiment 0074

## Context

0073 showed that a single revealed contract is not a decision. The smallest fix
is a board with an explicit choice, using the existing recipe controller.

## Decision

1. Add three seeded boards with three `(target, deadline, reward)` contracts.
2. Add a choose phase (3 actions) followed by recipe control (2 actions).
3. Append 19 board features to the recipe observation.
4. Add `board_aware`, fixed-contract, highest-reward, random, and oracle
   baselines.
5. Keep the task opt-in and the frozen benchmark unchanged.
6. Test fresh seeds 45,000–45,004.

## Alternatives considered

- **Second deliverable.** Larger; deferred until the board shows a choice
  effect.
- **Deadline-aware recipe only.** Already negative in 0073.
- **Seeded rewards only.** The fixed board variants already change the best
  contract.

## Consequences

- The task tests contract selection plus queue-aware control.
- A fixed contract policy loses on most seeds; board-aware selection wins.
- If board-aware does not beat best fixed by 10, close contracts.

## Follow-ups

- [ ] Formal 0074.
- [ ] If positive, consider a second deliverable or stop P3.
- [ ] Keep `factory-v0.1` frozen.
