# Experiment 0042 — Two-crew repair coordination

- **Status:** complete (all gates pass)
- **Date:** 2026-11-22
- **Type:** P2 multi-agent assignment experiment
- **Mechanic:** two crews, parallel travel + repair (RFC 0011, ADR 0021)
- **Task:** `factory.power.crew-coordination.v1` (debug/P2, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/multi_crew.py`,
  `src/fabline/harness/multi_crew.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Two crews turn an impossible single-crew deadline into a solved parallel
assignment.** Single-crew EDF scores **60.0** and succeeds on no seed; two-crew
nearest, greedy, and the oracle all score **260.0** with success 1.00, and
tabular Q also reaches **260.0** with success 1.00. The coordination gain is
**+200 points**. All five gates pass. The formal seeds are generous: every
parallel policy finds the pair (small A, large B), so the result is a clean
positive for parallel coordination but not yet a hard assignment benchmark.

## Environment

- Gear line, wired power, one generator, capacity 12.
- Crew A at the depot; crew B at the opposite corner.
- Targets: loop, small bridge, large bridge.
- Warnings at 40; failures at 90 (loop), 110 (small), 130 (large).
- One-shot assignment: one target per crew; same-wire positive pairs masked.
- Travel = 2 × Manhattan; service 40 ticks; jobs run concurrently.
- Reward: production score from the assignment to episode end.
- Success ≥ 150.

## Data and seeds

- Evaluation: seeds 1000, 1001, 1002, 1004, 1005; one episode each.
- Seed 1003 has no zero-impact loop and is skipped; 1005 replaces it.
- Q training: 500 layouts from 30000 + 1000 × Q seed.
- Pilot: seeds 0–9.

## Results

| policy | mean score | 95% CI | prevented | aborted | travel | success |
|---|---:|---:|---:|---:|---:|---:|
| noop | 46.0 | [42.0, 50.0] | 0.00 | 0.00 | 0.0 | 0.00 |
| single_edf | 60.0 | [60.0, 60.0] | 1.00 | 0.00 | 6.8 | 0.00 |
| random | 94.0 | [47.0, 178.0] | 1.20 | 0.40 | 28.4 | 0.20 |
| **parallel_nearest** | **260.0** | [260.0, 260.0] | 2.00 | 0.00 | 32.8 | **1.00** |
| **parallel_greedy** | **260.0** | [260.0, 260.0] | 2.00 | 0.00 | 32.8 | **1.00** |
| **tabular Q** | **260.0** | [260.0, 260.0] | 2.00 | 0.00 | 32.8 | **1.00** |
| **oracle** | **260.0** | [260.0, 260.0] | 2.00 | 0.00 | 34.4 | **1.00** |

Oracle pairs: action 11 (`small` for A, `large` for B) on every formal seed.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 coordination gain | best two-crew scripted ≥ single_edf + 10 | **pass**, +200 |
| H2 oracle gain | oracle ≥ single_edf + 10 | **pass**, +200 |
| H3 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 | **pass**, 100%; 1.00 |
| H4 assignment quality | report duplicates/aborts/pairs | **pass** |
| H5 budget | 500 training episodes | **pass** |

## Interpretation

- **Parallelism is the gain.** One crew cannot cover both bridges before their
  deadlines; two crews can.
- **The formal assignment is easy.** Nearest, greedy, Q, and the oracle all
  choose the same pair and score 260. The pilot had nearest/greedy failures on
  some seeds, but the formal seeds do not.
- **Q learns the pair.** The discretized role/position state is sufficient for
  this seed set.
- **This is a positive P2 slice, but shallow.** It demonstrates coordinated
  parallel work, not communication, partial views, or agent failure.
- **Do not overclaim multi-agent.** The task is centralized two-crew assignment.

## Caveats

- Centralized assignment; no per-crew observations or communication limits.
- One-shot; no repeated dispatch or crew failure.
- Fixed crew bases and targets.
- Formal seeds favor the pair heuristic; a harder seed set would be a new
  experiment.
- Deterministic layouts; one episode per seed.
- Not part of frozen `factory-v0.1`.

## Follow-up — experiment 0044

A 40-seed robustness run (seeds 3000–3039) keeps the coordination gain but shows
that this five-seed block was mildly optimistic: nearest **255.5**, greedy
**245.0**, pooled Q **225.5**, oracle **260.0**, single-crew **60.0**. The oracle
pair is still small for crew A and large for crew B on every seed. See
[`../0044-crew-robustness/summary.md`](../0044-crew-robustness/summary.md).

## Next

1. **Crew failure or unavailable crew** — test replanning; the centralized gain
   is robust.
2. **Larger/random layouts** — make nearest fail more often and give partial
   views a graded structure.
3. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0011, ADR 0021
- Env: `src/fabline/env/multi_crew.py`
- Harness: `src/fabline/harness/multi_crew.py`
- CLI: `python -m fabline multi-crew`
- Raw results: `results/multi_crew/` (ignored)
- Task card: `docs/tasks/multi-crew.md`
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
