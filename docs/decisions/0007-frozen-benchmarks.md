# ADR 0007 — Frozen benchmark versions

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0005

## Context

A living world changes under the benchmark. If tasks, splits, seeds, or
mechanics change silently, results from different dates are not comparable and
"method A beats method B" becomes unverifiable.

## Decision

Benchmark releases are **frozen and immutable**:

- a benchmark tag pins world, observation, task, dataset, and baseline versions;
- tasks, splits, seeds, and metrics do not change within a release;
- changes require a new benchmark version;
- retired benchmarks remain for provenance but accept no new results;
- every report records the benchmark tag, config hash, and git commit.

Draft benchmarks may change. Frozen benchmarks may not.

## Alternatives considered

- **Always-latest benchmark.** Rejected: incomparable results and silent drift.
- **Version only the code.** Rejected: data, splits, and tasks can drift
  independently.
- **Freeze everything forever.** Rejected: the world must be able to improve;
  new versions are how it does so.

## Consequences

- Benchmark maintenance has a cost; that is the point.
- Old results remain interpretable.
- New mechanics or tasks require a new benchmark version.
- Public releases, if any, can point to stable tags.
