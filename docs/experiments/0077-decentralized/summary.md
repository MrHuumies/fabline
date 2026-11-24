# Experiment 0077 — Decentralized private-view triage

- **Status:** complete (local/global positive; Q mean positive; success gate fails)
- **Date:** 2026-11-24
- **Type:** P3 decentralized multi-agent experiment
- **Task:** `factory.multiagent.decentralized.v1` (debug/P3, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/crew_decentralized.py`,
  `src/fabline/harness/crew_decentralized.py`
- **CLI:** `python -m fabline crew-decentralized`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Private views create a large local/global gap, and independent Q learns a
better local policy — but not a reliable one.** On fresh seeds 54,000–54,004,
the global oracle scores **748** with success 1.00; local greedy is **460**
(0.40), local nearest **260** (0.20), local aware **260** (0.20). Independent
per-crew Q scores **582** (0.47), **+122 over local greedy**, but below the 0.60
success gate. H1 and H3 pass; H2 fails. The learned per-agent policy is a real
improvement over scripted local rules, but seed-sensitive.

## Results

| policy | mean score | success |
|---|---:|---:|
| local nearest | 260 | 0.20 |
| local aware | 260 | 0.20 |
| local greedy | 460 | 0.40 |
| **private Q** | **582** | **0.47** |
| **global oracle** | **748** | **1.00** |

Per-seed global oracle: `780, 760, 740, 740, 720`.
Private Q pooled over 3 Q seeds × 5 evaluation seeds: `780, 600, 180, 570,
570, 780, 600, 600, 570, 570, 570, 600, 600, 570, 570`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 local cost | global oracle ≥ best local scripted + 10 | **pass**, +288 |
| H2 local success | best local scripted success ≥ 0.60 | **fail**, 0.40 |
| H3 learned policy | private Q ≥ best local scripted + 10 | **pass**, +122 |
| H4 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Visibility is binding.** The local/global gap is +288, much larger than the
  +140 smoke and the +98 from the 0052 shared-report task. The private view is a
  real information limit.
- **Q beats local scripted mean.** Independent Q learns a per-crew policy worth
  +122 over local greedy, closing 42% of the local/global gap.
- **Reliability is the failure.** Q succeeds on 0.47 of episodes, and local
  scripted succeeds on at most 0.40. The task is hard for local policies; the
  oracle is reliable.
- **The learned policy is seed-sensitive.** Q scores range from 180 to 780
  across Q/eval seed pairs. State aliasing and independent credit assignment are
  the likely causes.
- **The task is a benchmark candidate with a caveat.** The local/global and Q
  gains are real, but the 0.60 local-success gate is not met.

## Caveats

- Five evaluation seeds, three Q seeds; pooled Q CIs are wide.
- Radius 16 and one spread layout.
- Independent Q shares reward but not state; no centralized training.
- Private view is Manhattan radius, not occlusion.
- Not part of frozen `factory-v0.1`.

## Next

1. Improve independent Q with a compact relative-geometry state or centralized
   training/decentralized execution; target success ≥0.60.
2. Add a communication-budget condition (shared top-2 reports) and compare with
   the private Q.
3. **Deferred from `factory-v0.2`**: the local-success gate is still open; the
   task remains a debug task, not a frozen benchmark task. See the
   [freeze review](../../../benchmarks/factory-v0.2/freeze-review.md).

## Artifacts

- Task card: [`../../tasks/crew-decentralized.md`](../../tasks/crew-decentralized.md)
- Env: `src/fabline/env/crew_decentralized.py`
- Harness: `src/fabline/harness/crew_decentralized.py`
- Raw results: `results/crew-decentralized/` (ignored)
