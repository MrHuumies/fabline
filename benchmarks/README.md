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
