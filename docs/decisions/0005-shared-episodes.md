# ADR 0005 — Shared episodes, task projections, replay first

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0003, ADR 0007

## Context

Different tasks need different observations, labels, and splits. Generating a
new world per task is wasteful and makes comparisons invalid. Storing every
rendered frame is also wasteful and version-fragile.

## Decision

- Generate an **episode once** and store its replay: seed, action log, config,
  and version pins.
- Define tasks as **projections** over episodes: observation adapters, labels or
  rewards, termination, splits, and metrics.
- Materialize observations and labels on demand into Parquet/Zarr caches.
- Treat the replay as the source of truth; materialized data is a cache.
- Record ground truth in a separate annotation stream.

## Alternatives considered

- **One dataset per task.** Rejected: duplication and drift.
- **Store full state and frames for every step.** Rejected: size and version
  fragility.
- **Generate data inside the training loop.** Rejected for benchmark tasks:
  harder to reproduce and audit. On-demand generation remains an option for
  large training runs.

## Consequences

- The data layer needs manifests, version pins, and projection tooling.
- The same episode can feed supervised, self-supervised, and control tasks.
- Replays are small and exact; caches are rebuildable.
- Splits must be defined over episode IDs and validated for disjointness.
