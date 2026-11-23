# Experiment 0063 — Three-crew recall and recovery

- **Status:** complete (pilot-confirmed; see the transparency note)
- **Date:** 2026-11-23
- **Type:** P2 third-crew/recovery experiment
- **Mechanic:** 64-action initial dispatch plus 16-action A/C recovery after B
  recall (RFC 0021, ADR 0032)
- **Task:** `factory.power.crew-three-replan.v1` (debug/P2, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/three_crew_replan.py`,
  `src/fabline/harness/crew_three_replan.py`
- **CLI:** `python -m fabline crew-three-replan`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Transparency note

The pilot (seeds 23000–23002) and formal gates were fixed before the formal
block, but this pre-registration file was written after the formal run. It
records the gates honestly rather than claiming an independent timestamped
preregistration.

## Question

Does the third crew help after B is recalled, beyond the initial three-crew
coverage?

## Environment

- 32×16 twin-line, three positive bridges.
- A at depot; B and C on seeded random bases.
- Warning 40; failures 100/130/160; recall 100.
- Initial 64-action A/B/C dispatch; B's unfinished job aborts.
- Recovery 16-action A/C pair; duplicate positive targets masked.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 23000–23002.
- Formal: seeds 24000–24004 (5 contiguous, all valid by reset-only check).
- No Q training.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| three nearest | nearest initial; nearest A/C recovery |
| three greedy | outage per service time; greedy recovery |
| three aware | earliest deadline; aware recovery |
| three no-replan | initial dispatch only |
| oracle | best 64 initial and 16 recovery actions |

## Gates

| Gate | Threshold |
|---|---|
| H1 recovery gain | three best ≥ no-replan + 10 |
| H2 coordination | three best ≥ single/noop + 10 |
| H3 oracle gap | report oracle vs three best; may be shallow |
| H4 oracle success | oracle success ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Predictions

- Three best 500–520; no-replan 300–400; single/noop 100–130.
- Oracle 520; three greedy 500–520.
- Recovery gain 100+; oracle gap 0–30 (possibly shallow).

## Analysis plan

- Report all baselines with score/CI/success.
- Report oracle actions.
- Keep layout, deadlines, recall, and one-pair budget fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0021, ADR 0032
- Env: `src/fabline/env/three_crew_replan.py`
- Harness: `src/fabline/harness/crew_three_replan.py`
- CLI: `python -m fabline crew-three-replan`
- Task card: `docs/tasks/crew-three-replan.md`
- Raw results: `results/crew-three-replan/` (ignored)
- Summary: `docs/experiments/0063-crew-three-replan/summary.md`
- Prior: [`../0062-crew-three/summary.md`](../0062-crew-three/summary.md)
