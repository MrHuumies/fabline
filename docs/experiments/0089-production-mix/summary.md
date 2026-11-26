# Experiment 0089 — Production-mix pilot

- **Status:** complete (mixed: fixed-item effect, no schedule gap)
- **Date:** 2026-11-26
- **Type:** 0.4.0 Phase 1 mechanic pilot
- **Task:** `factory.production.mix.v1` (draft, not in a frozen benchmark)
- **Code:** `src/fabline/worlds/factory/production.py`,
  `src/fabline/env/production_mix.py`,
  `src/fabline/harness/production_mix.py`
- **CLI:** `python -m fabline production-mix`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**The production mix creates a fixed-item choice but not a scheduling decision.**
The opt-in mechanic runs, and the default state hash is unchanged. On five
seeds, always-component scores **186** versus always-gear **150**, and tabular Q
reaches **189.2** with 23.8 switches; best fixed is 186. H2 passes (+36 over
always-gear), but H3 fails: the best schedule gains only 3.2 over best fixed,
not 10. No policy reaches the 200 success threshold. The mix alone is too easy;
the order stream (or the assembly-edge Phase 1b) is the real decision layer.

## Results

Seeds 70,000–70,004; 5 episodes per seed:

| policy | mean score | gear | component | switches | success |
|---|---:|---:|---:|---:|---:|
| always_gear | 150.0 | 15.0 | 0.0 | 0.0 | 0.00 |
| always_component | **186.0** | 0.0 | 31.0 | 1.0 | 0.00 |
| alternate_10 | 166.0 | 10.0 | 11.0 | 2.0 | 0.00 |
| alternate_20 | 166.0 | 10.0 | 11.0 | 1.0 | 0.00 |
| alternate_40 | 150.0 | 15.0 | 0.0 | 0.0 | 0.00 |
| random | 177.2 | 9.3 | 14.0 | 14.7 | 0.00 |
| tabular Q | **189.2** | 9.8 | 15.2 | 23.8 | 0.00 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 mechanic | config runs; default hash unchanged | **pass** |
| H2 decision | best fixed ≥ always-gear + 10 | **pass**, +36 |
| H3 oracle gap | oracle ≥ best fixed + 10 | **fail**, +3.2 |
| H4 frozen benchmark | `factory-v0.2` unchanged | **pass** |

## Interpretation

- **Component is the better fixed item** at the current cost/score; gear is
  dominated unless demand changes the value.
- **Switching does not add a meaningful schedule gain.** Q learns a small +3.2
  over always-component, below the gate.
- **The mix is a prerequisite, not a standalone task.** Orders, deadlines, and
  values are needed to make switching worth it.
- **No success at 200.** The fixed score threshold was too high for this slice;
  do not tune it post-hoc.

## Caveats

- One 16×8 gear line, one component cost/score, no orders.
- The wrapper action is recipe-only; no build/route decisions.
- The component→gear assembly edge is not implemented.
- Tabular Q is a small state baseline; no deep RL.

## Next

1. Implement the order stream and order-planning/control tasks.
2. Keep the production mix as the mechanic precondition.
3. Consider Phase 1b assembly edge only if orders still do not create a
   scheduling gain.
4. Keep `factory-v0.2` and `v0.3.0` unchanged.

## Artifacts

- Task card: [`../../tasks/production-mix.md`](../../tasks/production-mix.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/production_mix.py`
- Raw results: `results/production-mix/` (ignored)
