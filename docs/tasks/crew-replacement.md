# Task card — replacement crew handoff

- **Task ID:** `factory.power.crew-replacement.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run complete; H2 fails; not promoted; not
  in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power and twin-line layout
- **Owner:** FABLINE
- **Date:** 2026-11-23

## Phenomenon

Three positive bridges, two crews at the start. Both active jobs fail or abort
at tick 100, and crew B is recalled. Replacement crew C arrives at B's base and
takes the second slot. A and C then choose a recovery pair. The task tests
handoff and parallel recovery against the no-replacement sequential triage.

## Contract

- **Observation:** three-role crew observation; second-crew position is B before
  recall and C after.
- **Actions:** initial 16 pair actions (A/B); post-failure 16 pair actions
  (A/C), with duplicate positive targets masked.
- **Failure/recall:** 100; B's unfinished job aborts.
- **Replacement:** C at B's original base, immediately available at 100.
- **Recovery:** one A/C pair; no sequential jobs.
- **Reward:** final production score; success ≥ 300.

## Metrics

- mean score and success;
- replacement handoff gain vs no-replacement;
- oracle gap;
- recovery pair choices.

## Baselines

| Baseline | Rule |
|---|---|
| no-replacement triage | A-only sequential recovery |
| replacement nearest | nearest pair for A/C |
| replacement greedy | outage per service time for A/C |
| replacement aware | earliest deadlines for A/C |
| noop / single | context |
| oracle | best initial pair and replacement pair |

## Gates

| Gate | Threshold |
|---|---|
| H1 replacement oracle | replacement oracle ≥ no-replacement oracle + 10 |
| H2 handoff gain | replacement best scripted ≥ no-replacement best + 10 |
| H3 coordination | replacement best ≥ no-replacement single/noop + 10 |
| H4 oracle gap | report oracle vs best scripted; may be shallow |
| H5 frozen benchmark | unchanged |

## Results (0060)

Seeds 20000–20004; failure/recall 100; replacement pair.

| condition | best scripted | oracle | success |
|---|---:|---:|---:|
| no-replacement | 424 | 456 | 1.00 |
| replacement | 386 | **476** | 0.80/1.00 |

Replacement oracle +20 over no-replacement, but best scripted −38. H1/H3/H4/H5
pass; H2 fails. The handoff opportunity exists, but scripted pair policies do
not capture it. See
[`experiments/0060-crew-replacement`](../experiments/0060-crew-replacement/summary.md).

## Known pitfalls

- C reuses B's base; a new base or delay is future work.
- One replacement pair; no third-agent initial coordination.
- Greedy may match oracle; the handoff gain is the headline.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-23 — card created; replacement handoff contract and gates defined.
- 2026-11-23 — formal run: oracle +20, best scripted −38; H2 fails; not
  promoted.
