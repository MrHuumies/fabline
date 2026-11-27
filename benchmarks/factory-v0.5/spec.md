# Benchmark specification — factory-v0.5

- **Status:** frozen
- **Version:** 0.5.0
- **Date:** 2026-11-27
- **World:** `factory-0.1.0` + opt-in production tree
- **Plan:** `assembly-v0.5`
- **Predecessor:** `factory-v0.4` remains immutable
- **Expected summary:** [`expected/summary.json`](expected/summary.json)
- **Freeze review:** [`freeze-review.md`](freeze-review.md)
- **Related:** RFC 0031, 0.6.0 roadmap, assembly task cards

## Purpose

`factory-v0.5` publishes the assembly edge. It does not add a new world. It
keeps the frozen v0.4 coverage suite by reference and adds an **assembly tier**
with four task families:

- online recipe control;
- finite-horizon recipe planning;
- BOM output forecasting;
- counterfactual recipe-switch estimation.

The release separates the production mechanic from the frozen v0.3/v0.4
surfaces. All assembly tasks require the opt-in production tree; v0.1–v0.4
hash tests must remain unchanged.

## Assembly tier

| Task | Task ID | Family | Observation | Gate |
|---|---|---|---|---|
| assembly-control | `factory.assembly.control.v1` | control | 12-feature cell state | Q beats random; success |
| assembly-planning | `factory.assembly.plan.v1` | planning | initial state | CEM beats random; near oracle |
| assembly-bom | `factory.assembly.bom.v1` | regression | 12-feature cell state | nonlinear skill; not saturated |
| assembly-intervention | `factory.assembly.recipe_intervention.v1` | causal | 12-feature cell state | effect skill; decision gain |

The challenge list is empty for this release. The negative and weak results are
reported in the task cards and freeze review rather than promoted silently.

## Production mechanics

- Component recipe: 1 ingot / 24 ticks → 1 component.
- Assembly recipe: 1 ingot + 1 component / 16 ticks → 2 gears.
- Direct-gear recipe: 1 ingot / 16 ticks → 1 gear.
- Fixed two-feed cell: component assembler at x=5, assembly assembler at x=7.
- Decision interval 10 ticks; episode 500 ticks unless stated otherwise.

## Data and splits

### Assembly control

- 16×8 line, one component assembler, one assembly assembler.
- Decision interval 10 ticks; 500-tick episodes.
- Formal seeds 0–4; 5 episodes each.
- Baselines: always gear, always assembly, buffer-aware, batch-aware, random,
  tabular Q.
- Q training: 500 episodes at seed block 10,000, disjoint from evaluation.
- Gates: scripted +10 over always gear; Q +10 over random; Q success ≥ 0.60.

### Assembly planning

- Five binary recipe blocks of 100 ticks; 500 ticks total.
- Open-loop plan execution; no replanning.
- Formal seeds 0–4.
- Baselines: always gear, always assembly, alternate, batch-3, frontload,
  random plans, CEM with the true simulator, exhaustive 32-plan oracle.
- Gates: oracle ≥ best scripted + 10; CEM ≥ random + 10; CEM ≥ oracle − 10;
  CEM success ≥ 0.60.

### Assembly BOM forecast

- 50 episodes, seeds 0–49; 500-tick episodes.
- Epsilon-random batch policy logging (`random_action_prob` 0.30).
- Warmup 5 decision steps; horizon 5 steps; target is the future gear delta.
- Episode split 60/20/20; 1,200 / 400 / 400 samples.
- Baselines: mean, linear, GBDT, MLP; bootstrap CIs.
- Gates: GBDT R² ≥ 0.30; GBDT ≥ linear + 0.05; GBDT < 0.98;
  MLP R² ≥ 0.20.

### Assembly intervention

- 200 episodes, seeds 58,000–58,199; 500-tick episodes.
- Sample decision steps 10, 20, 30, 40.
- Behaviour policy: epsilon-random batch policy (`random_action_prob` 0.30).
- Treatment: force the opposite assembly recipe and hold it to the end.
- Control: continue the behaviour policy from the same state.
- Effect: treatment terminal score − factual terminal score.
- Episode split from `assign_split`: 560 / 160 / 80 samples.
- Baselines: mean, linear, GBDT, MLP; bootstrap CIs.
- Decision metric: model switches when the predicted effect is positive. The
  decision CI uses an episode-cluster bootstrap.
- Gates: GBDT R² ≥ 0.30; GBDT ≥ linear + 0.05; GBDT < 0.98;
  model gain ≥ half of oracle gain and ≥ 0.5; MLP R² ≥ 0.20.

## Expected summary

The expected summary is compact and deterministic. It contains:

- headline task list;
- control and planning mean scores, 95% CIs, success rates;
- BOM and intervention test R²/MAE;
- intervention decision values and gains;
- gates for every task;
- tolerance: `rtol = 0.03`, `atol = 0.02`.

Check it with:

```bash
python -m fabline assembly-suite \
  --out results/factory-v0.5 \
  --check-expected benchmarks/factory-v0.5/expected/summary.json
```

## Freeze criteria

1. Four assembly tasks have cards, splits, and public harnesses.
2. The expected summary is deterministic and the full check reports zero
   mismatches.
3. `factory-v0.1` through `factory-v0.4` assets and expected summaries are
   unchanged.
4. A freeze review and expected summary are checked in.
5. The limitations below are documented in the card and freeze review.
6. CI runs the full expected-summary check.

## Known limitations

These are follow-ups, not hidden requirements for the 0.6.0 assembly freeze:

- demand uncertainty is deferred;
- no layout split or private holdout;
- planning is a five-bit open-loop task with true-simulator CEM;
- BOM and intervention use tabular baselines only;
- intervention labels are simulator potential outcomes, not logged-data-only
  causal identification;
- the fast path is a smoke check, not a benchmark result.

They are tracked for the next benchmark version.

## Changelog

- 2026-11-27 — spec created for the `factory-v0.5` freeze.
