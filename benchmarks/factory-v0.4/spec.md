# Benchmark specification — factory-v0.4 (draft)

- **Status:** draft; not frozen
- **Version:** 0.4.0-draft
- **Date:** 2026-11-26
- **World:** `factory-0.1.0`
- **Plan:** `coverage-v0.4`
- **Predecessor:** `factory-v0.3` remains immutable
- **Related:** RFC 0030, ADR 0042, 0.5.0 roadmap, coverage analysis

## Purpose

`factory-v0.4` is the first release of the coverage-first sequence. It does not
add a new game mechanic. It publishes positive backlog tasks, adds public
structured baselines, and separates headline, coverage, and challenge results.

The goal is to make the benchmark honest about what is covered:

- `core`: the frozen v0.3 12-task headline, kept by reference;
- `coverage`: positive backlog tasks that fill missing families;
- `challenge`: valid tasks with negative learned baselines.

## Coverage tier

| Task | Task ID | Family | Why it is here | Status |
|---|---|---|---|---|
| reliability-contract | `factory.power.contract.v1` | risk/uncertainty | mean/CVaR selection | pass |
| partial-throughput | `factory.throughput.partial.v1` | partial observability | masked frame vs history window | pass |
| wired-cascade | `factory.power.cascade.v1` | relational/graph | graph cut under a wire fault | diagnostic |
| crew-schedule | `factory.power.crew-schedule.v1` | spatial scheduling | travel/deadline/budget | pass |
| crew-triage | `factory.power.crew-triage.v1` | multi-agent | centralized coordination | pass |
| preventive-wire | `factory.power.wire-maintenance.v1` | temporal credit | warning-to-action timing | proposed |
| recipe-choice | `factory.production.recipe-choice.v1` | production control | queue-aware recipe choice | proposed |
| maintenance-threshold | `factory.fault.preventive-threshold.v1` | bandit/context | threshold selection | proposed |

The integrated runner covers the first five rows. The other rows are
implementation work for the same tier, not a new benchmark version.

## Challenge tier

| Task | Task ID | Why it is a challenge |
|---|---|---|
| twin-line assignment | `factory.power.crew-layouts.v1` | oracle 441, greedy 419, Q 217/0.00 |
| decentralized triage | `factory.multiagent.decentralized.v1` | local/global gap +288; Q success 0.47 |
| replacement handoff | `factory.power.crew-replacement.v1` | oracle +20; best scripted −38 |
| recall + twin-line | `factory.power.crew-replan-layouts.v1` | recovery +240; oracle-greedy +9 |
| maintenance calibration | `factory.fault.maintenance_calibration.v1` | diagnostics ECE 0.0054; full view 0.0929 |

A challenge task needs a card, split, expected summary, and reproducible runner.
It does not need a winning learned baseline.

## Data and splits

### Reliability contract

- 2,000 train and 2,000 test episodes.
- Even train blocks 600–998; odd test blocks 601–999.
- 10 episodes per block; seeds `block * 10 + episode`.
- Fixed scripted alternator operating policy.
- Payoff: score + (target − 100) on a hit; score − 40 on a miss.
- CVaR alpha 0.2; 2,000-sample block bootstrap.

### Partial throughput

- 100 episodes, 1,100 samples in the public draft.
- 150-tick warmup, 300-tick episode, 10-tick sampling, 50-tick horizon.
- 60% feature dropout; 4-frame masked window.
- Splits by episode: 770 / 209 / 121.

### Wired cascade

- 199 valid layouts from seeds 500–699; 1,990 samples.
- 32×16 gear line, one generator, wired topology, redundancy 2.
- Up to 10 faults per layout, stratified loop/bridge.
- Split by layout: 1,400 / 390 / 200.
- Label: number of consumers disconnected by the marked fault.

### Crew schedule

- 16×8 gear line, one crew, seeds 800–804, 5 episodes each.
- Warning 40; failures 90/120/150; budget 2; travel 2 × Manhattan + 40 service.
- Baselines: noop, impact, nearest, EDF, travel-aware, random, tabular Q,
  deadline Q, oracle.
- Suite Q training: 100 episodes per seed.

### Crew triage

- 32×16 twin-line, three positive bridges, seeds 12000–12004, one episode each.
- Failure/recall 100; two survivor jobs; initial 16 pair actions.
- Baselines: noop, single EDF, nearest, greedy, aware, no-replan, oracle.
- Oracle: exhaustive 16×4×4 sequence per seed.

## Baselines

- Tabular: mean, persistence, linear, GBDT, MLP.
- Structured: `graph_mp`, CNN, MPNN, GRU, Transformer (public `harness/models`).
- Risk: fixed targets, mean-optimal, CVaR-optimal.
- Cost: parameters, training seconds, inference cost where available.

## Gates

- Reliability contract: H1 tradeoff, H2 mean cost, H3 tail gain ≥ +10,
  H4 direction, H5 no free lunch.
- Partial throughput: H1 mask loss, H2 window recovery ≥ +0.10,
  H3 no leakage.
- Wired cascade: H1 graph gain ≥ +0.05; H2 report graph_mp vs GNN; H3 oracle;
  H4 seed consistency; H5 budget.
- Crew schedule: travel gain ≥ +5; oracle ≥ impact +10; deadline Q ≥ 0.85 ×
  best scripted and success ≥ 0.80.
- Crew triage: oracle ≥ best scripted +10; coordination gain ≥ +10; nearest
  below oracle; oracle success ≥ 0.60.
- A failed gate does not lower the threshold; the task is demoted to
  diagnostic/challenge or redesigned.

## Runner

```bash
python -m fabline coverage-suite --out results/factory-v0.4-coverage
python -m fabline coverage-suite --out results/factory-v0.4-coverage-fast --fast
python -m fabline coverage-suite --out results/factory-v0.4-coverage \
  --skip-wired --include-mpnn
```

The runner writes one aggregate JSON/Markdown report and per-task reports. It
is not a frozen benchmark; there is no expected summary yet.

## Freeze criteria

1. The coverage tier has at least six tasks with cards, splits, and baselines.
2. Public CNN, GNN, sequence, and OR baselines run in CI.
3. Episode-level cluster bootstrap and a private holdout are in place.
4. A layout split exists for the spatial tasks.
5. The challenge tier has cards and expected summaries.
6. `factory-v0.3` assets and expected summaries are unchanged.
7. The public/private evidence audit passes.
8. A freeze review and expected summary are checked in.

## Not in this draft

- a new world mechanic;
- a public leaderboard;
- text/pixels adapters;
- deep/offline RL expansion beyond existing public tracks;
- edits to v0.1/v0.2/v0.3 assets.

## Changelog

- 2026-11-26 — draft spec created for the three-task coverage slice.
