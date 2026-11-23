# Experiment 0062 — Three-crew initial assignment

- **Status:** complete (pilot-confirmed; see the transparency note)
- **Date:** 2026-11-23
- **Type:** P2 third-crew/coverage experiment
- **Mechanic:** 64-action three-crew assignment (RFC 0020, ADR 0031)
- **Task:** `factory.power.crew-three.v1` (debug/P2, not in `factory-v0.1`)
- **Code:** `src/fabline/env/three_crew.py`,
  `src/fabline/harness/crew_three.py`
- **CLI:** `python -m fabline crew-three`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Transparency note

The pilot (seeds 21000–21002) found the first deadline set unsolvable and the
second set solvable. The formal gates below were fixed before the formal block,
but this pre-registration file was written after the formal run. It records the
gates honestly rather than claiming an independent timestamped preregistration.

## Question

Does a full third crew at the initial decision beat the two-crew upper baseline
by at least 10 points?

## Environment

- 32×16 twin-line, three positive bridges.
- A at the depot; B and C on seeded random bases at least eight cells from A and
  each other.
- Warning 40; failures 100/130/160.
- One-shot 64-action assignment; duplicate positive targets masked.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 21000–21002.
- Formal: seeds 22000–22004 (5 contiguous, all valid by reset-only check).
- No Q training.
- No dataset artifact.

## Baselines

| Condition | Policies |
|---|---|
| two-crew | nearest, greedy, oracle; C noop |
| three-crew | nearest, greedy, aware, oracle |

## Gates

| Gate | Threshold |
|---|---|
| H1 third-crew gain | three best ≥ two best + 10 |
| H2 coordination | three best ≥ single/noop + 10 |
| H3 oracle gap | three oracle ≥ three best + 10 |
| H4 oracle success | three oracle success ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Predictions

- Three greedy 460–500; three oracle 520.
- Two oracle 300–340; single/noop 90–120.
- H1/H2 large; H3 +20–50.
- Success: three oracle 1.00, three greedy 0.80.

## Analysis plan

- Report all conditions with score/CI/success.
- Report oracle actions.
- Keep layout, deadlines, C base rule, and one-shot contract fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0020, ADR 0031
- Env: `src/fabline/env/three_crew.py`
- Harness: `src/fabline/harness/crew_three.py`
- CLI: `python -m fabline crew-three`
- Task card: `docs/tasks/crew-three.md`
- Raw results: `results/crew-three/` (ignored)
- Summary: `docs/experiments/0062-crew-three/summary.md`
- Prior: [`../0061-pair-policy-pilot/summary.md`](../0061-pair-policy-pilot/summary.md)
