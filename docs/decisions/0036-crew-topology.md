# ADR 0036 — Random-topology triage

- **Status:** accepted for pilot/formal test
- **Date:** 2026-11-23
- **Related:** RFC 0025, RFC 0017, ADR 0028, experiment 0067

## Context

The P2 review lists larger/random topology as the remaining structural gap.
The 0059 spread layout was negative: greedy matched oracle. A 5-seed pilot on
seeds 27,000–27,004 suggests a full-width random three-line layout has a more
consistent oracle gap than spread (mean per-seed gap +34 vs +18).

## Decision

1. Add a `random_topology` scenario: 48×24, three lines, random y rows,
   full-width random x starts, one extra belt per line.
2. Add a `crew-topology` CLI with `--layout random|spread` and the 0055 triage
   rules.
3. Keep the scenario and CLI opt-in; default scenarios and tasks are unchanged.
4. Test the random layout against the spread control on fresh seeds
   28,000–28,004.
5. If the random layout does not beat the spread gap by 10 points, retire the
   topology axis and move to P3.

## Alternatives considered

- **Spread bands only.** Already negative in 0059.
- **True random graph topology.** Deferred; a larger mechanic.
- **Change the triage rules.** Rejected; the layout is the only variable.

## Consequences

- The test isolates layout randomness from task rules.
- Absolute scores are lower on the random layout; the gate is the per-seed
  oracle gap, not raw score.
- The pilot has one negative paired seed; the formal block decides.
- No world or frozen benchmark change outside the new opt-in scenario.

## Follow-ups

- [ ] Formal experiment 0067.
- [ ] Update the coverage map and roadmap with the verdict.
- [ ] Keep `factory-v0.1` frozen.
