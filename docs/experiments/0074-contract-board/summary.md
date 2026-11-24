# Experiment 0074 — Gear-contract board

- **Status:** complete (positive; all gates pass)
- **Date:** 2026-11-24
- **Type:** P3 contract-selection experiment
- **Mechanic:** three-contract board plus recipe control (RFC 0028, ADR 0040)
- **Task:** `factory.production.contract-board.v1` (debug/P3, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/contract_board.py`,
  `src/fabline/harness/contract_board.py`
- **CLI:** `python -m fabline contract-board`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**An explicit contract choice creates a real decision.** On fresh seeds
45,000–45,004, board-aware scores **112.0** against the best fixed contract
**90.0** (**+22**) and the oracle **122.0** (gap **10**). Fixed contracts score
36/76/90; highest-reward also scores 90; random scores 32. Board-aware succeeds
on every seed. The board fixes the 0073 failure: a single revealed contract was
not a decision, but choosing among three contracts is.

## Results

| policy | mean reward | 95% CI | success | selected |
|---|---:|---:|---:|---|
| contract0 | 36.0 | [12.0, 60.0] | 0.60 | 0,0,0,0,0 |
| contract1 | 76.0 | [38.0, 98.0] | 0.80 | 1,1,1,1,1 |
| contract2 | 90.0 | [30.0, 150.0] | 0.60 | 2,2,2,2,2 |
| highest reward | 90.0 | [30.0, 150.0] | 0.60 | 2,2,2,2,2 |
| **board-aware** | **112.0** | [84.0, 140.0] | **1.00** | 1,2,0,1,2 |
| random | 32.0 | [0.0, 72.0] | 0.40 | varied |
| oracle | 122.0 | [86.0, 150.0] | 1.00 | 1,2,0,2,2 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 choice gain | board-aware ≥ best fixed + 10 | **pass**, +22 |
| H2 oracle gap | board-aware within 10 of oracle | **pass**, 10 |
| H3 success | board-aware success ≥ 0.60 | **pass**, 1.00 |
| H4 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Choice is the decision.** Fixed contract and highest-reward policies lose
  on boards where their contract is infeasible or low-value.
- **The feasibility rule works.** `target × 16 ≤ deadline` selects the best
  feasible contract on 4/5 boards; the oracle takes a higher-reward contract on
  one board.
- **The conservative rule costs exactly the 10-point oracle gap.** Board-aware
  is within the gate but not optimal; do not tune the rate after the formal
  block.
- **The queue controller still carries production.** The contract decision is a
  selection layer; the buffer-aware recipe is unchanged.
- **The contract line now has a positive result.** A second deliverable is not
  needed to justify the board.

## Caveats

- Three fixed boards, not arbitrary contracts.
- One feasibility rate (16 ticks/gear); no learning.
- The contract controller is buffer-aware; no recipe learning.
- One line, no power/faults.
- Not part of frozen `factory-v0.1`.

## Next

1. **Stop the contract line here.** The board is positive; a second deliverable
   is a larger mechanic, not needed for this claim.
2. **P3 review update:** add 0074 to the coverage review; P3 now has recipe,
   byproduct, and contract-board positives.
3. Keep the frozen benchmark unchanged.

## Artifacts

- Mechanic: RFC 0028, ADR 0040
- Env: `src/fabline/env/contract_board.py`
- Harness: `src/fabline/harness/contract_board.py`
- CLI: `python -m fabline contract-board`
- Task card: [`../../tasks/contract-board.md`](../../tasks/contract-board.md)
- Raw results: `results/contract-board/` (ignored)
