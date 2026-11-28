# Experiment 0099 — Layout-shift formal block

- **Status:** complete (negative on H2; see [summary](summary.md))
- **Date:** 2026-11-28
- **Type:** 0.8.0 spatial grammar, formal layout-shift block
- **Task:** `factory.throughput.layout-shift.v1` (draft; `factory-v0.7` candidate)
- **Code:** `src/fabline/harness/layout_shift.py`,
  `src/fabline/obs/layout.py`, `src/fabline/tasks/throughput.py`
- **CLI:** `python -m fabline layout-shift --formal ...`
- **Benchmark:** none; `factory-v0.6` unchanged; `factory-v0.7` candidate
- **Related:** RFC 0033, ADR 0044, experiments 0097/0098

## Question

Does a padded-grid CNN trained on base layouts generalize to **fresh** larger,
randomized, and obstacle-heavy layouts, and does it beat tabular layout-summary
baselines on the shift splits?

## Hypotheses

1. The CNN has base skill (test R² ≥0.20).
2. The CNN has a material OOD gap (≥0.10) on the large or random shift.
3. The CNN beats the best tabular model on the large and random shifts.
4. No layout seed leaks across train/val/test/shift.

The obstacle shift is reported separately; its gap may be smaller.

## Layout specs

Base: 16×8 gear, 20×12 gear, 24×16 twin. Shift: 32×24 three-line spread, 24×20
randomized twin, 24×20 obstacle-heavy. Target: future score per production
line. Task: 200-tick warmup, 100-tick horizon, 500-tick episode, 10-tick
samples.

## Seeds

- Base train: 300,000–300,015 (16 per spec).
- Base val: 300,016–300,021 (6 per spec).
- Base test: 300,022–300,027 (6 per spec).
- Large shift: 310,000–310,009 (10 layouts).
- Random shift: 320,000–320,009 (10 layouts).
- Obstacles shift: 330,000–330,009 (10 layouts).

All layout seeds are fresh relative to 0097/0098. Splits are by layout seed;
no episode-level leakage.

## Conditions

| View | Models | Input |
|---|---|---|
| layout-summary | mean, persistence, linear, GBDT, MLP | vector + width/height/line count/density |
| padded-grid | CNN | 24×32×14: 6 grid channels + valid mask + 7 layout descriptors |

CNN: 50 epochs, hidden 32, default batch/learning rate. MPNN and Transformer
are **not** in this block; they are a documented follow-up/scope cut.

## Gates

| Gate | Threshold |
|---|---|
| H1 base skill | best model test R² ≥ 0.20 |
| H2 OOD gap | CNN test R² − shift R² ≥ 0.10 on large or random |
| H3 no leakage | all layout seed sets disjoint |
| H4 metrics complete | CNN + tabular metrics present |
| H5 model ordering | CNN shift R² > best tabular shift R² on large and random |

The obstacle shift gap is reported but is not the primary H2 condition.

## Freeze rule

- H1–H5 pass: freeze `factory-v0.7` as a standard spatial benchmark.
- H1/H3/H4 pass but H2 or H5 fails: keep layout-shift as a diagnostic or
  challenge candidate; do not freeze.
- H1 fails: no freeze; the task/representation needs a new pre-registration.
- MPNN/Transformer can be added after the freeze as a baseline expansion; they
  do not change the task contract.

## Analysis

- Report per-spec and pooled test/shift R² and MAE.
- Report the OOD gap per model and shift.
- Report CNN parameters and training seconds.
- Negative and challenge results go first in the summary.
- No post-hoc changes to seeds, specs, target, observation, gates, or CNN
  epochs after the formal run.

## Kill criteria

- No base skill: task is not learnable; no freeze.
- No OOD gap: layout shift is a diagnostic; no freeze.
- CNN loses to tabular on shift: the padded grid is not justified; no freeze.
- MPNN/Transformer absence is a scope cut, not a failure; document it.

## Result

The seeded formal block fails the preregistered H2: CNN base 0.967; large/random
gaps 0.015/−0.017; obstacle gap 0.169. No `factory-v0.7` freeze. See
[summary](summary.md).

## Artifacts

- RFC: [`../../rfcs/0033-0.8.0-spatial-grammar.md`](../../rfcs/0033-0.8.0-spatial-grammar.md)
- ADR: [`../../decisions/0044-0.8.0-scope.md`](../../decisions/0044-0.8.0-scope.md)
- Raw results: `results/layout-shift-formal*/` (ignored)
