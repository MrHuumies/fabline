# Data products

This document defines how FABLINE records, stores, and publishes data. The
guiding rule: **replay is the source of truth; materialized observations are a
cache.**

## Shared episodes and projections

The M3 benchmark uses **shared episodes**: one passive rollout records all views
and targets, and offline tasks are projections over that recording.

```text
shared episode
  seed, scenario, split, sample ticks, state hashes
  views:
    vector           (N, 18)
    grid             (N, H, W, 6)
    entity_features  (N, max_entities, F)
    entity_mask      (N, max_entities)
    adjacency        (N, max_entities, max_entities)
  targets:
    future_score     (N,)
    next_vector      (N, 18)
    bottleneck       (N,) class labels
```

A projection selects a view, a target, a split, and metrics:

- throughput: vector/grid/entities → future_score;
- next-state: vector → next_vector;
- masked-grid: masked grid → masked patch;
- bottleneck: vector → bottleneck class.

The shared writer stores one `data.npz` per episode plus `meta.json` and
`replay.json`. The manifest and dataset card record versions, splits, scenarios,
view shapes, target statistics, and class counts. Projections are computed by
the harness; they are not separate datasets.

## Four data products

## Four data products

1. **Replay** — seed, action log, and version pins. Small, exact, regenerable.
2. **Materialized observations** — arrays for training, derived from replays.
3. **Demonstrations** — scripted, optimal, or human trajectories.
4. **Annotations** — ground-truth latents, causal graphs, event labels, and
   counterfactuals.

Most projects need 1 and 2. Imitation and human-in-the-loop work need 3.
Probing, causal work, and diagnosis need 4.

## Directory layout

Small debug dataset:

```text
datasets/factory-debug-v0.1/
  manifest.json
  dataset_card.md
  stats.json
  episodes/
    ep_000001/
      meta.json
      replay.json
      steps.parquet
      events.jsonl
    ep_000002/
      ...
```

Large dataset:

```text
datasets/factory-train-v0.1/
  manifest.json
  dataset_card.md
  stats.json
  shards/
    split=train/shard-00000.parquet
    split=train/shard-00001.parquet
    split=val/shard-00000.parquet
  views/
    grid/split=train/shard-00000.zarr
    pixels/split=train/shard-00000.zarr
  events/
    split=train/events-00000.jsonl
```

The manifest pins:

- world, observation, action, task, and dataset versions;
- generator config and config hash;
- seeds and split definitions;
- row counts and hashes;
- creation time and git commit.

## Replay format

```json
{
  "episode_id": "ep_000001",
  "seed": 123,
  "world_version": "factory-0.1.0",
  "observation_version": "grid-0.1.0",
  "action_version": "grid-build-0.1.0",
  "task_version": "throughput-predict-0.1.0",
  "config_hash": "sha256:...",
  "actions": [
    {"t": 0, "op": "build", "entity": "miner", "x": 4, "y": 7, "direction": "E"},
    {"t": 10, "op": "noop"}
  ],
  "state_hash_interval": 100,
  "state_hashes": ["...", "..."],
  "metrics": {"gears": 42, "ticks": 2000}
}
```

Replay validation recomputes the hashes and fails at the first divergence.

## Materialized observations

For the M1 debug tier, per-episode NPZ files are acceptable and are what the
current writer produces. For larger releases, use columnar storage:

- Parquet for scalar, vector, and label columns;
- Zarr for dense arrays such as grid or pixels;
- JSONL for events and semantic annotations.

Minimum columns:

```text
episode_id, t, split, task_id
action, reward, label, done
view_mask (struct or separate booleans)
info (struct, optional)
```

High-dimensional views are stored separately and referenced by key. Do not
duplicate the same array in multiple columns.

## Ground truth and annotations

The `info`/annotations stream may include:

- true entity positions, inventories, and craft states;
- production and delivery counters;
- causal bottleneck labels;
- counterfactual outcomes for interventions;
- sensor noise, delay, and failure parameters;
- event references.

Annotations are privileged. They must not leak into agent-visible observations
unless a task explicitly derives a view from them.

## Embedding cache

For expensive encoders, cache embeddings keyed by:

```text
(episode_id, t, view_name, adapter_version, encoder_id, encoder_version)
```

Cache entries are content-addressed or validated by hash. A cache is invalid
when the adapter, encoder, preprocessing, or world version changes. Store the
cache size and creation cost in the manifest.

## Generation

- Headless and seeded.
- Parallel by episode or seed.
- Deterministic; resumable.
- Cost log: ticks/s, wall-clock, memory, output bytes.
- Validate a sample of episodes by replay before publishing.
- Never hand-edit a generated dataset; regenerate it.

## Tiers

| Tier | Size | Purpose | Committed? |
|---|---|---|---|
| Debug | 10–100 episodes | Tests and examples; NPZ per episode | Manifest only |
| Benchmark | Fixed seeds, 1k–10k episodes | Comparable results | Manifest + cards |
| Large train | 10k+ episodes | Training and scaling | Generated on demand |

Do not commit large arrays. Commit manifests, cards, configs, and small samples.

## Dataset card

Every published dataset includes:

- purpose and generation config;
- world, observation, and task versions;
- seeds and split definitions;
- row and episode counts;
- statistics: label distribution, view availability, action mix, outcome
  distribution;
- known biases and confounds;
- leakage audit;
- license and provenance;
- known issues and errata.

See [`templates/dataset-card.md`](templates/dataset-card.md).

## Anti-patterns

- storing every rendered frame at render rate;
- random splits over near-duplicate layouts;
- leaking labels through text or metadata views;
- missing view masks or availability logs;
- unversioned preprocessing;
- caching embeddings without an invalidation key;
- publishing a dataset without a card;
- comparing results across different dataset versions without saying so.
