# Experiment 0067 — Random-topology triage

- **Status:** complete (negative; H1 and H3 fail; topology axis retired)
- **Date:** 2026-11-24
- **Type:** P2 random-topology experiment
- **Mechanic:** full-width random three-line layout for the three-bridge survivor
  triage (RFC 0025, ADR 0036)
- **Task:** `factory.power.crew-topology.v1` (debug/P2, not in `factory-v0.1`)
- **Code:** `src/fabline/worlds/factory/generator.py`,
  `src/fabline/harness/crew_multi_orphan.py`
- **CLI:** `python -m fabline crew-topology --layout random|spread`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The random topology did not widen the triage gap.** On fresh seeds
28000–28004, the random layout has oracle 464.0 and per-seed best scripted
460.0, giving a mean per-seed gap of **+4.0** (`20, 0, 0, 0, 0`). The spread
control has oracle 536.0 and per-seed best scripted 518.0, a gap of **+18.0**
(`10, 50, 0, 0, 30`). H1 fails (random gap below +10) and H3 fails (random is
not +10 over spread). Random topology is harder in absolute score, but greedy,
aware, and nearest are at or near the oracle on most seeds. It does not create a
new assignment decision.

## Pilot vs formal

Pilot seeds 27000–27004:

| Layout | Mean per-seed gap |
|---|---:|
| spread | +18.0 |
| random | +34.0 |
| paired difference | +16.0 |

Formal seeds 28000–28004:

| Layout | Mean per-seed gap |
|---|---:|
| spread | +18.0 |
| random | +4.0 |
| paired difference | −14.0 |

The pilot's +34 did not replicate. This is another pilot/formal regression, not
a confirmation.

## Random-topology results

| policy | mean score | 95% CI | success |
|---|---:|---:|---:|
| noop | 108.0 | [98.0, 120.0] | 0.00 |
| single_edf | 114.0 | [102.0, 126.0] | 0.00 |
| nearest | 436.0 | [390.0, 485.1] | 1.00 |
| greedy | 414.0 | [361.9, 477.0] | 1.00 |
| aware | 432.0 | [384.0, 488.0] | 1.00 |
| no-replan | 116.0 | [102.0, 128.0] | 0.00 |
| **oracle** | **464.0** | [432.0, 498.0] | **1.00** |

Per-seed best scripted: `400, 480, 530, 450, 440`; oracle:
`420, 480, 530, 450, 440`; gaps: `20, 0, 0, 0, 0`.

## Spread control

| policy | mean score | success |
|---|---:|---:|
| nearest | 500.0 | 1.00 |
| greedy | 488.0 | 1.00 |
| aware | 502.0 | 1.00 |
| **oracle** | **536.0** | **1.00** |

Per-seed best scripted: `450, 440, 550, 560, 590`; oracle:
`460, 490, 550, 560, 620`; gaps: `10, 50, 0, 0, 30`.

## Oracle sequences

Random:

| seed | initial | replan 1 | replan 2 |
|---:|---:|---:|---:|
| 28000 | 0 | 12 | 8 |
| 28001 | 8 | 12 | 4 |
| 28002 | 0 | 12 | 4 |
| 28003 | 2 | 12 | 4 |
| 28004 | 4 | 12 | 8 |

Spread:

| seed | initial | replan 1 | replan 2 |
|---:|---:|---:|---:|
| 28000 | 0 | 12 | 8 |
| 28001 | 0 | 12 | 8 |
| 28002 | 2 | 12 | 4 |
| 28003 | 12 | 4 | 8 |
| 28004 | 14 | 4 | 0 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 random gap | ≥ +10 | **fail**, +4 |
| H2 coordination | best scripted ≥ single/noop + 10 | **pass**, +346 |
| H3 layout effect | random ≥ spread + 10 | **fail**, −14 paired |
| H4 oracle success | ≥ 0.60 | **pass**, 1.00 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Random topology is harder, not deeper.** The random layout lowers absolute
  scores but also compresses the gap: nearest/greedy/aware are at or near the
  oracle on four of five seeds.
- **The spread control remains the better assignment test.** It has a +18 gap
  driven by two seeds; random has +4.
- **The pilot was optimistic.** The pilot's +34 came from seeds where nearest
  failed; fresh seeds do not reproduce it.
- **No new coordination decision.** Random layout changes the numbers, not the
  policy ranking. The topology axis is retired.
- **P2 multi-agent is near its practical ceiling.** Third crew, recall, cost,
  and topology have all been tested; none adds a robust new decision beyond the
  existing triage/assignment gaps.

## Caveats

- Five formal seeds; CIs are wide.
- One random-topology family and one map size.
- The random layout changes both line placement and line length (extra belt);
  the pilot does not separate those.
- Not part of frozen `factory-v0.1`.

## Next

1. **Close P2 multi-agent.** Do not add another topology or cost variant without
   a new named decision.
2. **Move to P3.** The remaining roadmap candidates are planning/world models,
   deep RL, offline RL, or a retention benchmark.
3. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0025, ADR 0036
- Layout: `src/fabline/worlds/factory/generator.py`
- Harness: `src/fabline/harness/crew_multi_orphan.py`
- CLI: `python -m fabline crew-topology --layout random|spread`
- Raw results: `results/crew-topology/` (ignored)
- Task card: [`../../tasks/crew-topology.md`](../../tasks/crew-topology.md)
- Prior: [`../0055-crew-triage/summary.md`](../0055-crew-triage/summary.md)
