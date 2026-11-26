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

The 0.3.0 benchmark is [`factory-v0.2`](factory-v0.2/spec.md), frozen on
2026-11-24. It has 10 headline tasks on 159 core episodes plus planning,
fault-calibration, and causal-removal blocks. Its expected summary is in
`factory-v0.2/expected/summary.json`; the [freeze review](factory-v0.2/freeze-review.md)
records the scope cuts (no layout split; decentralized/generative deferred;
fault/power/next-state are diagnostics).

The 0.4.0 benchmark is [`factory-v0.3`](factory-v0.3/spec.md), frozen on
2026-11-26. It has 12 headline tasks: the v0.2 core plus order control and
order planning. The [freeze review](factory-v0.3/freeze-review.md) records the
scope cuts.
