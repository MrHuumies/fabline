# ADR 0030 — Replacement crew handoff

- **Status:** mixed; not promoted as a benchmark (0060 H2 fails)
- **Date:** 2026-11-23
- **Related:** RFC 0019, RFC 0017, ADR 0028, experiment 0060

## Context

The two-crew triage task has sequential survivor work, and the P2 review
recommends a third crew/replacement. A full three-crew action space is large;
reusing the recalled crew's slot tests handoff with the existing 16-action pair
contract.

## Decision

1. Add `replacement: bool` to `CrewReplanConfig`.
2. At recall, B's unfinished job aborts and replacement crew C arrives at B's
   original base.
3. Post-failure, the pair action is A/C, with duplicate positive targets
   masked.
4. One replacement pair; no sequential jobs.
5. Define `factory.power.crew-replacement.v1` on the three-bridge triage task.
6. Compare no-replacement sequential triage, replacement nearest/greedy/aware,
   and oracles.

## Alternatives considered

- **Full three-crew initial action space.** Deferred; too large for this slice.
- **Random replacement delay.** Deferred; immediate handoff first.
- **Two-crew sequential only.** Already 0055.

## Consequences

- The second crew slot is B before recall and C after, so the observation and
  action vector are reused.
- The task tests handoff and parallel recovery, not three-agent initial
  coordination.
- Defaults and the frozen benchmark are unchanged.
- If replacement does not beat no-replacement by 10, retire the slice.

## Follow-ups

- [ ] Formal experiment 0060.
- [ ] Keep `factory-v0.1` frozen.
