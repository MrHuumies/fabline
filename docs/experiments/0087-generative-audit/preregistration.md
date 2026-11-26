# Experiment 0087 — Generative layout/recipe feasibility audit

- **Status:** complete (negative feasibility; see [summary](summary.md))
- **Date:** 2026-11-26
- **Type:** P3 generative pilot
- **Task:** `factory.generative.audit.v1` (feasibility audit, not a benchmark)
- **Code:** `src/fabline/harness/generative_audit.py`
- **CLI:** `python -m fabline generative-audit`
- **Benchmark:** none; `factory-v0.2` unchanged

## Question

Does the current factory content expose enough structural variation for a
meaningful generative layout/recipe pilot, or would a model only resample a
handful of line grammars?

## Hypothesis

The generator's line grammar is deliberately small. A generative model trained
on current layouts may have high validity but almost no structural novelty. The
pilot should measure structural diversity before adding a model or a new
mechanic.

## Audit

- 8 scenarios: ingot, extra_ingot, gear, extra_gear, shift_gear, random_gear,
  spread_gear, random_topology.
- 100 layouts per scenario.
- 48×24 config, starter line, rock density 0.02, two ore patches.
- Extract each production line as an entity-type token sequence.
- Metrics:
  - total lines and unique line sequences;
  - mean pairwise sequence diversity (1 − SequenceMatcher ratio);
  - unique line positions and position diversity;
  - per-scenario counts.

## Pilot

Seeds 0–99, 1,300 lines:

- 7 unique line sequences;
- diversity 0.081;
- 473 unique positions;
- every scenario has 1–3 unique sequences.

This fails the structural gate below. The position variation is real, but the
semantic line grammar is nearly fixed.

## Formal design

- Fresh seeds 1,000–1,099, same scenarios and config.
- Same metrics; no model training.
- Gate: at least **20 unique line sequences** and diversity ≥ **0.25**.
- No post-hoc scenario or metric changes.

## Gates

| Gate | Threshold |
|---|---|
| H1 structural variety | ≥ 20 unique line sequences |
| H2 sequence diversity | mean pairwise diversity ≥ 0.25 |
| H3 position variation | report only |
| H4 frozen benchmark | `factory-v0.2` unchanged |

If H1/H2 fail, a generative layout/recipe benchmark is not justified on the
current content; a richer grammar or recipe space is a new mechanic/RFC, not a
model tweak.

## Predictions

- 5–10 unique sequences; diversity 0.05–0.12.
- H1/H2 fail; H3 reports substantial position variation.
- The pilot is a negative feasibility result, not a model failure.

## Kill criteria

- Fewer than 20 unique sequences: stop the generative pilot.
- Diversity under 0.25: stop the generative pilot.
- Do not add a generative model just to produce copies of seven lines.

## Transparency note

The pilot was a design audit on seeds 0–99. Formal seeds 1,000–1,099 are fresh.
This is a content-feasibility result, not a generative-model benchmark.
