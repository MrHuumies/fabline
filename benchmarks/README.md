# Benchmarks

Frozen benchmark releases live here as versioned configs and expected results.

```
benchmarks/
  factory-v0.1/
    benchmark.toml        # tasks, splits, seeds, budgets
    tasks/                # task configs
    baselines/            # baseline configs
    expected/             # reference results and tolerances
    card.md               # benchmark card
```

Rules:

- A frozen benchmark is immutable. Changes require a new version.
- Every benchmark pins world, observation, task, dataset, and baseline versions.
- Every task has a card.
- Every result records seeds, compute budget, config hash, and git commit.
- Retired benchmarks stay for provenance.

The first frozen benchmark is [`factory-v0.1`](factory-v0.1/card.md), tagged
`factory-v0.1`. It remains immutable; changes require a new benchmark version.

The 0.3.0 candidate is [`factory-v0.2`](factory-v0.2/spec.md). It is a **draft**:
the task set, splits, baselines, and expected summary are frozen only after the
0.3.0 pilots pass their gates.
