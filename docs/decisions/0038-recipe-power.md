# ADR 0038 — Recipe choice under power constraints

- **Status:** accepted
- **Date:** 2026-11-24
- **Related:** ADR 0037, RFC 0026, experiment 0071

## Context

0070 established queue-aware recipe choice. The natural robustness question is
whether a tight power budget changes the best policy. The recipe env already
accepts `PowerConfig`; the observation can append the 12-feature power view.

## Decision

1. Add an optional `power` field to `RecipeEnvConfig`; default disabled.
2. Pass power to `FactoryWorld` and append `PowerObservation` when enabled.
3. Add `power_aware` and `power_saver` scripted policies.
4. Use capacity 10 for the power pilot: enough for the line, tight enough that
   slow recipe and random policies lose production.
5. Keep the task opt-in; the frozen benchmark is unchanged.
6. Test a formal 0071 on fresh seeds 39,000–39,004.

## Alternatives considered

- **Capacity 8.** Too tight; all policies score 146.7 and the recipe choice
  disappears.
- **Capacity 12+.** Power is not binding; identical to 0070.
- **Faults instead of power.** Larger interaction; deferred.

## Consequences

- The power condition tests robustness of the queue policy.
- A power-aware policy that gates on headroom is worse; a brownout-aware policy
  ties buffer-aware.
- If power-saver does not beat buffer-aware by 10, power adds no new decision.

## Follow-ups

- [ ] Formal 0071.
- [ ] If negative, keep power as a robustness condition and move to byproducts
  or faults.
- [ ] Keep `factory-v0.1` frozen.
