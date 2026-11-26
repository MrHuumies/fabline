# Experiment 0087 — Generative layout/recipe feasibility audit

- **Status:** complete (negative feasibility: current content is too constrained)
- **Date:** 2026-11-26
- **Type:** P3 generative pilot
- **Task:** `factory.generative.audit.v1` (feasibility audit, not a benchmark)
- **Code:** `src/fabline/harness/generative_audit.py`
- **CLI:** `python -m fabline generative-audit`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**The current factory content is too structurally constrained for a meaningful
generative layout/recipe pilot.** The formal audit on fresh seeds 1,000–1,099
produced **1,300 lines**, but only **7 unique line sequences** and mean pairwise
diversity **0.080**. The gate required at least 20 unique sequences and
diversity 0.25. Position variation is larger (477 unique placements, position
diversity 0.367), but the semantic line grammar is nearly fixed: most scenarios
have one unique sequence, and the richest has three. A generative model on this
data would mostly resample seven lines. The pilot is stopped; a richer grammar
or recipe space is a new mechanic/RFC, not a model tweak.

## Formal results

Fresh seeds 1,000–1,099; 100 layouts per scenario:

| scenario | lines | unique | diversity | positions |
|---|---:|---:|---:|---:|
| ingot | 100 | 1 | 0.000 | 18 |
| extra_ingot | 100 | 2 | 0.078 | 18 |
| gear | 100 | 1 | 0.000 | 18 |
| extra_gear | 100 | 3 | 0.081 | 18 |
| shift_gear | 100 | 1 | 0.000 | 18 |
| random_gear | 200 | 1 | 0.000 | 179 |
| spread_gear | 300 | 1 | 0.000 | 212 |
| random_topology | 300 | 3 | 0.081 | 248 |
| **total** | **1,300** | **7** | **0.080** | **477** |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 structural variety | ≥ 20 unique sequences | **fail**, 7 |
| H2 sequence diversity | ≥ 0.25 | **fail**, 0.080 |
| H3 position variation | report | 477 positions, 0.367 |
| H4 frozen benchmark | `factory-v0.2` unchanged | **pass** |

## Interpretation

- **The line grammar has seven semantic outcomes.** Extra belts and the
  assembler change the sequence, but there is no broad structural distribution
  to learn.
- **Position variation is not enough.** A model could generate line placements,
  but that is layout jitter, not a generative layout task; validity would be
  trivial.
- **This is a content-feasibility result.** The negative is not about a
  generative model; no model was trained because the data cannot support the
  claimed task.
- **A real generative pilot needs a new mechanic.** A richer grammar, recipe
  space, or multi-line topology would be a new RFC/ADR, not a post-hoc model.

## Caveats

- 48×24 config and eight scenarios; one generator family.
- Line token sequences ignore rocks, ore patches, and power wires; adding them
  would change the task, not rescue the line diversity.
- Position diversity is reported, not gated.
- No generative model was trained, deliberately.

## Next

1. Stop the generative pilot; do not add a model on seven lines.
2. The remaining release-quality work is the public efficiency table and viewer
   QoL.
3. A richer generative grammar/recipe space is a new mechanic/RFC if revisited.
4. Keep `factory-v0.2` and `v0.3.0` unchanged.

## Artifacts

- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/generative_audit.py`
- Raw results: `results/generative-audit/` (ignored)
