# Experiment 0099 — Layout-shift formal block

- **Status:** complete (negative on the preregistered H2; no benchmark freeze)
- **Date:** 2026-11-28
- **Type:** 0.8.0 spatial grammar, formal layout-shift block
- **Task:** `factory.throughput.layout-shift.v1` (candidate; not frozen)
- **Code:** `src/fabline/harness/layout_shift.py`,
  `src/fabline/obs/layout.py`, `src/fabline/tasks/throughput.py`
- **CLI:** `python -m fabline layout-shift --formal`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.6` unchanged; `factory-v0.7` **not** frozen

## Result in one paragraph

**The seeded formal block fails the preregistered OOD gate.** After fixing the
CNN initialization seed, the CNN reaches **0.967** test R² on base layouts and
**0.952 / 0.984 / 0.798** on the large, random, and obstacle shifts — gaps of
**0.015 / −0.017 / 0.169**. The registered H2 requires a ≥0.10 gap on the large
**or random** shift; it fails. Only the obstacle shift has a material gap
(0.169), and the pre-registration treats it as secondary. H1/H3/H4/H5 pass, but
H2 is a validity gate, so `factory-v0.7` is not frozen. The task remains a
diagnostic/challenge candidate.

## Formal results

Seeds: base train 300,000–300,015; val 300,016–300,021; test 300,022–300,027;
shifts 310,000/320,000/330,000 ×10. Target: future score per line. CNN: 50
epochs, hidden 32, 14,401 parameters, 44.1 s training.

| Shift | CNN base R² | CNN shift R² | CNN gap | Linear shift R² |
|---|---:|---:|---:|---:|
| large 32×24 | 0.967 | 0.952 | 0.015 | −0.981 |
| random 24×20 | 0.967 | 0.984 | −0.017 | 0.597 |
| obstacles 24×20 | 0.967 | 0.798 | 0.169 | −18.670 |

Tabular linear base R²: 0.670; MLP base: 0.036. The CNN generalizes on the
large/random shifts; the tabular models collapse on large/obstacle.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 base skill | best test R² ≥ 0.20 | **pass**, 0.967 |
| H2 OOD gap | ≥0.10 on **large or random** | **fail**, 0.015 / −0.017 |
| H3 no leakage | disjoint layout seeds | **pass** |
| H4 metrics complete | CNN + tabular | **pass** |
| H5 model ordering | CNN > best tabular on large and random | **pass** |

The in-code `layout_shift_gates` H2 uses the maximum gap over all shifts, so it
reports true via the obstacle gap (0.169). That is **not** the preregistered H2;
the formal decision follows the pre-registration and fails.

## Why the earlier pilot was optimistic

The 0098 CNN pilot reported base 0.905 and shifts 0.785/0.792/0.857. The CNN
was initialized before the training seed was applied, so those shift numbers
were initialization-sensitive. The formal freeze check exposed the bug; after
seeding the model before construction, the large/random gaps vanish. This is a
reproducibility correction, not a tune.

## Interpretation

- **The large/random shifts are in-distribution-like for a CNN.** The base
  representation is strong enough to generalize; there is no ≥0.10 gap on the
  registered primary shifts.
- **The obstacle shift is the only OOD signal.** It is a useful diagnostic but
  not enough for the registered standard benchmark.
- **Tabular models fail, but the CNN passes.** The model ordering is
  meaningful; the task just does not have a primary OOD gap.
- **No `factory-v0.7` freeze.** The package release 0.8.0 remains pending
  `factory-v0.8` and a spatial decision.
- **Do not tune 0099.** The H2 threshold, seed set, and layout specs are fixed
  by the pre-registration.

## Next

1. **Redesign the spatial shift** with a new pre-registration: a harder large
   layout (more lines/targets or tighter budget), a different target (e.g.,
   bottleneck or route cost), or an explicit obstacle challenge tier.
2. **Or move to `factory-v0.8` stochastic faults/POMDP** and revisit the
   spatial tier later.
3. Keep `factory-v0.6` current; no `factory-v0.7` tag; no 0.8.0 package release
   until the fault tier and a spatial decision.

## Artifacts

- Pre-registration: [`preregistration.md`](preregistration.md)
- Superseded pilot: [`../0098-layout-shift-cnn/summary.md`](../0098-layout-shift-cnn/summary.md)
- RFC 0033 / ADR 0044
- Raw results: `results/layout-shift-formal*/` (ignored)
