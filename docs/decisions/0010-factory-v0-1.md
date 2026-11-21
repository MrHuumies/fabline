# ADR 0010 — Freeze factory-v0.1

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0007, ADR 0009

## Context

M3 produced a shared-episode benchmark with scenario splits, confidence
intervals, task cards, a dataset card, and expected results. It is small (46
episodes, 6 test, 6 shift) but it is the first stable reference for comparing
methods and for future milestones.

Without a frozen version, later renderer or mechanic work would silently change
the benchmark and make old results incomparable.

## Decision

Freeze `factory-v0.1`:

- tag the M3 commit `factory-v0.1`;
- pin the world, scenario plan, episode parameters, projections, baselines, and
  report format in `benchmarks/factory-v0.1/`;
- treat `expected/summary.json` as a reference, not a strict tolerance;
- require a new benchmark version for changes to mechanics, splits, labels, or
  baselines;
- keep `results/factory-v0.1` out of git; the config, card, and summary are the
  artifacts.

## Alternatives considered

- **Wait for a larger benchmark.** Rejected: a small frozen reference is more
  useful than an ever-moving one. Scaling is a later decision.
- **Freeze only the code.** Rejected: data, splits, and labels can drift
  independently.
- **No expected summary.** Rejected: a reference run makes reproduction and
  regression checks concrete.

## Consequences

- M4 can add a viewer without changing benchmark behavior.
- Old results remain interpretable against the tag.
- Any benchmark improvement requires `factory-v0.2` or later.
- The expected summary is environment-dependent at the margins; compare
  qualitative ordering and CIs, not exact floats.
