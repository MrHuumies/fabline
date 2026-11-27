# FABLINE coverage analysis — gaps, mechanics, and promotion candidates

- **Status:** historical analysis; superseded by the roadmap and the 0.5.0 review
- **Date:** 2026-11-26
- **Inputs:** [`coverage-map.md`](coverage-map.md),
  [`coverage-review-0.4.0.md`](coverage-review-0.4.0.md),
  [`coverage-review-0.3.0.md`](coverage-review-0.3.0.md),
  [`coverage-review-p2.md`](coverage-review-p2.md), the public source tree,
  the experiment records, and `factory-v0.3`.
- **Method:** audit the claims in the map against the frozen benchmark and the
  public code; inventory benchmark families and model families; review every
  failed or unpromoted task; propose mechanics, tasks, baselines, and gates.
- **Companion:** this is a local analysis file. It does not change any frozen
  benchmark, world hash, or public release. Statements such as "not frozen" are
  as of 2026-11-26; see [`coverage-review-0.5.0.md`](coverage-review-0.5.0.md)
  for the final coverage-suite status.

## 0. Executive summary

FABLINE has a strong, unusually legible world and a large research surface. The
main coverage problem is **not a lack of mechanics**. It is that the published
benchmark is much narrower than the research surface, and the coverage map
counts debug/diagnostic tasks alongside frozen benchmark tasks without
distinguishing them.

The short version:

1. **`factory-v0.3` has 12 tasks, but only a narrow slice of the map is
   published.** Seven of the twelve are offline regression, classification, or
   self-supervised projections. There are two small control tasks, two
   true-simulator planning tasks, one calibration task, and one causal
   prediction task. There is no frozen multi-agent task, no partial-observability
   control task, no risk-sensitive control task, no relational-graph headline
   task, no layout/OOD split, no offline-RL task, no generative task, no
   continual/transfer benchmark, and no efficiency task.
2. **The public benchmark is essentially tabular.** The frozen shared suite runs
   mean, persistence, linear, GBDT, MLP, and `graph_mp` (two-hop pooling plus
   GBDT). The order block adds scripted policies, random, and tabular Q. The
   planning block adds CEM, random shooting, a ridge value model, and an oracle.
   CNN, GRU, Transformer, and end-to-end MPNN results exist in experiment
   summaries, but their code lives under `experiments/...` and is not in the
   public tree. They are not in the frozen runner. `graph_mp` is not a learned
   GNN.
3. **Task names and family labels overstate model coverage.** `throughput-grid`
   and `masked-grid` use flattened tabular baselines, not a CNN.
   `throughput-entities` uses
   `graph_mp` features, not an end-to-end GNN. `control-dynamics` is a one-step
   linear/MLP task, not a sequence benchmark. `causal-removal` uses GBDT/MLP on
   target features, not a causal model. This matters when the map says
   "Spatial partial", "Relational partial", or "Causal partial": the task
   exists, but the model family that defines the family is absent.
4. **The world already contains a large positive backlog.** Reliability
   contract (0031), wired cascade (0032), wire repair (0033), preventive wire
   (0035), maintenance-threshold selection (0038), crew scheduling (0041),
   two-crew coordination (0042/0044), twin-line assignment (0046), three-bridge
   triage (0055), recipe choice (0070), byproduct (0072), and contract board
   (0074) are positive or usable. None is in a frozen benchmark. Publishing
   these is the cheapest coverage gain available.
5. **The biggest missing benchmark families** are:
   multi-agent/communication; partial-observability/POMDP control; learned
   world-model planning; end-to-end relational/graph learning; long-horizon
   temporal/sequence control; causal intervention planning/discovery;
   risk-sensitive control; OOD/layout/scale; offline RL and imitation;
   generative design; continual/transfer; and OR/scheduling.
6. **The biggest missing model families** are:
   GNN/MPNN/GAT/GraphSAGE/GIN and graph transformers; CNN/UNet/ViT;
   Transformer/SSM (S4/Mamba); deep RL beyond a 10k-step PPO negative;
   offline RL (CQL/IQL/DT/AWAC/TD3+BC); model-based RL (Dreamer/MuZero/MBPO/
   PETS); MARL and communication (MAPPO/QMIX/MADDPG/COMA/CommNet/TarMAC);
   hierarchical RL; meta/continual learning; imitation beyond BC (DAgger/GAIL/
   IRL); causal discovery/effect estimation; probabilistic/Bayesian/conformal/
   survival models; OR (MILP/CP-SAT/A*/MCTS); MPC/LQR/control theory; and
   generative models (VAE/GAN/diffusion/flow/autoregressive).
7. **The top mechanic recommendations** are:
   (a) the assembly edge as a **per-assembler multi-input recipe graph**, not a
   single global gear/component switch; (b) demand arrivals/cancellations and
   online order uncertainty; (c) true sequential per-crew control with
   communication, not one-shot joint assignment; (d) stochastic faults, sensor
   noise, and hidden state; (e) layout/scale/topology splits; (f) inventory,
   depletion, and shared capacity; (g) quality/defects/rework; (h) a richer
   grammar for generative layout/recipe work.
8. **Promotion is mostly a curation problem, not a gate problem.** The positive
   backlog should be published in a new coverage suite. The near-miss tasks
   (0047, 0048/0050, 0060, 0063, 0077/0081/0082, 0084) should not be promoted
   by lowering thresholds or re-running the same block. They need a mechanic
   change or a stronger baseline, and the benchmark needs a **challenge tier**
   so a valid hard task with a weak learned baseline can be published without
   pretending it is solved.
9. **The freeze-gate methodology is selecting for easy tasks.** Gates that
   require a learned baseline to reach a success threshold exclude exactly the
   tasks where models fail differently, e.g. decentralized triage (local success
   0.40 but a +288 local/global gap) and twin-line assignment (oracle 441,
   greedy 419, Q 217/0.00). A benchmark should report those failures, not hide
   them. Separate **task validity** from **baseline quality**.
10. **Other high-value fixes:** episode-level cluster bootstrap instead of
    row-level bootstrap; more test episodes/seeds and a private holdout; a
    layout split; fair per-family tuning budgets; normalized regret; public
    baseline code or removal of unreproducible claims; a single status source of
    truth; and a coverage map that links every cell to a task/experiment.

The one-sentence conclusion:

> FABLINE does not need more content as much as it needs **publication of the
> positive backlog, public model-family baselines, and one or two mechanics
> that add real sequential, relational, and uncertainty structure**.

## 1. Audit: what the map claims vs. what is published

### 1.1 The frozen benchmark, by kind

`factory-v0.3` is 12 headline tasks on 159 core episodes:

| Kind | Tasks | Count |
|---|---|---:|
| Offline regression | throughput-vector, throughput-grid, throughput-entities, causal-removal | 4 |
| Self-supervised | masked-grid, control-dynamics | 2 |
| Classification | bottleneck | 1 |
| Control | expand-control, order-control | 2 |
| Planning | planning-triage, order-planning | 2 |
| Calibration | fault-calibration | 1 |

That is a reasonable small benchmark, but it is not a broad coverage
instrument. The missing categories are the story:

- no multi-agent task;
- no partial-observability control task (masked-grid is reconstruction);
- no risk-sensitive control task (the reliability contract is not frozen);
- no relational-graph headline task (throughput-entities is regression with a
  feature-engineering baseline);
- no temporal sequence task (control-dynamics is one-step);
- no OOD/layout split (the shift split is one scenario);
- no offline RL (BC is a negative diagnostic on order control);
- no generative task;
- no continual/transfer task (view arrival is a contract only);
- no efficiency task (the efficiency table is descriptive).

### 1.2 Map claims and their actual status

| Map claim | What is public | Audit |
|---|---|---|
| "Representative families added in P0/P1: CNN, end-to-end GNN/MPNN, Transformer, GRU/RNN" | Experiment summaries 0025-0027 cite `experiments/architecture_baselines/...`, `experiments/grid_vision/...`, `experiments/graph_baselines/...`. Those paths are not in the public tree. The public `harness` has no CNN/GRU/Transformer/MPNN code. | **Doc-only/private evidence; not reproducible; not in the benchmark.** |
| "Current baselines include `graph_mp` message-passing features" | `harness/graph_models.py` implements two-hop normalized pooling plus GBDT. | True, but it is **not a learned GNN**; it is fixed feature engineering. |
| "Spatial: partial; masked-grid, grid next-state; small fixed layouts" | `throughput-grid` and `masked-grid` use flattened linear/GBDT/MLP. The CNN result is debug-only. | **Task is spatial in shape; the benchmark does not test a spatial model.** |
| "Relational: partial; `graph_mp` and end-to-end MPNN on debug tasks; no frozen graph benchmark" | `throughput-entities` uses `graph_mp`; MPNN is debug-only/private. | Accurate in the small print, but the headline table reads as if relational coverage exists. **No frozen graph task.** |
| "Temporal / sequence: partial; next-state and control-dynamics; short horizons" | `control-dynamics` is one-step; masked-window GRU/Transformer is debug-only/private. | **No frozen sequence model or multi-step task.** |
| "Control / RL: partial; small discrete tasks; deep RL negative at 10k (0092)" | `expand-control` is a fixed six-tile puzzle with scripted/BC/Q at 1.00; `order-control` is two actions; PPO is negative at 10k. | **Control is broad but shallow; no task gives a deep policy room.** |
| "Offline / imitation: partial; scripted demos + BC; BC near random on orders; no offline RL" | BC only, negative; human recording exists but no benchmark. | Accurate; the gap is real. |
| "Planning / world models: partial; true-simulator triage/order planning; learned transition models negative" | True CEM/random shooting/oracle; ridge transition/ensemble/two-step negative. | **Planning exists only with the true simulator; no learned world-model success.** |
| "Causal / counterfactual: partial; bottleneck labels; no intervention benchmark" | `causal-removal` is interventional prediction with GBDT/MLP; no causal model. | **One task; no discovery, effect estimation, or intervention planning.** |
| "Self-supervised: strong; next-state, masked-grid, control-dynamics" | next-state is saturated; masked-grid is one fixed patch; control-dynamics is linear-solved. | **Thin, not strong.** |
| "Robustness / OOD: partial; scenario splits; stochastic power" | One `shift_gear` scenario; no layout split, noise, delay, adversarial, or composition. | **Thin.** |
| "Uncertainty / calibration: partial; calibration metrics for stochastic power; maintenance forecasts uncalibrated" | fault-calibration is frozen; power/maintenance calibration are debug/mixed; reliability contract is not frozen. | **One task; no risk-sensitive control in the benchmark.** |
| "Efficiency: partial; cost experiments; not in the public benchmark" | Efficiency table is descriptive. | Accurate; not a benchmark family. |
| "Multi-agent: partial; centralized two-crew assignment and recall/replanning (debug); no per-agent policies or communication" | Crew tasks are macro-action/one-shot; `step` often runs the whole job to completion. | **No frozen task; no sequential per-agent policy; no communication benchmark.** |
| "Generative: absent; no layout/recipe generation task" | Feasibility audit negative: 7 line sequences, diversity 0.080. | Accurate; content too constrained. |

### 1.3 The map's matrix is not evidence-linked

The model × benchmark matrix uses `●`, `◐`, `○`, `×` but does not distinguish:

- a frozen benchmark task from a debug task;
- a task that exists from a model family that was actually run;
- a public, reproducible result from a private experiment;
- calibration from general uncertainty quantification;
- "task family" from "model family tested on it".

This is why the matrix can show `CNN Spatial ●` while the frozen spatial tasks
have no CNN baseline, and `Causal model Causal ◐` while the causal task uses
GBDT on target features. The matrix is a design sketch, not a coverage audit.

**Recommendation:** add four evidence states to every cell:

- `F` — frozen benchmark task and baseline result;
- `D` — debug/diagnostic task or baseline, public code;
- `P` — private/doc-only experiment, not reproducible from the public tree;
- `A` — absent.

Then add a "saturated" flag (`S`). A cell with only `P` evidence should not be
counted as coverage.

### 1.4 Missing matrix columns

The current matrix has no column for:

- **partial observability / POMDP** (mentioned in the text, absent from the
  matrix);
- **continual / transfer / retention** (the view-arrival contract exists);
- **efficiency / sample efficiency** (only a separate table);
- **multi-objective / constrained control** (risk is folded into uncertainty);
- **language / instruction** (text is documented but not implemented);
- **OR / scheduling** (most control tasks are scheduling problems);
- **quality / yield**;
- **inventory / depletion**;
- **human-in-the-loop / imitation** (BC is folded into offline RL).

### 1.5 Status and documentation inconsistencies

These are small, but they undermine a public benchmark:

| Issue | Where | Fix |
|---|---|---|
| `factory-v0.3` is called "candidate" in code/report text but "frozen" in cards/spec | `harness/factory_v03.py` writes `status: "candidate"` and its report says "candidate; freeze only after..." | Single status source; update the writer. |
| `factory-v0.3/spec.md` says "The benchmark is not frozen" in Purpose, then "Status: frozen" | `benchmarks/factory-v0.3/spec.md` | Remove the stale sentence. |
| Order task cards say "not in any frozen benchmark" but v0.3 includes them | `docs/tasks/order-control.md`, `order-planning.md` | Update status to `factory-v0.3`. |
| `docs/benchmark.md` says current release is v0.3 but gives the v0.2 command and an outdated task list | `docs/benchmark.md` | Update command and task IDs. |
| `coverage-map.md` says "P0 coverage is complete" while the P0 risk contract is not frozen | `coverage-map.md` | Say "P0 roadmap is complete" and list publication gaps. |
| The map references 0023 and 0073, which have no experiment directory; the numbering also has gaps at 0064, 0065, 0068, 0069, and 0080 | `coverage-map.md`; `docs/experiments/` | Add records or mark them private/removed. |
| Architecture baseline summaries cite non-public `experiments/...` code | 0025/0026/0027 | Publish code or mark as private; do not count as public coverage. |
| Task cards and benchmark cards use different task-name styles | `factory.*.v1` vs `throughput-vector` | Add a registry mapping task ID to short name. |

These are fixable in a documentation pass and should be part of any coverage
release.

## 2. Benchmark-family gaps

### 2.1 A coverage-confidence audit

Define coverage confidence as:

- **Strong** — at least two frozen tasks, non-saturated, with at least two model
  families actually evaluated in the frozen benchmark.
- **Partial** — one frozen task, or a debug family with a clear, public result.
- **Thin** — only a debug task or a saturated frozen task.
- **Absent** — no task.

Using that standard, the audited map is:

| Benchmark family | Map label | Audited label | Why |
|---|---|---|---|
| Supervised tabular | strong | **Strong but saturated** | Many tasks; throughput-vector, bottleneck, fault-calibration near ceiling. |
| Spatial | partial | **Thin** | Two frozen tasks; fixed small layouts; no CNN/UNet in benchmark. |
| Relational / graph | partial | **Thin** | One regression with `graph_mp`; no end-to-end GNN; no frozen graph task. |
| Temporal / sequence | partial | **Thin** | One-step dynamics; no sequence model in benchmark. |
| Event detection | partial | **Partial** | Fault calibration frozen; fault onset debug. |
| Control / RL | partial | **Thin** | Two small tasks; expand-control saturated; no deep-RL success. |
| Offline / imitation | partial | **Thin** | BC only, negative; no offline RL. |
| Planning / world models | partial | **Partial** | Two true-simulator tasks; learned world models negative. |
| Causal / counterfactual | partial | **Thin** | One removal-prediction task; no causal model. |
| Self-supervised | strong | **Thin** | One fixed-patch reconstruction; one linear-solved one-step task; next-state saturated. |
| Robustness / OOD | partial | **Thin** | One scenario shift; no layout/noise/delay/adversarial. |
| Compositional generalization | partial (scenario proxy) | **Thin** | One held-out combination; no mechanic-composition split. |
| Uncertainty / calibration | partial | **Partial** | One calibration task; risk contract not frozen. |
| Efficiency | partial | **Thin** | Descriptive table only. |
| Multi-agent | partial | **Absent in benchmark; partial in repo** | Debug crew tasks only; one-shot centralized actions. |
| Generative | absent | **Absent** | Negative feasibility audit. |
| Continual / transfer | absent | **Absent in benchmark; contract only** | View arrival task contract. |
| Multi-objective / risk | absent | **Absent in benchmark** | Reliability contract positive but not frozen. |
| OR / scheduling | absent | **Absent** | CEM/EDF/scripted; no MILP/CP-SAT/A*/MCTS. |
| Partial observability / POMDP | not a column | **Thin/Absent** | Masked-grid is reconstruction; no POMDP control. |
| Hierarchical / long-horizon | folded into planning | **Thin** | Build planning negative (0075). |
| Quality / yield | absent | **Absent** | No mechanic. |
| Inventory / depletion | absent | **Absent** | No mechanic. |
| Market / auction | folded into P3 | **Thin** | Contract board selection only. |
| Weather / renewables | folded into P3 | **Thin** | Stochastic power only. |
| Adversarial / sabotage | folded into P3 | **Absent** | No mechanic. |
| Language / instruction | not a column | **Absent** | Text view documented but not implemented. |
| Human-in-the-loop | not a column | **Absent** | Human recording exists; no benchmark. |

### 2.2 The saturated frozen tasks

The map's own rule is "saturated tasks are controls; keep them, but do not
headline them." The frozen benchmark headlines several tasks that are at or near
ceiling:

- `throughput-vector`: linear R² 0.767, GBDT 0.649; linear is strong.
- `bottleneck`: GBDT accuracy 0.965, balanced 0.949; near ceiling.
- `expand-control`: scripted/BC success 1.00; tabular Q 0.80; saturated.
- `control-dynamics`: linear MSE 0.0085, cosine 0.961; linear-solved.
- `order-control` success: EDF/value/Q all 1.00 at the 160 threshold; success is
  not a discriminator (the card says value is the headline).
- `planning-triage`: CEM true = oracle; the learned value model is negative.
- `order-planning`: CEM = oracle on 32 plans; exact small-space, not general
  planning.

This is not a reason to remove them; they are useful controls and regression
tests. It is a reason to **label them as controls** in the benchmark card and to
add harder tasks as headlines. A benchmark whose headline tasks are all solvable
does not expose model boundaries.

### 2.3 The missing families, ranked

The following ranking is by diagnostic value per unit of cost, assuming the
project's constraints (small world, opt-in, deterministic, one mechanic per
release).

#### P0 — publish or add now, mostly no new world

1. **Risk-sensitive control.** The reliability contract (0031) is positive and
   already implemented. It tests mean/CVaR trade-offs, distributional
   preferences, and decision under uncertainty. Add it to a coverage suite with
   a fixed operating policy and a target-selection action. Model families:
   CVaR RL, distributional RL, quantile regression, conformal, risk-sensitive
   planning.
2. **Relational/graph prediction.** Wired cascade (0032) is positive; add it to
   a coverage suite. It tests graph cuts, failure propagation, and long-range
   dependencies. Model families: GNN/MPNN/GAT/GraphSAGE/GIN, graph transformer,
   `graph_mp`, vector/grid baselines.
3. **Spatial scheduling.** Crew scheduling (0041) is positive; add it. It tests
   travel time, deadlines, order choice, and budgeted service. Model families:
   OR/CP-SAT, EDF/nearest/greedy, tabular Q, GNN/Transformer, MPC.
4. **Multi-agent coordination.** Three-bridge triage (0055) passes all gates;
   two-crew coordination (0042/0044) is robust. Add one as a headline
   multi-agent task (centralized assignment is acceptable as a first step).
   Model families: centralized oracle, greedy/nearest, independent Q, MAPPO/
   QMIX, communication.
5. **Temporal credit assignment.** Preventive wire (0035) is positive; add it.
   It tests warning-to-action timing, delayed effects, and repair budgets.
   Model families: threshold/reactive, EDF, Q, POMDP/belief models.
6. **Partial observability.** Partial-throughput (0024) is positive; add it as a
   regression task with single-frame and window views. Model families: GBDT,
   GRU, Transformer, SSM, imputation/belief models.
7. **Contextual bandit.** Maintenance-threshold selection (0038) is positive;
   add it as a diagnostic. It tests representation selection and exploration.
   Model families: epsilon-greedy, UCB, Thompson sampling, LinUCB.
8. **Production scheduling.** Recipe choice (0070) or contract board (0074) is
   positive; add one. It tests queue-aware decisions and contract selection.
   Model families: scripted, tabular Q, CEM, OR, RL.

A `factory-v0.4` **coverage suite** with these eight tasks would fill risk,
relational, scheduling, multi-agent, temporal, partial-observability, bandit,
and production-control gaps without changing the world. It should be separate
from the 12-task headline so the headline stays comparable.

#### P1 — new mechanics, medium cost

9. **Assembly edge / multi-input recipe graph.** This is the leading 0.5.0
   candidate and the strongest new mechanic. It fills planning, compositional
   generalization, relational flow, causal recipe effects, and generative
   recipe space. See §4.1.
10. **Demand arrivals/cancellations.** Fills online decision, forecasting,
    calibration, risk, and non-stationarity. See §4.2.
11. **True sequential per-crew control + communication.** Fills the largest
    multi-agent gap. See §4.3.
12. **Stochastic faults, sensor noise, hidden state.** Fills POMDP, uncertainty,
    robust control, anomaly detection, survival analysis. See §4.4.
13. **Layout/scale/topology.** Fills spatial/relational OOD and systematic
    generalization. The cheapest version is a layout split, not new entities.
    See §4.5.
14. **Inventory/depletion/shared capacity.** Fills long-horizon planning,
    resource allocation, and OR. See §4.6.
15. **Quality/defects/rework.** Fills hidden state, stochastic yield, inspection,
    and multi-objective control. See §4.7.
16. **Setup times/changeovers.** Fills scheduling/sequencing at low cost; a
    natural extension of recipe choice.
- **Compositional mechanic combinations.** Train on AB/BC, test AC/ABC; the
  most direct test of the project's composition/continual thesis. See §4.8b.

#### P2 — larger or optional

17. **Buildable power/storage.** Fills constrained network design, long-horizon
    storage dispatch, and robustness. Natural extension of wired power.
18. **Splitters/mergers/routing.** Fills flow routing, graph planning, and
    congestion; also enriches the generative grammar.
19. **Generative layout/recipe.** Only after the grammar is rich enough
    (assembly edge + splitters + multi-line).
20. **Market/auction.** Fills mechanism design, strategic multi-agent, and
    online learning.
21. **Weather/renewables.** Fills forecasting, robust control, and storage.
22. **Adversarial/sabotage.** Fills robustness, anomaly detection, and game
    theory.
23. **Hierarchical build planning.** Fills long-horizon credit assignment and
    HRL; 0075 failed because the reward was too sparse, not because the idea is
    wrong.
24. **Language/instruction.** Fills LLM/VLM grounding and planning; optional and
    outside the current project intent.
25. **Transport/fleet.** Fills VRP and MARL, but is high-cost and an explicit
    non-goal; defer.

### 2.4 Cross-cutting benchmark weaknesses

- **Statistical power.** 20 test episodes and ~370 samples are small; CIs are
  wide. Row-level bootstrap treats correlated samples as independent. Increase
  test episodes, use episode-level cluster bootstrap, and report minimum
  detectable effects.
- **Fair tuning.** The benchmark compares a default 64-unit sklearn MLP to a
  200-tree GBDT. The MLP's poor results may be a tuning artifact. Tune each
  family on validation at a declared budget, or state that the comparison is
  "default hyperparameters" and not a family verdict.
- **Private holdout.** The map mentions one; the benchmark does not implement
  one. Add a held-out seed block.
- **Layout split.** The v0.2 freeze review deferred it. It is the cheapest OOD
  upgrade and should be added to any new benchmark.
- **Normalized metrics.** Scores are not comparable across tasks. Report
  normalized regret vs oracle/random, success, and cost.
- **Failure modes.** Report per-seed failure categories (noop, missed deadline,
  wrong assignment, brownout), not just means.
- **Negative results first.** The project's own protocol says to lead with
  negatives; the benchmark cards often lead with headline positives.
- **Ablations.** New mechanics need no-mechanic controls (recipe-only vs
  assembly; known orders vs arrivals; communication vs no communication).

## 3. Model-family gaps

### 3.1 What the public benchmark actually runs

| Block | Families actually run |
|---|---|
| Core shared suite | mean, persistence, linear, GBDT, MLP; `graph_mp` features on entities |
| Control | scripted, random, tabular Q, decision-tree BC |
| Planning | scripted greedy/aware, random, random shooting, CEM (true simulator), ridge value model, oracle |
| Calibration | majority, GBDT, MLP |
| Causal | mean, linear, GBDT, MLP on target vs type-only features |
| Order control | always gear/component, EDF, value, random, tabular Q |
| Order planning | always, value plan, EDF plan, random plan, CEM, oracle |
| Diagnostics | fault prediction, power brownout, next-state, production mix, order RL (BC/PPO separately) |

The public learned families are therefore: **linear, GBDT, MLP, `graph_mp`,
tabular Q, BC, PPO, CEM, bandits, calibration, CVaR selection.** That is a
respectable tabular/decision set. It is not a deep-learning or structured-model
set.

### 3.2 Missing model families and where they should be tested

| Model family | Public evidence | Frozen benchmark? | Where to test | Priority |
|---|---|---|---|---|
| GNN / MPNN / GAT / GraphSAGE / GIN | `graph_mp` features; MPNN debug/private | No | throughput-entities, wired cascade, assembly edge | **P0** |
| Graph transformer | None | No | wired cascade, production graph | P1 |
| CNN / UNet / ViT | CNN debug/private (0026) | No | throughput-grid, masked-grid | **P0** |
| Transformer | Debug/private (0025) | No | partial throughput, order control, crew scheduling | **P0/P1** |
| RNN / GRU / LSTM / TCN | GRU debug/private (0025) | No | partial throughput, fault onset, demand | P1 |
| SSM / S4 / Mamba | None | No | long sequences, demand, sensor history | P2 |
| Deep RL (DQN/Rainbow/SAC/PPO/TD3) | PPO negative at 10k (0092) | No | order control, crew, assembly, power | P1 |
| Offline RL (CQL/IQL/AWAC/TD3+BC/DT) | BC only, negative | No | order control, crew, maintenance | P1 |
| Model-based RL (Dreamer/MuZero/MBPO/PETS) | Ridge transition/ensemble/two-step negative | No | planning-triage, assembly, crew | P1 |
| MARL (MAPPO/QMIX/MADDPG/COMA) | Centralized assignment only | No | sequential crew control | **P0/P1** |
| Communication (CommNet/TarMAC/DIAL) | None | No | decentralized triage/crew | P1 |
| Hierarchical RL (options/FeUdal) | None | No | build planning, long-horizon | P2 |
| Meta-learning (MAML/Reptile/ProtoNets) | None | No | layout/recipe shift | P1 |
| Continual learning (EWC/replay/adapters/LoRA) | View-arrival contract only | No | view arrival, new recipe, layout shift | P1 |
| Imitation (DAgger/GAIL/IRL/MaxEnt) | BC only | Order control (negative) | control, human demos | P1 |
| Causal discovery (PC/NOTEARS/LiNGAM) | None | No | causal-removal, recipe intervention | P2 |
| Causal effect (IPW/DR/IV/double ML) | GBDT on target features | causal-removal | causal-removal, demand, recipe | P1 |
| Probabilistic/Bayesian (GP/BNN/MC dropout/deep ensembles) | Calibration only | No | calibration, POMDP, demand | P1 |
| Conformal/quantile | None | No | calibration, demand, maintenance | P1 |
| Survival/point process (Cox/Weibull/Hawkes) | None | No | fault onset, maintenance | P1 |
| State-space/Kalman/particle filter | None | No | POMDP, demand, fault | P1 |
| OR (MILP/CP-SAT/A*/MCTS) | CEM/random shooting/EDF/oracle | No | crew scheduling, order planning, assembly | **P0** |
| MPC/LQR/PID | None | No | power allocation, inventory, demand | P1 |
| Queueing/fluid models | None | No | production scheduling | P2 |
| Generative (VAE/GAN/diffusion/flow/AR) | None | No | layout/recipe generation | P2 |
| Contrastive/MAE (SimCLR/BYOL/MAE) | None | No | representation transfer, masked-grid | P2 |
| Graph generation | None | No | layout generation | P2 |
| Evolutionary search (GA/SA) | CEM only | No | planning/scheduling | P2 |
| LLM/VLM agents | None | No | language/vision, planning | P3 |

### 3.3 The reproducibility issue

The map's strongest architecture claims are not reproducible from the public
tree:

- 0025 sequence baselines cite `experiments/architecture_baselines/sequence_run.py`;
- 0026 grid CNN cites `experiments/grid_vision/cnn_run.py`;
- 0027 MPNN cites `experiments/graph_baselines/gnn_run.py`.

Those paths are absent. The public package cannot rerun the CNN, GRU,
Transformer, temporal CNN, or MPNN results. This is a public-release
reproducibility gap, not just a coverage gap. Either publish the code (preferred)
or mark the results as private diagnostics and do not count them as public
coverage. The same applies to any result whose raw artifacts are ignored and
whose code is absent.

## 4. Mechanics to fill the gaps

### 4.0 Selection rules

Every proposed mechanic should satisfy the project's own rules:

1. Name the model weakness it exposes.
2. Name the benchmark family and baseline families.
3. Fix observation, action, label, split, metric, and version first.
4. Add a task card and a pre-registration.
5. Keep it opt-in; default hashes unchanged.
6. Report negative and saturated results first.
7. Do not add content volume without a diagnostic question.

The proposals below are ranked by **diagnostic value per unit of reuse and
cost**, not by fun or content.

### 4.1 Assembly edge as a multi-input recipe graph (top new mechanic)

**What changes.** The current production mix is a global two-way switch:
assembler makes gear or component. The full assembly edge is
`INGOT + COMPONENT -> GEAR`. To make it a real decision, go one step further
than the current Phase 1b sketch:

- each assembler carries a recipe assignment (gear, component, or assembly);
- component is a logistics item with its own buffer/route;
- the depot accepts gear and component; orders can request either;
- recipe switches cost setup time (optional but recommended);
- byproduct/purge can be included as a second pressure.

This creates a small directed acyclic production graph with a shared
intermediate, which is the smallest structure that exposes compositional
planning and credit assignment.

**New decisions.** Which recipe per assembler; when to switch; how much
component buffer to hold; whether to build a second assembler or route; how to
allocate ingots between gear and component; when to purge byproduct.

**Model weaknesses exposed.**

- Flattened/tabular models cannot represent the DAG or the shared intermediate.
- Myopic/EDF policies fail because component production has a delay and an
  opportunity cost.
- Value models and one-step lookahead fail because the payoff is multi-step.
- Causal models must handle recipe interventions, not just correlations.
- Generative models get a richer recipe grammar.

**Benchmark families / tasks.**

- `assembly-control` — online recipe/route control against orders.
- `assembly-planning` — choose an initial recipe assignment/line plan for a
  known order set; 4-8 bits; CEM/OR/oracle.
- `bom-forecast` — predict component starvation/gear output from state.
- `recipe-intervention` — predict the counterfactual effect of removing or
  switching a recipe.

**Baselines.** Always gear/component/assembly; EDF; value; buffer-aware;
random; tabular Q; CEM; MILP/CP-SAT; GNN/MPNN; PPO/SAC; CQL/IQL/DT.

**Gates.**

- Mechanic: opt-in; default hash unchanged; component logistics tested.
- Control: oracle ≥ best scripted + 10; best learned ≥ random + 10; success ≥
  0.60.
- Planning: oracle ≥ best scripted + 10; CEM/OR within 10 of oracle; success ≥
  0.60.
- Causal: target features R² ≥ 0.30 and ≥ type-only + 0.20.

**Reuse.** `Item.COMPONENT`, `ProductionConfig`, `RecipeConfig`,
`_advance_machine` (already supports multiple inputs), depot acceptance, order
stream, production observation. The main new work is component acceptance into
assemblers, per-entity recipe state, and tests/hash invariants.

**Cost.** Medium. **Priority: P0.** This is the strongest new mechanic and the
natural 0.5.0/0.6.0 flagship.

**Risk.** Content treadmill. Keep the recipe set to 3–4 recipes and one
intermediate; do not add a catalog. The point is the DAG and the delay, not many
items.

### 4.2 Demand arrivals, cancellations, and online order uncertainty

**What changes.** Orders are currently known at reset. Add:

- a seeded arrival schedule (orders appear over time);
- cancellations/expedites;
- demand shocks (a regime shift within an episode);
- a noisy forecast/lead-time signal that carries real skill;
- optional accept/reject and capacity reservation.

**New decisions.** Accept/reject; reserve capacity; choose recipe/production;
forecast; when to switch; how much safety buffer.

**Model weaknesses exposed.**

- Memory and forecasting: the current state is not enough; history matters.
- Calibration: fulfillment risk must be calibrated, not just ranked.
- Online decision under uncertainty: EDF/value with known orders is not enough.
- Risk: late/unfilled penalties create asymmetric costs.
- Non-stationarity: a regime shift breaks stationary policies.

**Benchmark families / tasks.**

- `demand-forecast` — predict arrivals/cancellations/late risk.
- `order-arrival-control` — online accept/produce/switch.
- `demand-calibration` — Brier/NLL/ECE of fulfillment risk, with a skill gate.
- `capacity-allocation` — allocate shared capacity across order classes.

**Baselines.** Mean/GBDT; GRU/Transformer/SSM; DeepAR/TFT-style; conformal;
EDF/value; forecast-then-optimize; MPC; tabular Q; PPO; CQL/IQL/DT; bandits.

**Gates.**

- Forecast skill: AUC/R² over base rate on held-out episodes.
- Calibration: ECE ≤ 0.05 only if skill passes.
- Control: online policy ≥ best scripted + 10; success ≥ 0.60.
- No leakage: future arrivals not in observation.

**Reuse.** `OrderConfig`, `OrderControlEnv`, `OrderObservation`; add an arrival
schedule and history window. Low-medium cost.

**Priority: P0/P1.** The 0.4.0 review correctly says this is only worth doing if
the observation carries skill. Design the signal to carry skill (lead-time
jitter correlated with supplier state, early cancellation flags, queue backlog)
and gate on forecast skill before calibration or control claims.

### 4.3 True sequential per-crew control and communication

**What changes.** The current crew tasks are macro-action assignments. `step`
often runs a job to completion and returns the final score. There is no
per-agent sequential policy, no movement, and no communication action. Add:

- crews with positions; move one cell per decision (or a small macro move);
- actions: move N/E/S/W, wait, repair, report, maybe recharge;
- local observations with a radius; occlusion/fog rather than binary distance;
- communication budget, delay, and noise;
- dynamic faults, recalls, and agent failure;
- per-crew rewards or a team reward with credit assignment.

**New decisions.** Path planning; task assignment; when to communicate; what to
report; when to abandon a job; handoff/replacement.

**Model weaknesses exposed.**

- Decentralized POMDP: local views and partial information.
- Credit assignment: team reward, individual actions.
- Communication: bandwidth, delay, noise, information value.
- Coordination: collision/duplication avoidance, role specialization.
- Robustness: agent failure, recall, replanning.

**Benchmark families / tasks.**

- `crew-sequential` — cooperative repair with 2–3 crews; per-agent actions.
- `crew-communication` — limited messages; measure communication gain.
- `agent-failure` — one crew fails; handoff/replacement.

**Baselines.** Centralized oracle; greedy/nearest/EDF; independent Q; MAPPO;
QMIX/VDN; MADDPG; COMA; CommNet/TarMAC/DIAL; OR/CP-SAT for the centralized
assignment.

**Gates.**

- Coordination gain ≥ +10 over single crew.
- Communication gain ≥ +10 over no communication.
- Oracle gap ≥ +10.
- Best learned success ≥ 0.60; cost reported.
- If no learned policy succeeds, publish as a challenge task, not a failure of
  the task.

**Reuse.** `crew_schedule`, `multi_crew`, `crew_visibility`,
`crew_decentralized`; but a new sequential environment is needed because the
current `step` executes whole jobs. Medium-high cost.

**Priority: P0/P1.** This is the largest multi-agent gap and the natural
follow-up to the P2/P3 crew work. Do it after the coverage release, not as a
quick add-on.

### 4.4 Stochastic faults, sensor noise, and hidden state

**What changes.** Faults are currently deterministic wear. Add:

- stochastic onset (hazard depends on wear, load, maintenance);
- sensor noise, drift, false positives/negatives;
- hidden wear or hidden fault state;
- correlated failures (shared power/load);
- optional inspection actions.

**New decisions.** Inspect vs repair vs continue; belief update; sensor
placement; when to trust a warning.

**Model weaknesses exposed.**

- POMDP/belief state; memory.
- Calibration and uncertainty quantification.
- Robust control under false alarms.
- Anomaly detection and survival analysis.
- Active perception (inspection).

**Benchmark families / tasks.**

- `fault-detection-noise` — detection/calibration under noise.
- `pomdp-maintenance` — hidden wear; inspect/repair/continue.
- `root-cause` — identify the source of a production drop.

**Baselines.** GBDT; HMM; Kalman/particle filter; Cox/Weibull; conformal;
threshold/reactive; belief-state RL; POMDP solver.

**Gates.** Detection skill over base rate; ECE ≤ 0.05; control gain over
threshold; success.

**Reuse.** `FaultConfig`, sensors, `partial.py`; low-medium cost.
**Priority: P0/P1.** This is the cheapest way to add real partial observability
and uncertainty to control.

### 4.5 Layout, scale, and topology

**What changes.** The benchmark uses small fixed layouts (16×8, 32×16, 48×24)
and one scenario shift. Add:

- larger maps and random obstacles/ore;
- random line offsets/orientations;
- multi-line/shared-resource layouts;
- a layout split: train on some generator families, test on unseen layouts;
- optional splitters/mergers and rotations.

**New decisions.** Build/route under layout uncertainty; line balancing;
generalize a policy to a new topology.

**Model weaknesses exposed.**

- CNN receptive field and spatial generalization.
- GNN/relational generalization.
- Systematic/OOD generalization; meta-learning.
- Planning under layout uncertainty.

**Benchmark families / tasks.**

- `layout-shift` — throughput/bottleneck on unseen layouts.
- `scale-transfer` — train small, test large.
- `route-control` — splitters/mergers; build a route.

**Baselines.** CNN/UNet/ViT; GNN/GAT; Transformer; MLP; meta-learning;
domain generalization.

**Gates.** In-distribution vs OOD gap; model ranking; success; no leakage of
layout seed.

**Reuse.** Generator; low cost for the split, medium for splitters/mergers.
**Priority: P0 for the split; P2 for splitters/mergers.** A layout split is the
cheapest OOD upgrade and should be in the next benchmark.

### 4.6 Inventory, depletion, and shared capacity

**What changes.**

- finite ore patches that deplete;
- storage/warehouse buffers with holding costs;
- multiple lines sharing ore, power, or crews;
- expansion decisions (new miner/patch/line);
- replenishment/spare parts.

**New decisions.** Allocate scarce inputs; store vs sell; expand vs optimize;
replenish; schedule shared capacity.

**Model weaknesses exposed.**

- Long-horizon planning and credit assignment.
- Resource allocation and combinatorial optimization.
- OR/MILP/MPC.
- Multi-objective trade-offs (throughput vs cost vs depletion).

**Benchmark families / tasks.**

- `resource-allocation` — allocate ore/power across lines.
- `expansion-planning` — when/where to expand.
- `inventory-control` — safety stock/replenishment under demand uncertainty.

**Baselines.** MILP/CP-SAT; MPC; RL; heuristics; queueing/fluid models.

**Gates.** Oracle gap; success; cost; feasibility.

**Reuse.** World core/generator; medium cost.
**Priority: P1.** Fills the 0.4.0 review's "multi-item breadth" gap and adds a
genuine long-horizon planning axis.

### 4.7 Quality, defects, and rework

**What changes.**

- craft completion can yield a defective item;
- defect probability depends on wear, speed, power stability, and recipe;
- inspection reveals defects; rework/scrap decisions;
- quality-speed trade-off.

**New decisions.** Inspect/rework/scrap; choose speed vs quality; schedule
maintenance to protect yield.

**Model weaknesses exposed.**

- Hidden state and stochastic yield.
- Calibration of defect risk.
- POMDP/active inspection.
- Multi-objective control (throughput vs quality vs cost).

**Benchmark families / tasks.**

- `defect-prediction` — calibrated defect risk.
- `inspection-control` — inspect/rework/scrap.
- `quality-aware-scheduling` — speed/quality trade.

**Baselines.** Calibration; Bayesian; POMDP; constrained RL; OR.

**Gates.** Skill/calibration; control gain; quality/throughput trade.

**Reuse.** World core/faults; medium cost.
**Priority: P1.** A genuinely new axis; the 0.4.0 RFC considered it as a
fallback, and it is stronger than another calibration view.

### 4.8 Setup times and changeovers

**What changes.** Recipe switches take setup time and may incur yield loss;
sequence-dependent changeovers.

**New decisions.** Batch/sequence/switch; lot sizing; order sequencing.

**Model weaknesses exposed.** Scheduling/sequencing; combinatorial optimization;
credit assignment; attention over order sets.

**Tasks.** `changeover-scheduling`, `lot-sizing`, `order-sequencing`.

**Baselines.** OR/CP-SAT; EDF; value; RL; attention.

**Reuse.** `RecipeConfig`, `ProductionConfig`; low cost. **Priority: P1.**

### 4.8b Compositional mechanic combinations

**What changes.** The current compositional split is a scenario proxy
(`extra_gear`); it does not combine mechanics. Add a split that trains on
mechanic pairs AB and BC and tests AC/ABC, e.g.:

- faults + orders;
- power + orders;
- crews + faults;
- assembly + power + orders;
- layout shift + recipe shift.

**New decisions.** Compose learned sub-policies; retain old mechanics; adapt to
a new combination.

**Model weaknesses exposed.** Systematic generalization; modularity; continual
learning; credit assignment across mechanisms; causal abstraction.

**Tasks.** `compositional-throughput`, `compositional-control`,
`compositional-planning`.

**Baselines.** Joint retrain; fine-tune; modular networks; GNN; meta-learning;
EWC/replay/adapters.

**Gates.** OOD gap; new-mechanic acquisition; old-mechanic retention; cost.

**Reuse.** Existing mechanics and generator; low-medium cost.
**Priority: P1.** This is the most direct test of the project's stated
composition/continual thesis.

### 4.9 Human demonstrations and preferences

**What changes.** Record human play in the viewer; build a demonstration dataset
with diverse skill levels; collect pairwise preferences.

**New decisions.** Imitate; prefer; learn a reward; collaborate.

**Model weaknesses exposed.** Offline RL; imitation; distribution shift; reward
learning; human-AI collaboration.

**Tasks.** `imitation`, `preference-learning`, `human-ai-collaboration`.

**Baselines.** BC/DAgger/GAIL/IRL; preference transformer; CQL/IQL/DT.

**Reuse.** `record/human.py`, viewer/play; low-medium cost. **Priority: P1.**

### 4.10 Buildable power and storage

**What changes.** Generators, wires, and batteries become buildable; storage
charge/discharge; intermittent supply.

**New decisions.** Network design; storage dispatch; redundancy; reserve.

**Model weaknesses exposed.** Constrained network design; long-horizon
planning; uncertainty; graph optimization.

**Tasks.** `power-network-design`, `storage-dispatch`, `cascade-prevention`.

**Baselines.** MILP; GNN; MPC; robust RL.

**Reuse.** `power.py`, `wire.py`; medium-high cost. **Priority: P1/P2.**

### 4.11 Splitters, mergers, and routing

**What changes.** Add splitter/merger entities and route choice; optionally
rotations and underground belts.

**New decisions.** Route/merge/balance; build order; congestion management.

**Model weaknesses exposed.** Flow routing; graph planning; spatial reasoning;
OR.

**Tasks.** `route-control`, `line-balancing`, `congestion-control`.

**Baselines.** A*/MCTS; GNN; RL; OR.

**Reuse.** World/actions; medium cost. **Priority: P2.** This also enriches the
generative grammar.

### 4.12 Generative layout/recipe

**What changes.** Only after the grammar is rich enough (assembly edge,
splitters, multi-line, power), define a conditional generation task.

**New decisions.** Generate valid structures/recipes under constraints; optimize
a downstream objective.

**Model weaknesses exposed.** Distribution matching; validity/diversity;
constraint satisfaction; inverse design.

**Tasks.** `layout-generation`, `recipe-generation`, `conditional-generation`.

**Baselines.** Random grammar; VAE; GAN; diffusion; flow; autoregressive; RL.

**Gates.** ≥20 unique structures; diversity ≥0.25; validity ≥0.9; downstream
gap.

**Reuse.** Generator/production; medium-high cost. **Priority: P2.** Do not
revisit on seven line sequences.

### 4.13 Market, weather, adversarial, language, transport

These are lower priority but worth recording:

- **Market/auction.** Multiple buyers, prices, bidding, contract clearing.
  Exposes mechanism design, strategic agents, online learning. Reuse contract
  board/orders; medium cost; P2.
- **Weather/renewables.** Exogenous weather affects supply/demand; storage.
  Exposes forecasting, robust control, non-stationarity. Reuse stochastic
  power; medium cost; P2.
- **Adversarial/sabotage.** Attacks on sensors/wires/belts; detect/recover.
  Exposes robustness, anomaly detection, game theory. Reuse faults/wires;
  medium cost; P2.
- **Language/instruction.** Text adapter + templated instructions; LLM/VLM
  planning. Exposes grounding, compositional generalization, tool use. Low cost
  but outside current scope; P3.
- **Transport/fleet.** Vehicles, routing, loading. Exposes VRP/MARL; high cost
  and an explicit non-goal; defer.

### 4.14 Mechanic × model-family map

| Mechanic | Primary model families it would expose |
|---|---|
| Assembly edge / multi-input recipe | GNN/graph transformer; MILP/CP-SAT; world models; hierarchical RL; causal intervention |
| Demand arrivals/uncertainty | RNN/Transformer/SSM; DeepAR/TFT; conformal; bandits; MPC; offline RL; risk-sensitive RL |
| Sequential crew control/communication | MAPPO/QMIX/MADDPG/COMA; CommNet/TarMAC; POMDP/belief RL; credit assignment |
| Stochastic faults/noise | HMM/Kalman/particle filter; survival; conformal; robust RL; POMDP |
| Layout/scale/topology | CNN/UNet/ViT; GNN/GAT; meta-learning; domain generalization |
| Inventory/depletion | MILP/CP-SAT; MPC; RL; queueing/fluid |
| Quality/defects | calibration; Bayesian; POMDP; constrained RL |
| Setup times | OR/scheduling; attention; RL |
| Human demos/preferences | BC/DAgger/GAIL/IRL; preference transformer; offline RL |
| Buildable power/storage | MILP; GNN; MPC; robust optimization |
| Splitters/mergers/routing | A*/MCTS; GNN; RL; OR |
| Generative grammar | VAE/GAN/diffusion/flow/AR; RL for generation |
| Market/auction | game theory; bandits; MARL |
| Weather/renewables | time series; MPC; robust RL |
| Adversarial/sabotage | robust RL; anomaly detection; game theory |
| Hierarchical build planning | HRL/options; MCTS; LLM planners |
| Language/instruction | LLM/VLM; tool use |

## 5. Promotion analysis: failed, mixed, and unpromoted tasks

### 5.1 A better gate philosophy

The current freeze gates mix two questions:

- **Is the task valid?** Deterministic label/reward, disjoint splits, a real
  oracle-scripted gap, a non-saturated signal.
- **Is the current learned baseline strong?** Does it beat random by 10? Does it
  reach 0.60 success?

These are different. A task can be valid and hard while the current best learned
baseline is weak. Excluding it because the baseline is weak selects for easy
tasks and hides the most diagnostic failures.

The map already says: "A task that every reasonable model solves is a control,
not a headline benchmark." The converse is also true: a task that no current
model solves can be a **challenge benchmark**, not a failed task. The project's
own principle "negative results count" supports publishing it.

**Recommendation:** add a **challenge tier** to the benchmark:

- `headline`: stable, comparable, at least one strong baseline.
- `challenge`: valid task, oracle/scripted baselines, best learned baseline
  reported as negative; explicitly not part of the headline score.
- `diagnostic`: a mechanic/baseline probe, not a benchmark task.
- `control`: saturated task kept for regression and sanity checks.

A task enters `challenge` if it has a real oracle-scripted or information gap
and a deterministic contract. It does **not** need a learned policy to succeed.
This lets FABLINE publish tasks like decentralized triage and twin-line
assignment without pretending they are solved, and without lowering gates.

### 5.2 Promotion ledger

A "promote" row means the task is a good benchmark candidate. It does not mean
the public repo can run it today: 0031, 0032, and 0024 have public cards/world
support but their experiment harness is not in the public tree. The public
reliability-contract harness is now started; the other two need W1 work.

| Task / experiment | Gate result | Task valid? | Baseline issue? | Recommendation |
|---|---|---|---|---|
| Reliability contract (0031) | all pass; CVaR +17.05 | Yes | No | **Promote to coverage suite** |
| Wired cascade (0032) | H1/H3/H4 pass | Yes | `graph_mp` strong; no GNN | **Promote; add GNN** |
| Wire repair (0033) | all pass | Yes | Q strong | **Promote; timed variant diagnostic** |
| Preventive wire (0035) | all pass | Yes | No | **Promote** |
| Maintenance threshold (0038) | all pass | Yes | Deterministic/easy | **Promote as bandit diagnostic** |
| Crew schedule (0041) | all pass | Yes | Q 97.4% EDF | **Promote** |
| Two-crew coordination (0042/0044) | all pass; robust | Yes | Shallow; nearest near ceiling | **Promote** |
| Twin-line assignment (0046) | H1-H3 pass; H4 Q fails | Yes | Q 217/0.00; oracle 441 | **Challenge tier**; add stronger baseline |
| Crew triage (0055) | all pass | Yes | Greedy 378 vs oracle 456 | **Promote** |
| Recipe choice (0070) | all pass | Yes | Scripted gap | **Promote or production diagnostic** |
| Byproduct (0072) | all pass | Yes | Narrow | **Diagnostic** |
| Contract board (0074) | all pass | Yes | Small board | **Promote or diagnostic** |
| Partial throughput (0024) | positive | Yes | Two-value label; small | **Promote as regression** |
| Power allocation (0016/0020) | positive | Yes | Easy for Q | **Control/floor diagnostic** |
| Fault recovery (0009) | positive | Yes | Repair-now optimal | **Control/floor diagnostic** |
| Fault + power (task card only; no experiment record) | positive | Yes | Easy | **Control/floor diagnostic** |
| Fault onset (0013) | positive | Yes | Small acoustic signal | **Event-detection diagnostic** |
| Maintenance calibration (0084) | H2 ECE fails on full view; diagnostics passes | Mixed | GBDT miscalibrated | **Diagnostic**; add calibration method, not a new view |
| Decentralized triage (0077/0081/0082) | H2 local success 0.40; Q 0.47 | Yes | Local policies weak; +288 gap | **Challenge tier**; new communication mechanic |
| Recall + twin-line (0047) | H3 +9 vs +10; H4 Q fails | Mostly | Near-miss | **Redesign with repeated failure/second recall**; then challenge/headline |
| Replacement handoff (0060) | H2 scripted −38; oracle +20 | Yes | Scripted handoff weak | **Redesign with pair-aware/learned handoff**; challenge |
| Three-crew recall (0063) | H3 +4; shallow | Yes | Scripted ceiling | **Diagnostic**; add four bridges/multiple recalls |
| Production mix (0089) | H3 schedule gap fails | Precondition | No schedule decision | **Keep diagnostic**; assembly edge |
| Transition planning (0083/0085/0086) | planning gates fail | Task already frozen | Linear model ceiling | **New nonlinear world-model pre-reg**; don't promote model |
| Generative audit (0087) | diversity/validity fail | Content not ready | No model trained | **Enrich grammar**; then generative |
| Deep/offline RL (0092) | BC +6.6; PPO −74.3 | Task already frozen | Budget/task too small | **New budget + harder task**; don't tune 0092 |
| Build planning (0075) | sparse; CEM 0 | Task design | Reward too sparse | **Redesign with dense subgoals/curriculum** |
| Single deadline contract (0073) | negative | Easy/impossible | No decision | **Do not promote**; use 0074 |
| Timed repair (0034) | H3 order gate fails | Timing effect present | Order not robust | **Diagnostic**; use 0033/0035 |
| Risk-score noise (0036) | negative pilot | No | — | **Retire** |
| Contextual threshold (0039) | negative pilot | No | — | **Retire** |
| Partial per-crew view (0043) | binary radius | No | — | **Retire** |
| Margin-aware Q (0049) | negative | No | — | **Retire** |
| Visibility on twin-line (0051) | binary | No | — | **Retire** |
| One-shot multi-orphan (0053) | negative | No | — | **Retire** |
| One-report rule (0058) | negative | No | — | **Retire** |
| Spread triage (0059) | greedy=oracle | No | — | **Retire** |
| Pair policy (0061) | negative | No | — | **Retire** |
| Asymmetric costs (0066) | negative | No | — | **Retire** |
| Random topology (0067) | negative | No | — | **Retire** |
| Compact decentralized Q (0081) | negative | Task valid | Representation not binding | **Do not tune**; new mechanic |
| CTDE (0082) | negative | Task valid | Credit assignment | **Retire local-policy line** |
| Transition ensemble/two-step (0085/0086) | negative | Task valid | Linear ceiling | **New nonlinear model** |

### 5.3 Detailed near-miss redesigns

#### 0047 — recall/replanning on twin lines

- **Why it failed:** recovery gain +240, but oracle-greedy +9 misses the +10
  gate and Q fails. The combined task is easier for scripted policies than the
  assignment-only task.
- **Is it improvable?** Yes, but not by re-running the same seeds. The summary
  itself suggests the fix: multiple orphans, repeated failure, or a deadline
  that prevents free recovery.
- **Redesign:** two sequential recalls (B then C), or a second failure during the
  recovery pair, or a tighter deadline that makes the survivor choose between
  two orphans. Pre-register the new task; do not change the old gate.
- **Promotion:** challenge tier if the layout gap remains small; headline if
  the redesign restores a ≥10 oracle-scripted gap and a learned policy can at
  least beat random.

#### 0048/0050 — compact Q and ensemble

- **Why they failed:** the task (0046) is valid; the Q baseline misses 0.60
  success. The compact state is a large representation win (422 vs 233; 95.5%
  of oracle) but one aliased seed remains.
- **Is it improvable?** The task is; the Q variant is near its ceiling. Do not
  tune another compact state (0049 already failed). A GNN/Transformer policy, an
  imitation policy from the oracle, or a CP-SAT assignment baseline is the right
  next comparison.
- **Promotion:** publish 0046 as a **challenge** task with oracle 441, greedy
  419, Q 217; report compact Q as a diagnostic. Do not publish 0048/0050 as
  separate tasks.

#### 0060 — replacement handoff

- **Why it failed:** replacement oracle +20 over no replacement, but best
  scripted replacement is −38. The handoff opportunity is real; the scripted
  rules do not capture it.
- **Is it improvable?** Yes. A pair-aware rule using remaining time, bridge
  value, distance, and current job progress; or a learned policy; or a delayed
  replacement arrival/new base. Pre-register a new handoff task.
- **Promotion:** challenge tier now; headline after a scripted or learned
  handoff beats no-replacement +10.

#### 0063 — three-crew recall

- **Why it failed:** H3 shallow (+4). The third crew absorbs the recall, and
  three greedy is within 4 of oracle.
- **Is it improvable?** Only with a harder task: four bridges, two recalls, or
  travel/deadline pressure. As-is it is a diagnostic/control.
- **Promotion:** do not headline; use as a multi-agent control/diagnostic.

#### 0077/0081/0082 — decentralized triage

- **Why it failed:** local success 0.40; private Q 0.47; compact Q and CTDE do
  not close the gate. But the local/global gap is +288, and private Q beats
  local greedy by +122.
- **Is it improvable?** The task is valid and diagnostic. The missing piece is a
  communication action and a sequential per-agent policy, not another compact
  state. CTDE collapsed; do not tune it.
- **Promotion:** **challenge tier now** with global oracle, local scripted, and
  private Q; this is exactly the kind of task a benchmark should expose. Add a
  communication mechanic later; then it can become a headline.

#### 0084 — maintenance calibration

- **Why it failed:** the registered full maintenance view is miscalibrated for
  GBDT (ECE 0.0929); the diagnostics view passes (0.0054) but was not the
  primary view.
- **Is it improvable?** Yes, but not by dropping the maintenance features
  post-hoc. Add a calibration method (temperature scaling, isotonic, Dirichlet)
  or a probabilistic model (GP/BNN) as a baseline. The diagnostics view can be
  a diagnostic.
- **Promotion:** diagnostic; not a headline calibration task until a method
  passes on the registered full view.

#### 0083/0085/0086 — transition/world-model planning

- **Why they failed:** linear transition models fit one-step but compound in
  rollout; the ensemble and two-step models improve but remain far below true
  CEM.
- **Is it improvable?** Yes, with a **nonlinear** world model (small MLP/
  Transformer/RNN), multi-step training, uncertainty, and a terminal-score head.
  That is a new pre-registration, not a tune of the ridge model.
- **Promotion:** the planning task is already in v0.2; do not promote the
  negative models. Add a world-model baseline track when a nonlinear model is
  ready.

#### 0087 — generative feasibility

- **Why it failed:** current content has 7 unique line sequences and diversity
  0.080. No model can learn a meaningful distribution.
- **Is it improvable?** Only after a richer grammar: assembly edge, splitters/
  mergers, multi-line, power/obstacles. Then rerun the feasibility audit.
- **Promotion:** do not promote until the audit passes.

#### 0092 — deep/offline RL

- **Why it failed:** BC +6.6, PPO −74.3 at 10k steps on a two-action task. The
  task is small and the budget is tiny.
- **Is it improvable?** Yes, but not by tuning 0092. Use a harder sequential task
  (crew/assembly), a larger declared budget, and proper offline datasets. Add
  CQL/IQL/DT/AWAC, not just BC/PPO.
- **Promotion:** task already in v0.3; keep the negative as a baseline result.
  New budget/pre-reg on a new task.

#### 0075 — build planning

- **Why it failed:** sparse reward; CEM 0 vs scripted 140.
- **Is it improvable?** Yes, with dense subgoals/curriculum, a target-throughput
  reward, or a macro-action hierarchy. This is a real long-horizon planning gap.
- **Promotion:** new task after redesign; high potential.

### 5.4 A proposed `factory-v0.4` coverage slate (package 0.5.0)

Do not edit `factory-v0.3`. Create a new, separate coverage suite with six to
eight tasks. The benchmark version can be `factory-v0.4` while the package
release is `0.5.0`; keep the two version lines explicit in the card. Suggested
slate:

| Task | Source | Family | Why |
|---|---|---|---|
| reliability-contract | 0031 | risk/uncertainty | Mean/CVaR trade, risk-sensitive selection |
| wired-cascade | 0032 | relational/graph | Graph cut, failure propagation |
| crew-schedule | 0041 | spatial scheduling | Travel, deadlines, budget |
| crew-triage | 0055 | multi-agent | Coordination, oracle gap |
| preventive-wire | 0035 | temporal credit | Warning-to-action timing |
| partial-throughput | 0024 | partial observability | Missing features, history |
| recipe-choice or contract-board | 0070/0074 | production control | Queue/contract decision |
| maintenance-threshold | 0038 | bandit/context | Representation/exploration |

Add to the suite:

- **Public baseline code** for CNN/UNet, GNN/MPNN, Transformer, GRU, and OR
  (CP-SAT or a simple exhaustive/ILP baseline), even if optional extras.
- **A layout split** on the existing grid/bottleneck tasks.
- **Episode-level cluster bootstrap** and a **private holdout**.
- **A challenge tier** for 0046, 0060, 0077, and 0084.
- **A task registry** mapping IDs, cards, runners, and expected summaries.

This is the highest-ROI release: no new world, immediate coverage, and it
exposes the current model gaps honestly. It is a **curation/publication**
release, not a new mechanic, so it does not violate the "one mechanic per
milestone" rule; the mechanic release can follow.

### 5.5 A proposed next mechanic slate (package 0.6.0, benchmark `factory-v0.5`)

If the owner wants one new mechanic per release, make it the **assembly edge as
a per-assembler multi-input recipe graph**, bundled with demand arrivals only if
the forecast skill gate passes. This directly addresses the 0.4.0 review's
leading candidate and the 0089 finding that the recipe-only mix has no schedule
gap.

Then the following release can be the sequential multi-agent + stochastic-fault
release, and the one after that the layout/grammar/inventory/generative release.
See §7.

## 6. Other improvements

These are secondary to the gaps but improve the benchmark's credibility.

### 6.1 Benchmark methodology

1. **Separate task validity from baseline quality.** Add a challenge tier; do
   not use a learned-baseline success threshold as a task-admission gate.
2. **Cluster bootstrap by episode.** Current row-level CIs treat correlated
   samples as independent. Use episode/seed-level resampling.
3. **More power.** Increase test episodes/seeds for control and new tasks;
   report minimum detectable effect; use paired comparisons.
4. **Fair tuning.** Tune each model family on validation at a declared budget;
   report hyperparameters and compute. Do not compare a default MLP to a tuned
   GBDT and call it a family verdict.
5. **Private holdout.** Add a seed block not used during development.
6. **Layout split.** Add a fifth split with unseen layouts/topologies.
7. **Normalized metrics.** Report regret vs oracle/random, success, and cost.
8. **Failure-mode analysis.** Per-seed failure categories, not just means.
9. **Ablations.** No-mechanic controls for every new mechanic.
10. **Negative results first.** Follow the project's own protocol in cards and
    reports.

### 6.2 Reproducibility

- Publish the architecture baseline code (CNN/GRU/Transformer/MPNN) or mark the
  results as private diagnostics.
- Add the missing experiment records referenced by the map (0023, 0073) and
  document the numbering gaps (0064, 0065, 0068, 0069, 0080), or remove the
  references.
- Add a link checker/test that every experiment/task card/benchmark link
  resolves.
- Pin benchmark dependencies and record library versions (already partly done).
- Keep raw configs/seeds; commit summaries, not large arrays (already done).

### 6.3 Status and docs

- One source of truth for benchmark status (e.g., a registry TOML) and
  generated cards.
- Add `benchmark membership`, `status` (`frozen-headline`, `frozen-challenge`,
  `diagnostic`, `debug`, `retired`), `evidence`, and `public code` columns to the
  coverage map.
- Add a changelog to the coverage map.
- Fix the specific inconsistencies in §1.5.
- Update `docs/benchmark.md` to the current command/task list.

### 6.4 Code

- Add a task registry and a coverage manifest test.
- Add `harness/models/` for public CNN/GNN/Transformer/GRU/MLP variants.
- Add `harness/offline_rl.py`, `harness/marl.py`, `harness/or.py`,
  `harness/pomdp.py`, `harness/control_theory.py`, `harness/survival.py`,
  `harness/conformal.py` as optional extras.
- Add `benchmark-v04` with core/coverage/challenge tiers and a
  `benchmark-current` alias.
- Add a sample-efficiency runner.
- Add episode-level bootstrap utilities.

A minimal public baseline plan that respects the optional-dependency rule:

- `harness/models/cnn.py` — small CNN for grid tasks; Torch optional; a
  flattened MLP fallback for CI.
- `harness/models/gnn.py` — a small MPNN/GIN implemented directly in Torch
  (no PyG dependency); `graph_mp` remains the NumPy fallback.
- `harness/models/sequence.py` — GRU and a small Transformer; Torch optional.
- `harness/or.py` — exhaustive/ILP for small crew/order plans; OR-Tools
  optional, not required.
- `harness/offline_rl.py` — BC, CQL, IQL, Decision Transformer; Torch optional.
- `harness/marl.py` — independent Q, MAPPO, QMIX; Torch optional.

Keep every model behind the optional `train` extra and make the core benchmark
runnable with NumPy/scikit-learn only. That preserves the headless contract while
making the structured-model results reproducible.

### 6.5 Metrics and reporting

- Add normalized regret, oracle gap, success, sample efficiency, and cost to
  every control/planning task.
- Add calibration and sharpness, not just ECE.
- Add per-seed tables and failure categories.
- Add a "known limitations" section to every benchmark card.

### 6.6 Community and release

- No public leaderboard; keep a private holdout.
- Publish negative results and challenge tasks.
- Keep the game shell separate from the benchmark core.
- Do not add content volume without a diagnostic question.

### 6.7 A proposed coverage-map schema

The current map is a good narrative. To keep it a living ledger, give each row
an ID, a status, and an evidence link. A minimal schema:

**Task inventory**

| Column | Meaning |
|---|---|
| `task_id` | Stable ID, e.g. `factory.orders.control.v1` |
| `short_name` | Benchmark name, e.g. `order-control` |
| `kind` | regression / classification / self-supervised / control / planning / calibration / causal |
| `observation` | Adapter(s) |
| `action` | Action space or `none` |
| `label_or_reward` | Precise definition |
| `benchmark` | `factory-v0.3`, `factory-v0.4-coverage`, `challenge`, `diagnostic`, `none` |
| `status` | `frozen-headline` / `frozen-challenge` / `diagnostic` / `debug` / `retired` |
| `last_experiment` | Experiment number and link |
| `gate_result` | pass / mixed / fail / saturated |
| `evidence` | Link to summary/code |

**Model-family evidence**

| Column | Meaning |
|---|---|
| `family` | e.g. GNN, Transformer, offline RL |
| `public_code` | path or `none` |
| `frozen_tasks` | Where it is actually run in a frozen benchmark |
| `debug_evidence` | Experiment links |
| `expected_failure` | The weakness it should expose |
| `candidate_mechanic` | What would test it |
| `priority` | P0/P1/P2/P3 |

**Mechanic backlog**

| Column | Meaning |
|---|---|
| `mechanic` | Game rule change |
| `new_decisions` | Actions/observations it adds |
| `weaknesses` | Model weaknesses it exposes |
| `first_task` | The smallest task that tests it |
| `reuse` | Existing code/data |
| `cost` | low / medium / high |
| `priority` | P0/P1/P2/P3 |
| `unlocks` | Failed task or benchmark family it could promote |

**Promotion ledger**

| Column | Meaning |
|---|---|
| `task` | Experiment/task |
| `gate` | Which gate failed |
| `task_valid` | yes / no / mixed |
| `baseline_issue` | yes / no |
| `decision` | promote / challenge / diagnostic / redesign / retire |
| `next_action` | Concrete next step |

This schema would make the map self-auditing and prevent the current
"debug-as-coverage" ambiguity.

## 7. Proposed roadmap

This is a menu, not a commitment. The ordering respects "one mechanic per
milestone" and "publish before adding more content."

### 0.5.0 — coverage release (no new world)

- Publish a `factory-v0.4` coverage suite with the eight tasks in §5.4.
- Add public CNN/GNN/Transformer/GRU/OR baselines.
- Add a layout split, private holdout, episode-level bootstrap.
- Add a challenge tier for 0046, 0060, 0077, 0084.
- Fix status/docs/reproducibility issues.
- **Gate:** every new task has a card, splits, expected summary, and a
  positive/negative baseline; no frozen v0.3 asset changes.

### 0.6.0 — assembly edge + demand uncertainty

- Implement per-assembler recipe graph, component logistics, optional setup
  time/byproduct.
- Add `assembly-control`, `assembly-planning`, `bom-forecast`,
  `recipe-intervention`.
- Add demand arrivals/cancellations only if the forecast skill gate passes.
- Add GNN/OR/world-model/offline-RL baselines.
- **Gate:** default hash unchanged; oracle-scripted ≥10; learned-random ≥10;
  success ≥0.60; causal/calibration gates as applicable.

### 0.7.0 — sequential multi-agent + stochastic faults

- True per-crew sequential movement/repair/communication.
- `crew-sequential`, `crew-communication`, `agent-failure`.
- Stochastic faults, sensor noise, hidden state; `pomdp-maintenance`,
  `fault-detection-noise`.
- Add MAPPO/QMIX/MADDPG/CommNet, POMDP/belief models, survival/conformal.
- **Gate:** coordination/communication gain ≥10; oracle gap ≥10; challenge tier
  if learned success <0.60.

### 0.8.0 — layout, inventory, quality, generative

- Splitters/mergers/routing; larger/random layouts.
- Inventory/depletion/shared capacity.
- Quality/defects/rework.
- Enrich grammar; rerun generative feasibility; add generative task only if
  ≥20 structures and diversity ≥0.25.
- Add CNN/UNet/ViT, GNN/GAT, MILP/MPC, VAE/GAN/diffusion baselines.
- **Gate:** OOD gap, oracle gap, validity/diversity gates.

### 0.9.0+ — optional

- Market/auction, weather/renewables, adversarial/sabotage, language/
  instruction, transport/fleet.
- Only with a named model weakness and a task card.

## 8. Appendix

### A. Frozen task inventory (`factory-v0.3`)

| Task | Kind | Observation | Headline |
|---|---|---|---|
| throughput-vector | regression | vector | R²/MAE |
| throughput-grid | regression | grid | R²/MAE |
| throughput-entities | regression | entities/graph | graph_mp R² |
| masked-grid | self-supervised | grid | MSE/cosine |
| bottleneck | classification | vector | accuracy/balanced |
| expand-control | control | control | success/score |
| control-dynamics | self-supervised | control | MSE/cosine |
| planning-triage | planning | crew state | CEM/oracle |
| fault-calibration | calibration | sensors | ECE/balanced |
| causal-removal | prediction | intervention | target R² |
| order-control | control | production+orders | fulfilled value |
| order-planning | planning | order set | plan value |

### B. Positive tasks not in a frozen benchmark

Some of these have public task cards and world support but their experiment
harness lives under `experiments/...` and is not in the public tree. As of this
analysis, that includes the reliability contract (0031), wired cascade (0032),
and partial-throughput (0024) harnesses. Promotion requires a public
reimplementation, not just a card. The reliability-contract public harness has
since been started on `feat/0.5.0-reliability-contract`.

- partial-throughput (0024; public harness pending)
- reliability contract (0031; public harness started)
- wired cascade (0032; public harness pending)
- wire repair (0033)
- preventive wire (0035)
- maintenance threshold (0038)
- crew schedule (0041)
- two-crew coordination (0042/0044)
- twin-line assignment (0046)
- three-bridge triage (0055)
- recipe choice (0070)
- byproduct (0072)
- contract board (0074)
- power allocation (0016/0020)
- fault recovery (0009)
- fault + power (task card only; no experiment record)
- fault onset (0013)

### C. Public debug/diagnostic tasks

- fault prediction
- power brownout
- next-state
- view arrival (contract)
- decentralized triage (0077/0081/0082)
- transition planning (0083/0085/0086)
- maintenance calibration (0084)
- generative audit (0087)
- production mix (0089)
- order RL (0092)

### D. What not to do next

- Do not add more throughput variants; the tabular block is saturated.
- Do not add another calibration view without a skill gate.
- Do not add another Q variant on the same crew task.
- Do not tune PPO/BC after 0092.
- Do not add a generative model on seven line sequences.
- Do not add trains/fluids/3D/full circuit networks before coverage is published.
- Do not lower a gate or re-run a failed block to force a promotion.
- Do not headline a task that every baseline solves.
- Do not count a private experiment as public coverage.
- Do not compare methods at different tuning budgets.
- Do not add content volume without a diagnostic question.

### E. Open questions for the map

1. Which positive backlog tasks enter the coverage suite first, and which stay
   diagnostics?
2. Does the assembly edge create a real scheduling gap, or is it another
   global switch?
3. Does demand uncertainty carry forecast skill, or is it a redundant view?
4. Can a true sequential crew task produce a learned policy above 0.60, or is it
   a challenge tier?
5. Which model families can be published without Torch as an optional extra?
6. What is the minimum test power for a headline task (episodes/seeds)?
7. Is the layout split the next OOD benchmark, or is topology shift better?
8. Which task families should remain controls rather than headlines?
9. Can the generative grammar reach 20+ structures after assembly/splitters?
10. What is the release cadence: coverage release first, or mechanic first?

### F. References

- [`coverage-map.md`](coverage-map.md)
- [`coverage-review-0.4.0.md`](coverage-review-0.4.0.md)
- [`coverage-review-0.3.0.md`](coverage-review-0.3.0.md)
- [`coverage-review-p2.md`](coverage-review-p2.md)
- [`benchmarks/factory-v0.3/card.md`](../benchmarks/factory-v0.3/card.md)
- [`benchmarks/factory-v0.2/card.md`](../benchmarks/factory-v0.2/card.md)
- [`docs/tasks/`](tasks/)
- [`docs/experiments/`](experiments/)
- [`docs/efficiency.md`](efficiency.md)

---

*This analysis is intentionally opinionated. The owner decides scope; the
recommendations are ordered by diagnostic value per unit of cost, not by
content appeal.*
