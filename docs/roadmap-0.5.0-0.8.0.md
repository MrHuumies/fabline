# FABLINE roadmap — 0.5.0 to 0.8.0

- **Status:** proposed; requires owner approval
- **Date:** 2026-11-26
- **Theme:** coverage first, then structural mechanics
- **Inputs:** [`coverage-analysis-2026-11-26.md`](coverage-analysis-2026-11-26.md),
  [`coverage-map.md`](coverage-map.md),
  [`coverage-review-0.4.0.md`](coverage-review-0.4.0.md),
  [`benchmarks/factory-v0.3/card.md`](../benchmarks/factory-v0.3/card.md),
  [`project_intent.md`](../project_intent.md),
  [`docs/testbed.md`](testbed.md)
- **Related:** RFC 0030, ADR 0042, P2/P3 coverage reviews
- **Branch:** `plan/0.5.0-0.8.0-roadmap`

This document is a plan, not an approved scope. It turns the gap analysis into
four release-sized increments. It does not change any frozen benchmark or world
hash. The owner decides which rows are committed.

## 1. Why this sequence

The analysis reached five conclusions that determine the order:

1. **The published benchmark is narrower than the research surface.** v0.3 has
   12 tasks; the world has a large positive backlog and several implemented
   debug families that are not published. The cheapest coverage gain is
   publication, not another mechanic.
2. **The public model-family coverage is essentially tabular.** CNN, GRU,
   Transformer, and MPNN results are documented but their code is not in the
   public tree and they are not in the frozen runner. The first release should
   make structured baselines public and comparable.
3. **The freeze gates currently select for easy tasks.** A valid task with a
   weak learned baseline is excluded, which hides the most diagnostic failures
   (twin-line assignment, decentralized triage, replacement handoff). The first
   release should add a challenge tier and separate task validity from baseline
   quality.
4. **The largest missing benchmark families need structural mechanics, not more
   content.** They are multi-agent/communication, partial-observability/POMDP
   control, learned world-model planning, end-to-end relational/graph learning,
   long-horizon temporal control, causal intervention, risk-sensitive control,
   OOD/layout, and generative design. These map naturally to three flagship
   mechanics: the assembly edge, sequential crews under uncertainty, and a
   richer layout/grammar.
5. **One flagship per release.** Each release below has one flagship mechanic
   and, at most, one closer that reuses the same surface. A release that mixes
   unrelated mechanics is a scope failure, not a coverage win.

The sequence is therefore:

```text
0.5.0  publish and measure        (no new world; coverage + baselines + method)
0.6.0  production tree            (assembly edge; demand uncertainty if skilled)
0.7.0  uncertain repair           (sequential crews + stochastic faults/POMDP)
0.8.0  spatial production grammar (layout/scale/splitters; optional inventory/quality)
```

The generative line is conditional: it follows the grammar, not the calendar.

### 1.1 Status snapshot (2026-11-27)

| Work item | Branch | Status |
|---|---|---|
| Public baselines | `feat/0.5.0-public-baselines` | merged to main; CNN/MPNN/GRU/Transformer tests pass |
| Reliability contract | `feat/0.5.0-reliability-contract` | merged; full suite CVaR +17.62 [13.90, 21.68] |
| Partial throughput | `feat/0.5.0-partial-throughput` | merged; full suite window GBDT R² 0.897 |
| Wired cascade | `feat/0.5.0-wired-cascade` | merged; graph_mp R² 0.124, +0.018 < +0.05; diagnostic |
| Coverage suite | `feat/0.5.0-coverage-suite` | merged and frozen as `factory-v0.4`; 8 tasks, 7 pass / 1 diagnostic |
| Assembly edge | `feat/0.6.0-assembly-*` | merged and frozen as `factory-v0.5`; four tasks, 4/4 pass; demand uncertainty deferred |
| 0.7.0 design | `feat/0.7.0-uncertain-repair-design` | branch ready; RFC 0032 and task cards; design only |

`factory-v0.4` is **frozen**: eight tasks, **7 pass / 1 diagnostic**, with a
checked-in expected summary and zero-mismatch full check (reliability +17.62
CVaR, partial 0.897, crew-schedule Q 256.4/1.00, crew-triage oracle 456 vs
greedy 378, preventive wire 260 vs reactive 195.3, recipe 318 vs fast 278,
threshold learner 250, wired diagnostic).

`factory-v0.5` is **frozen**: four assembly tasks, **4/4 pass** (control Q 460
vs random 429.2, planning CEM 428 vs oracle 430, BOM GBDT R² 0.503,
intervention GBDT R² 0.944 with +1.62 of +2.00 oracle gain). Demand uncertainty,
layout splits, and logged-data causal identification are deferred to a later
version; the freeze review records them.

The next step is the 0.7.0 sequential-crew / uncertain-repair implementation.

### 1.2 How this plan uses the analysis

| Analysis section | Use in this roadmap |
|---|---|
| §0 Executive summary | Sequencing and top priorities |
| §1 Audit / status inconsistencies | 0.5.0 documentation and reproducibility work |
| §2 Benchmark-family gaps | 0.5.0 coverage slate; 0.6.0–0.8.0 mechanics |
| §3 Model-family gaps | W2 public baseline workstream |
| §4 Mechanics | 0.6.0–0.8.0 flagship and closer scope |
| §5 Promotion analysis | 0.5.0 coverage/challenge slate; promotion ledger |
| §6 Other improvements | W3 evaluation methodology and W4 docs/reproducibility |
| §7 Proposed roadmap | The four-release sequence below |

The analysis remains the detailed evidence; this plan is the execution view.

## 2. Version map

Package releases and benchmark versions are independent. Keep the mapping
explicit in every card.

| Package | Benchmark | Theme | Status target |
|---|---|---|---|
| 0.5.0 | `factory-v0.4` | Coverage suite, challenge tier, public baselines, methodology | new frozen coverage benchmark |
| 0.6.0 | `factory-v0.5` | Production tree: assembly edge + demand uncertainty | new frozen benchmark |
| 0.7.0 | `factory-v0.6` | Uncertain repair: sequential crews + stochastic faults | new frozen benchmark |
| 0.8.0 | `factory-v0.7` | Spatial production grammar: layout/scale/splitters | new frozen benchmark |
| 0.8.0 stretch | `factory-v0.8` | Generative layout/recipe, only if the grammar audit passes | diagnostic or frozen, not both |

`factory-v0.1`, `v0.2`, and `v0.3` stay immutable. A new benchmark version may
reference the old core, but must not edit the old assets or expected summaries.

### 2.1 Tiered benchmark architecture

To avoid benchmark bloat, use tiers rather than a single ever-growing score:

| Tier | Contents | Reported as |
|---|---|---|
| `core` | v0.3 12-task headline, unchanged | continuity/score |
| `coverage` | v0.4 positive backlog tasks | coverage score |
| `challenge` | valid tasks with negative learned baselines | open challenges |
| `production` | v0.5 assembly/demand tasks | production score |
| `multiagent` | v0.6 crew/communication/POMDP tasks | multi-agent score |
| `spatial` | v0.7 layout/grammar/inventory/quality tasks | spatial score |
| `generative` | v0.8 conditional generation tasks | diagnostic or score |

A runner should be able to execute one tier or the full set. The full set is
compute-heavy; CI should run the cheap core/coverage subsets and a scheduled
full check. Do not sum tiers into a single leaderboard score.

## 3. Planning rules

These inherit the project intent and the coverage map's decision rules:

1. **Frozen stays frozen.** New work targets a new benchmark version.
2. **One flagship per release.** A closer is allowed only if it reuses the same
   world surface and answers the same diagnostic question.
3. **Task validity first.** A task needs a deterministic contract, disjoint
   splits, and at least one non-trivial scripted/oracle baseline. A learned
   baseline is reported, not required to pass.
4. **Challenge tier, not goalpost moves.** If a valid task is hard for current
   models, publish it as a challenge. Do not lower a threshold, re-run a failed
   block, or tune on evaluation seeds to force a promotion.
5. **Public evidence.** A model family counts as covered only if its code is in
   the public tree and it runs in a public benchmark tier. Doc-only/private
   results are diagnostics, not coverage.
6. **Opt-in mechanics.** Every new mechanic must leave the default hashes and
   the frozen v0.3 assets unchanged.
7. **Pre-register and report negatives.** Every new task has a card and a
   pre-registration; negative results are reported first.
8. **Cost is a metric.** Report sample efficiency, training/inference cost, and
   parameter/artifact size for every learned family.
9. **Small world, deep tasks.** Prefer observation/action/task variants over
   more entity types.
10. **No content treadmill.** A mechanic enters only with a named weakness and a
    task that separates families.

## 4. Cross-cutting workstreams

These run across all releases and should be staffed before the mechanic work.

| ID | Workstream | Output | Owner |
|---|---|---|---|
| W1 | Benchmark engineering | tiered runner, expected summaries, CI cheap/full | benchmark |
| W2 | Public baselines | CNN/UNet, GNN/MPNN/GAT, Transformer/GRU, OR/CP-SAT, optional offline RL | models |
| W3 | Evaluation methodology | episode-level cluster bootstrap, private holdout, layout split, challenge tier, normalized regret | evaluation |
| W4 | Docs and reproducibility | coverage ledger, status source of truth, link checker, public code links | docs |
| W5 | World mechanics | assembly edge, sequential crews, stochastic faults, layout grammar | world |
| W6 | Release engineering | version pins, release audit, public scrub, tags | release |

Dependencies:

- W2 and W3 must land before the 0.5.0 coverage freeze; otherwise the coverage
  suite is another tabular benchmark.
- W4 must land before 0.5.0; otherwise the same status inconsistencies continue.
- W5 starts after 0.5.0 scope approval, but research spikes can start earlier
  behind feature flags.
- W6 runs at every release; no release without a clean audit.

## 5. 0.5.0 — Coverage release (no new world)

### 5.1 Goal

Publish the positive backlog, add public structured baselines, and fix the
evaluation methodology **before** adding another mechanic.

This is a curation/publication release. It does not introduce a new game rule,
so it does not violate "one mechanic per milestone."

### 5.2 Scope

**In scope:**

- `factory-v0.4` coverage suite with 6–8 tasks.
- A challenge tier for hard, valid tasks with negative learned baselines.
- Public structured baselines: CNN/UNet, GNN/MPNN, Transformer/GRU, OR/CP-SAT.
- Episode-level cluster bootstrap; private holdout; layout split.
- Normalized regret/success/cost; per-seed failure categories.
- Coverage-map ledger: task IDs, benchmark membership, status, evidence.
- Status/doc/reproducibility fixes from the analysis §1.5 and §6.

**Out of scope:**

- Any new world mechanic (assembly, crews, faults, layout grammar).
- Edits to v0.1/v0.2/v0.3 assets or expected summaries.
- A public leaderboard.
- Text/pixels adapters.
- Deep RL/offline RL expansion beyond the existing public baselines; those are
  0.6.0+ baseline tracks.

### 5.3 Coverage suite tasks

Promote from the positive backlog; do not re-run pilots unless a task lacks a
stable expected summary.

**Public-evidence caveat:** some backlog tasks have public task cards and world
support, but their experiment harness lives under `experiments/...` and is not
in the public tree. As of this plan, that includes the reliability contract
(0031), wired cascade (0032), and partial-throughput (0024) harnesses. Promotion
requires a public reimplementation with the same contract, not just a card.
The reliability-contract public harness has now been started on
`feat/0.5.0-reliability-contract`; the other two are still W1 work.

| Task | Source | Family | Why it is here | Baseline gap to add |
|---|---|---|---|---|
| reliability-contract | 0031 | risk/uncertainty | mean/CVaR trade; risk-sensitive selection | CVaR/quantile baseline |
| wired-cascade | 0032 | relational/graph | graph cut, failure propagation | GNN/MPNN/GAT |
| crew-schedule | 0041 | spatial scheduling | travel, deadlines, budget | CP-SAT/OR, GNN/Transformer |
| crew-triage | 0055 | multi-agent (centralized) | coordination, oracle gap | MAPPO/QMIX, CP-SAT |
| preventive-wire | 0035 | temporal credit | warning-to-action timing | POMDP/belief, survival |
| partial-throughput | 0024 | partial observability | missing features, history | GRU/Transformer/SSM |
| recipe-choice or contract-board | 0070/0074 | production control | queue/contract decision | CEM/OR, tabular Q |
| maintenance-threshold | 0038 | bandit/context | representation/exploration | Thompson/LinUCB |

If eight is too many for one release, cut `maintenance-threshold` and
`recipe-choice` first; keep the six families that are otherwise absent
(risk, graph, scheduling, multi-agent, temporal, partial observability).
For the multi-agent slot, `crew-triage` (0055) and two-crew coordination
(0042/0044) are alternatives; pick one, not both.

### 5.4 Challenge tier

Publish valid tasks with negative learned baselines. They are not headline
scores; they are open challenges with oracle/scripted references.

| Task | Source | Evidence | Challenge statement |
|---|---|---|---|
| twin-line assignment | 0046 | oracle 441, greedy 419, Q 217/0.00 | Can a learned/assignment policy close the oracle gap? |
| decentralized triage | 0077 | global 748, local greedy 460, Q 582/0.47 | Can a local/communication policy reach 0.60 success? |
| replacement handoff | 0060 | replacement oracle 476 vs 456; best scripted 386 | Can a handoff policy beat no-replacement? |
| recall + twin-line | 0047 | recovery +240; oracle-greedy +9 | Does repeated failure restore the layout gap? |
| maintenance calibration | 0084 | diagnostics ECE 0.0054; full view 0.0929 | Can a calibration method fix the registered view? |

A challenge task still needs a card, split, expected summary, and a reproducible
runner. It simply does not need a winning learned baseline.

### 5.5 Public baselines

Add code under an optional `train` extra; keep the core runnable with NumPy and
scikit-learn.

- `harness/models/cnn.py` — small CNN for grid tasks; flattened MLP fallback.
- `harness/models/gnn.py` — MPNN/GIN in Torch without a PyG dependency;
  `graph_mp` remains the NumPy fallback.
- `harness/models/sequence.py` — GRU and small Transformer.
- `harness/or.py` — exhaustive/ILP for small plans; OR-Tools optional.
- `harness/offline_rl.py` — optional BC/CQL/IQL/DT track for 0.6.0+; do not
  block the 0.5.0 coverage freeze on it.

Every model family must have a declared budget, seeds, and a cost fingerprint.
Do not compare a default MLP to a tuned GBDT and call it a family verdict.

### 5.6 Methodology changes

- **Episode-level cluster bootstrap** for all CIs; rows within an episode are
  correlated.
- **Private holdout**: a seed block not used during development, reported
  separately.
- **Layout split**: a fifth split with unseen layouts; keep the existing
  scenario shift for continuity.
- **Normalized regret**: `(oracle - score) / (oracle - random)` or a documented
  equivalent; report success and cost alongside.
- **Failure categories**: noop, missed deadline, wrong assignment, brownout,
  aborted job, wasted repair, etc.
- **Challenge tier**: see §5.4.
- **Fair tuning**: validation-only selection; report hyperparameters and
  compute.
- **Ablations**: no-mechanic controls for any new task; for promoted tasks, the
  existing fixed-policy baselines are the controls.

### 5.7 Deliverables

- `benchmarks/factory-v0.4/`:
  - `card.md`, `spec.md`, `benchmark.toml`;
  - `expected/summary.json`;
  - `freeze-review.md`.
- `fabline coverage-suite` with the eight-task coverage tier, a `--fast` smoke
  mode, and `--expected`/`--check-expected` regression checks. The challenge
  task list is documented but not integrated.
- Task cards for the coverage and challenge tasks (some exist; update status).
- `docs/coverage-map.md` updated to the ledger schema, or a new
  `docs/coverage-ledger.md` linked from it.
- `docs/benchmark.md` updated to the current command/task list.
- Public baseline code and tests.
- A status source of truth and a link/coverage check.

### 5.8 Exit criteria

- [ ] v0.3 assets and expected summaries unchanged.
- [ ] v0.4 expected summary deterministic; cheap/full checks pass.
- [ ] Every coverage/challenge task has a card, split, expected summary, and a
      non-trivial reference baseline.
- [ ] At least one public CNN, GNN, sequence, and OR baseline runs in CI.
- [ ] CIs are episode-level; private holdout and layout split are reported.
- [ ] Challenge tasks report negative learned baselines without gate changes.
- [ ] Coverage-map ledger has task IDs, status, benchmark membership, evidence.
- [ ] Status inconsistencies from analysis §1.5 are fixed.
- [ ] Public/private experiment links are honest; no doc-only result counts as
      coverage.

### 5.9 Risks

| Risk | Mitigation |
|---|---|
| Benchmark bloat | Tiered suite; coverage tier separate from core score |
| Promoted tasks lack stable expected summaries | Re-run only the deterministic benchmark block; do not tune on test |
| Model code adds dependencies | Optional `train` extra; NumPy/sklearn fallbacks |
| Statistical changes make old numbers incomparable | Apply to v0.4 only; v0.3 stays frozen |
| Challenge tier is misread as "solved" | Label clearly; no headline score; report oracle/scripted |
| Scope creep into mechanics | Freeze 0.5.0 scope before implementation; defer all new world rules |

## 6. 0.6.0 — Production tree (assembly edge; demand uncertainty deferred)

### 6.1 Goal

Turn the production mix from a global two-way switch into a small production
graph with a shared intermediate, and add demand-side uncertainty only if the
forecast signal carries skill.

This is one integrated mechanic: **demand-driven multi-item production**, the
0.4.0 review's leading candidate. It addresses the 0089 finding that the
recipe-only mix has no schedule gap.

### 6.2 Mechanic

Opt-in `ProductionTreeConfig`:

```text
ORE -> INGOT                         (furnace)
INGOT -> GEAR                        (assembler recipe A, existing fast recipe)
INGOT -> COMPONENT                   (assembler recipe B)
INGOT + COMPONENT -> GEAR            (assembler recipe C, assembly edge)
```

Requirements:

- per-assembler recipe assignment, not only a global switch;
- component is a logistics item with its own buffer/route;
- depot accepts gear and component; orders can request either;
- optional setup time on recipe switch;
- optional byproduct/purge pressure;
- default world hash and v0.3 assets unchanged.

Keep the recipe set to 3–4 recipes and one intermediate. The point is the DAG,
the shared intermediate, and the delay, not a content catalog.

### 6.3 Demand uncertainty (deferred)

Demand arrivals were not added in 0.6.0. They remain a conditional follow-up,
not part of `factory-v0.5`. Add only if the forecast/observation carries
measurable skill:

- seeded order arrivals, cancellations, and expedites;
- a noisy lead-time/queue signal with real predictive value;
- optional accept/reject and capacity reservation;
- demand shocks within an episode.

Gate: a forecast model must beat the base rate on held-out episodes before
demand-calibration or online-control claims are made. If the gate fails, ship
the assembly edge alone and defer demand uncertainty.

### 6.4 Tasks

| Task | Kind | Observation | Action/reward | Gate |
|---|---|---|---|---|
| `assembly-control` | control | production graph + buffers + orders | per-assembler recipe/route; fulfilled value | oracle-scripted ≥10; learned-random ≥10; success ≥0.60 |
| `assembly-planning` | planning | initial state + known orders | initial recipe/line plan; plan value | oracle-scripted ≥10; CEM/OR within 10; success ≥0.60 |
| `bom-forecast` | regression | graph + buffers + history | predict component starvation/gear output | R²/MAE over persistence; shift |
| `recipe-intervention` | causal | state + recipe intervention | counterfactual output/order effect | target R² ≥0.30 and ≥type-only +0.20 |
| `demand-forecast` | temporal | partial order book + history | arrivals/late risk | deferred |
| `order-arrival-control` | control | partial order book | accept/produce/switch | deferred |

The frozen release includes `assembly-control`, `assembly-planning`,
`assembly-bom`, and `assembly-intervention`. The demand pair is deferred. The
BOM and intervention tasks use decision-noise logs and paired counterfactual
rollouts; they do not require an order stream.

### 6.5 Baselines

- Scripted: always gear/component/assembly; EDF; value; buffer-aware; random.
- Tabular Q; CEM; MILP/CP-SAT; GNN/MPNN; Transformer; PPO/SAC; CQL/IQL/DT.
- Demand: GBDT/GRU/Transformer/SSM; DeepAR/TFT-style; conformal; forecast-then-
  optimize; MPC; bandits.

### 6.6 Deliverables

- RFC and ADR for the production tree.
- Task cards and pre-registrations.
- `factory-v0.5` benchmark with a `production` tier.
- Expected summary and freeze review.
- Tests for component logistics, recipe state, hash invariants, and action masks.

### 6.7 Exit criteria

- [x] Default world hash and v0.1–v0.4 assets unchanged.
- [x] Assembly control, planning, BOM, and causal gates pass.
- [ ] Demand forecast skill gate is reported; deferred with the demand pair.
- [ ] At least one GNN and one OR baseline run on the production tier; not
      integrated, scope cut recorded in the freeze review.
- [x] Negative/saturated results are reported first.
- [x] `factory-v0.4` remains immutable.

### 6.8 Kill criteria

- If the assembly edge does not create a schedule gap over the best fixed/scripted
  policy, keep it as a diagnostic and do not freeze a new headline task.
- If demand uncertainty has no forecast skill, defer it; do not add a redundant
  view.
- If the recipe graph grows beyond 3–4 recipes or becomes a content catalog,
  stop and cut scope.

## 7. 0.7.0 — Uncertain repair (sequential crews + stochastic faults)

### 7.1 Goal

Replace one-shot crew macro-actions with true per-agent sequential control under
partial observability, and make faults stochastic/noisy so belief state and
calibration matter. The integrated theme is **uncertain repair**: multiple
crews, local views, communication, and stochastic failures.

This is one flagship (sequential multi-agent) with one closer on the same
surface (stochastic faults/sensors). If the owner wants strictly one mechanic,
ship sequential crews first and move stochastic faults to 0.8.0.

### 7.2 Sequential crew mechanic

- crews have positions and move one cell per decision (or a small macro move);
- actions: move N/E/S/W, wait, repair, report, maybe recharge;
- local observations with a radius/occlusion, not binary distance;
- communication budget, delay, and noise;
- dynamic faults, recalls, and agent failure;
- team reward or per-crew rewards with credit assignment.

Tasks:

| Task | What it tests | Baselines |
|---|---|---|
| `crew-sequential` | cooperative repair with 2–3 crews | centralized oracle, greedy/nearest/EDF, independent Q, MAPPO, QMIX, MADDPG, COMA |
| `crew-communication` | communication budget/delay/noise | no communication, shared, CommNet/TarMAC/DIAL |
| `agent-failure` | handoff/replacement after failure | oracle, scripted handoff, learned handoff |

Gates:

- coordination gain ≥10 over single crew;
- communication gain ≥10 over no communication;
- oracle gap ≥10;
- best learned success ≥0.60, or publish as a challenge;
- cost and message volume reported.

### 7.3 Stochastic faults / POMDP mechanic

- stochastic onset (hazard depends on wear/load/maintenance);
- sensor noise, drift, false positives/negatives;
- hidden wear or hidden fault state;
- correlated failures via shared power/load;
- inspection action.

Tasks:

| Task | What it tests | Baselines |
|---|---|---|
| `fault-detection-noise` | detection/calibration under noise | GBDT, HMM, Kalman/particle filter, survival, conformal |
| `pomdp-maintenance` | hidden wear; inspect/repair/continue | threshold/reactive, POMDP/belief RL, RNN/SSM |
| `root-cause` | identify source of a production drop | causal discovery, GBDT, graph models |

Gates:

- detection skill over base rate;
- ECE ≤0.05 if calibration is claimed;
- control gain over threshold;
- success, or challenge tier.

### 7.4 Baselines

- MARL: MAPPO, QMIX/VDN, MADDPG, COMA.
- Communication: CommNet, TarMAC, DIAL.
- POMDP: belief-state RL, POMDP solver, HMM, Kalman/particle filter.
- Survival/conformal; GNN/Transformer for local observations.
- OR/CP-SAT for the centralized assignment reference.

### 7.5 Deliverables

- RFC/ADR for sequential crews and stochastic faults.
- Task cards/pre-regs.
- `factory-v0.6` with `multiagent` tier.
- Replay/hash tests for stochastic mechanics.
- Expected summary and freeze review.

### 7.6 Exit criteria

- [ ] v0.5 assets unchanged.
- [ ] Action masks, movement, communication, and replay are deterministic.
- [ ] Coordination/communication gains are measured; challenge tier is used if
      learned success <0.60.
- [ ] Stochastic faults are seeded and included in the hash when enabled;
      fault-free hashes unchanged.
- [ ] Calibration is reported only with detection skill.
- [ ] At least one MARL and one POMDP baseline run in the tier.

### 7.7 Kill criteria

- If sequential crews add no coordination/communication gain over the existing
  one-shot tasks, keep the old tasks as the multi-agent surface and retire the
  sequential variant.
- If stochastic faults do not change decisions or calibration, retire them as a
  diagnostic.
- If the combined theme is too large, split 0.7.0 into sequential crews and
  0.8.0 stochastic faults; do not ship both half-finished.

## 8. 0.8.0 — Spatial production grammar (layout, scale, splitters)

### 8.1 Goal

Make layout and flow structure a first-class variable: larger/random layouts,
splitters/mergers, routing, and scale transfer. This fills the spatial,
relational, OOD, and planning gaps that the small fixed layouts cannot.

Inventory/depletion and quality are optional closers only if they reuse the
same spatial/resource surface. Generative layout/recipe is conditional on the
grammar audit.

### 8.2 Layout/grammar mechanic

- larger/random layouts and obstacles;
- random line offsets/orientations;
- splitter/merger entities and route choice;
- multi-line/shared-resource layouts;
- layout split and scale split.

Tasks:

| Task | What it tests | Baselines |
|---|---|---|
| `layout-shift` | throughput/bottleneck on unseen layouts | CNN/UNet/ViT, GNN/GAT, Transformer, MLP |
| `scale-transfer` | train small, test large | same, meta-learning/domain generalization |
| `route-control` | splitters/mergers, build a route | A*/MCTS, GNN, RL, OR |
| `line-balancing` | balance multiple lines | OR/CP-SAT, RL, GNN |

Gates:

- in-distribution vs OOD gap;
- model ranking/ordering;
- success/throughput;
- no layout-seed leakage.

### 8.3 Optional closer: inventory/depletion

If it reuses the same spatial/resource surface:

- finite ore patches that deplete;
- storage/warehouse buffers with holding costs;
- multiple lines sharing ore/power/crews;
- expansion/replenishment decisions.

Tasks: `resource-allocation`, `expansion-planning`, `inventory-control`.
Baselines: MILP/CP-SAT, MPC, RL, queueing/fluid.
Gate: oracle gap, feasibility, cost.

### 8.4 Optional closer: quality/defects

If it reuses the same production/layout surface:

- defect probability depends on wear/speed/power/recipe;
- inspection, rework, scrap;
- quality-speed trade-off.

Tasks: `defect-prediction`, `inspection-control`, `quality-aware-scheduling`.
Baselines: calibration, Bayesian, POMDP, constrained RL, OR.
Gate: skill/calibration, control gain.

### 8.5 Conditional: generative layout/recipe

Do not start with a model. Start with a grammar audit:

- at least 20 unique structural sequences;
- diversity ≥0.25;
- validity ≥0.90;
- a downstream objective that distinguishes generated structures.

If the audit passes, add `layout-generation`/`recipe-generation` with
VAE/GAN/diffusion/flow/autoregressive baselines and a `generative` tier.
If it fails, publish the audit as a negative result and defer to 0.9.0+.

### 8.6 Deliverables

- RFC/ADR for layout/grammar (and optional inventory/quality).
- Task cards/pre-regs.
- `factory-v0.7` with `spatial` tier; `factory-v0.8` only if the generative
  audit passes.
- Split definitions and generator tests.
- Expected summary and freeze review.

### 8.7 Exit criteria

- [ ] v0.6 assets unchanged.
- [ ] Layout/scale splits are disjoint and reproducible.
- [ ] Splitter/merger invariants and item conservation hold.
- [ ] OOD gap and model ordering are reported.
- [ ] Inventory/quality tasks are included only if their gates pass.
- [ ] Generative audit is reported; no generative benchmark on <20 structures.

### 8.8 Kill criteria

- If layout shift does not separate model families, keep it as a diagnostic.
- If splitters/mergers add complexity without a new decision, cut them.
- If inventory/quality do not add a new decision over existing production
  tasks, defer them.
- If the generative audit fails, defer; do not train a model on 7 lines.

## 9. Backlog and dependencies

Priority is relative to the release. `S/M/L` is effort, not calendar time.

| Release | Workstream | Item | Type | Depends on | Effort |
|---|---|---|---|---|---|
| 0.5.0 | W1 | Tiered `factory-v0.4` runner | new | plan approval | M |
| 0.5.0 | W1 | Coverage suite (8 tasks) | promote | v0.3 cards | M |
| 0.5.0 | W1 | Challenge tier (5 tasks) | promote | v0.3 cards | S |
| 0.5.0 | W2 | CNN/UNet baseline | new | W1 dataset | M |
| 0.5.0 | W2 | GNN/MPNN/GAT baseline | new | W1 dataset | M |
| 0.5.0 | W2 | Transformer/GRU baseline | new | W1 dataset | M |
| 0.5.0 | W2 | OR/CP-SAT baseline | new | W1 tasks | M |
| 0.5.0 | W3 | Episode-level bootstrap | new | W1 | S |
| 0.5.0 | W3 | Private holdout | new | W1 | S |
| 0.5.0 | W3 | Layout split | new | generator | M |
| 0.5.0 | W3 | Challenge tier policy | new | owner decision | S |
| 0.5.0 | W4 | Coverage ledger/status source | new | W1 | M |
| 0.5.0 | W4 | Link/coverage checks | new | W4 | S |
| 0.5.0 | W4 | Doc/status fixes | fix | — | S |
| 0.5.0 | W6 | v0.4 freeze/release audit | release | all | S |
| 0.6.0 | W5 | Production tree RFC/ADR | design | 0.5.0 | S |
| 0.6.0 | W5 | Per-assembler recipe + component logistics | mechanic | RFC | L |
| 0.6.0 | W5 | Assembly control/planning tasks | task | mechanic | M |
| 0.6.0 | W5 | BOM forecast/causal tasks | task | mechanic | M |
| 0.6.0 | W5 | Demand arrivals/forecast (conditional) | mechanic | skill gate | M |
| 0.6.0 | W2 | GNN/OR/world-model/offline-RL baselines | baseline | tasks | M |
| 0.6.0 | W6 | v0.5 freeze/release audit | release | all | S |
| 0.7.0 | W5 | Sequential crew RFC/ADR | design | 0.6.0 | S |
| 0.7.0 | W5 | Movement/communication/local views | mechanic | RFC | L |
| 0.7.0 | W5 | Crew sequential/communication/failure tasks | task | mechanic | M |
| 0.7.0 | W5 | Stochastic faults/noise/hidden state | mechanic | 0.6.0 | M |
| 0.7.0 | W5 | POMDP detection/maintenance/root-cause tasks | task | mechanic | M |
| 0.7.0 | W2 | MARL/communication/POMDP baselines | baseline | tasks | L |
| 0.7.0 | W6 | v0.6 freeze/release audit | release | all | S |
| 0.8.0 | W5 | Layout/grammar RFC/ADR | design | 0.7.0 | S |
| 0.8.0 | W5 | Splitters/mergers/routing | mechanic | RFC | L |
| 0.8.0 | W5 | Larger/random layouts + splits | mechanic | RFC | M |
| 0.8.0 | W5 | Layout/scale/route tasks | task | mechanic | M |
| 0.8.0 | W5 | Inventory/depletion (optional) | closer | layout | M |
| 0.8.0 | W5 | Quality/defects (optional) | closer | layout | M |
| 0.8.0 | W5 | Generative grammar audit | gate | layout | S |
| 0.8.0 | W5 | Generative tasks (conditional) | task | audit pass | L |
| 0.8.0 | W2 | CNN/GNN/OR/MPC/generative baselines | baseline | tasks | L |
| 0.8.0 | W6 | v0.7/v0.8 freeze/release audit | release | all | S |

## 10. Promotion ledger

The detailed per-task reasoning is in the analysis §5.2. The release decisions:

| Task | Decision | Release |
|---|---|---|
| reliability-contract (0031) | promote | 0.5.0 |
| wired-cascade (0032) | promote + GNN | 0.5.0 |
| wire-repair (0033) | reserve; promote if the temporal slot is not filled by preventive-wire | 0.5.0 |
| preventive-wire (0035) | promote | 0.5.0 |
| maintenance-threshold (0038) | promote as bandit diagnostic | 0.5.0 |
| crew-schedule (0041) | promote | 0.5.0 |
| two-crew coordination (0042/0044) | promote one of this or crew-triage | 0.5.0 |
| crew-triage (0055) | promote one of this or two-crew coordination | 0.5.0 |
| recipe-choice (0070) / contract-board (0074) | promote one | 0.5.0 |
| partial-throughput (0024) | promote | 0.5.0 |
| twin-line assignment (0046) | challenge | 0.5.0 |
| decentralized triage (0077) | challenge; revisit with communication | 0.5.0 / 0.7.0 |
| replacement handoff (0060) | challenge; redesign handoff | 0.5.0 / 0.7.0 |
| recall + twin-line (0047) | redesign; challenge if still near-miss | 0.5.0 / 0.7.0 |
| maintenance calibration (0084) | diagnostic; add calibration method | 0.5.0 |
| three-crew recall (0063) | diagnostic; harder variant later | 0.7.0 |
| production mix (0089) | diagnostic; precondition for assembly | 0.6.0 |
| transition planning (0083/0085/0086) | new nonlinear world model | 0.6.0+ |
| deep/offline RL (0092) | new budget on harder tasks | 0.6.0+ |
| build planning (0075) | redesign with dense subgoals | 0.7.0+ |
| generative audit (0087) | grammar first | 0.8.0 |
| single deadline contract (0073) | retire; use contract board | — |
| timed repair (0034) | diagnostic | — |
| negative pilots (0036, 0039, 0043, 0049, 0051, 0053, 0058, 0059, 0061, 0066, 0067, 0081, 0082) | retire/keep as negative controls | — |

## 11. Release gates and checklist

Every release:

- [ ] Frozen predecessor assets and expected summaries unchanged.
- [ ] New mechanics opt-in; default hashes unchanged.
- [ ] Every task has a card, pre-registration, split, expected summary, and
      baseline.
- [ ] Cheap CI and full scheduled check pass.
- [ ] Negative and saturated results are reported first.
- [ ] No gate lowering; challenge tier used instead.
- [ ] Public/private evidence is labeled.
- [ ] Release audit and public scrub pass.
- [ ] Docs, cards, and dataset cards updated.
- [ ] Tag and release notes.

Release-specific gates are in §5.8, §6.7, §7.6, and §8.7.

## 12. Risks and kill criteria

| Risk | Likelihood | Impact | Mitigation / kill |
|---|---|---|---|
| Scope creep across four releases | high | high | One flagship per release; owner approves scope; freeze before implementation |
| Benchmark bloat | high | medium | Tiered architecture; separate scores; no summed leaderboard |
| Coverage suite is still tabular | medium | high | Public structured baselines required before 0.5.0 freeze |
| Challenge tier misread as solved | medium | medium | Clear labeling; no headline score; oracle/scripted references |
| Assembly graph becomes content treadmill | medium | high | 3–4 recipes; one intermediate; stop if it grows |
| Demand uncertainty has no skill | medium | medium | Skill gate; defer if it fails |
| Multi-agent sequential scope too large | high | high | Split 0.7.0 if needed; challenge tier; no half-finished release |
| Stochastic mechanics break determinism | medium | high | Seeded RNG; hash when enabled; replay tests |
| Layout grammar/complexity explodes | medium | high | Start with layout split; splitters only if a new decision appears |
| Generative audit fails again | high | medium | Audit first; defer; do not train on 7 lines |
| Model code dependencies block CI | medium | medium | Optional extras; NumPy/sklearn fallbacks |
| Statistical changes invalidate old numbers | medium | medium | Apply to new versions only; v0.3 stays frozen |
| Owner bandwidth/release cadence | medium | high | Sequence releases; 0.5.0 is the only must-do next |

## 13. Branch and PR strategy

- **Plan branch:** `plan/0.5.0-0.8.0-roadmap` contains this document and the
  analysis. It is a draft PR candidate; no frozen assets are touched.
- **Feature branches:** one per workstream, e.g.
  - `feat/0.5.0-coverage-suite`
  - `feat/0.5.0-public-baselines`
  - `feat/0.5.0-eval-methodology`
  - `feat/0.5.0-docs-ledger`
  - `feat/0.6.0-assembly-edge`
  - `feat/0.7.0-sequential-crew`
  - `feat/0.7.0-stochastic-faults`
  - `feat/0.8.0-layout-grammar`
- **PR rules:**
  - small PRs; one concern each;
  - rebase on `main` before review;
  - never edit frozen benchmark tags/assets;
  - include tests and docs;
  - report what was intentionally not changed.
- **Concurrent work:** the plan branch is isolated; feature branches can start
  from `main` after the relevant scope is approved. Do not push directly to
  `main`; use PRs. Tag frozen benchmarks only after the release gate.
- **Push:** the plan branch is ready to push for safekeeping/PR; pushing a new
  branch does not obstruct `main`.

## 14. Open decisions for the owner

1. **Coverage first vs assembly first.** Recommendation: coverage first; it is
   cheap, it fixes the benchmark, and it gives the assembly work a fair
   measurement surface.
2. **Tiered benchmark architecture.** Recommendation: yes; keep the v0.3 core
   score separate from coverage/challenge/production tiers.
3. **0.5.0 slate.** Recommendation: eight tasks; cut `maintenance-threshold` and
   `recipe-choice` first if too large.
4. **Challenge tier policy.** Recommendation: publish valid hard tasks with
   negative learned baselines; do not lower gates.
5. **Public baseline scope.** Recommendation: CNN/UNet, GNN/MPNN, Transformer/
   GRU, OR; Torch/OR-Tools optional; fallbacks for CI.
6. **0.7.0 integration.** Recommendation: "uncertain repair" as one integrated
   theme; if too large, split sequential crews and stochastic faults into
   separate releases.
7. **0.8.0 scope.** Recommendation: layout/grammar flagship; inventory/quality
   only if they reuse the same surface; generative conditional.
8. **Benchmark version mapping.** Recommendation: package 0.5.0 -> benchmark
   v0.4, 0.6.0 -> v0.5, 0.7.0 -> v0.6, 0.8.0 -> v0.7; v0.8 only for generative.
9. **Private holdout.** Recommendation: reserve a seed block, do not publish it.
10. **Text/pixels/language.** Recommendation: defer; keep the factory-specific
    scope.

## 15. What not to do

- Do not edit `factory-v0.1`, `v0.2`, or `v0.3` assets or expected summaries.
- Do not add another order-control, throughput, or calibration variant before
  the coverage release.
- Do not tune PPO/BC after 0092.
- Do not lower a gate, re-run a failed block, or tune on evaluation seeds to
  force a promotion.
- Do not add a generative model on the seven current line sequences.
- Do not count private/doc-only experiments as public coverage.
- Do not add trains, fluids, 3D, or full circuit networks before the coverage
  and production tree are published.
- Do not create a public leaderboard.
- Do not mix unrelated mechanics in one release.
- Do not add content volume without a diagnostic question.

## 16. Immediate next steps

1. **Owner decision:** approve the coverage-first sequence and the 0.5.0
   coverage/challenge slate.
2. **Freeze the 0.5.0 scope:** write `benchmarks/factory-v0.4/spec.md` and
   `benchmark.toml`; do not add mechanics.
3. **Open W1–W4 issues:** tiered runner, public baselines, evaluation
   methodology, docs/ledger.
4. **Build the tiered runner skeleton:** `benchmark-v04 --tier
   core|coverage|challenge`; reuse v0.3 core by reference.
5. **Publish at least one structured baseline per family** (CNN, GNN, sequence,
   OR) before the coverage freeze.
6. **Run the coverage/challenge blocks**, produce the expected summary, and
   fix the status/docs inconsistencies.
7. **Freeze `factory-v0.4`** and publish the coverage report; then open the
   assembly-edge RFC for 0.6.0.

## 17. References

- [`coverage-analysis-2026-11-26.md`](coverage-analysis-2026-11-26.md) — gap
  analysis, promotion ledger, mechanic proposals.
- [`coverage-map.md`](coverage-map.md) — current model/benchmark map.
- [`coverage-review-0.4.0.md`](coverage-review-0.4.0.md) — 0.4.0 review and
  next-slice recommendation.
- [`benchmarks/factory-v0.3/card.md`](../benchmarks/factory-v0.3/card.md) —
  current frozen benchmark.
- [`project_intent.md`](../project_intent.md) — goals and non-goals.
- [`docs/testbed.md`](testbed.md) — contracts and success criteria.
- [`docs/benchmark.md`](benchmark.md) — benchmark protocol.
- RFC 0030 and ADR 0042 — 0.4.0 scope and demand-driven production.

---

*This roadmap is a proposal. It is deliberately ordered by diagnostic value per
unit of cost, not by content appeal. The owner decides which releases are
committed; the analysis remains the source for the detailed gap evidence.*
