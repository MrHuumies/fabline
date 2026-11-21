# Contributing to FABLINE

FABLINE is a research testbed. The human owner is the final authority on scope.
When in doubt, ask; do not silently expand the project.

Read first:

1. [`project_intent.md`](project_intent.md) — goals and non-goals.
2. [`docs/testbed.md`](docs/testbed.md) — what the testbed is for.
3. [`docs/interface.md`](docs/interface.md) — contracts.
4. [`docs/world.md`](docs/world.md) — factory mechanics.
5. The relevant ADR in [`docs/decisions/`](docs/decisions/) before changing
   behavior.

## Invariants

- **Canonical state is the source of truth.** Observations, rewards, labels, and
  splits are derived. Do not put ML concerns in the simulation.
- **Headless first.** The core runs without a renderer, a GPU, or the ML stack.
- **The renderer never mutates state.** It reads state or replays.
- **Determinism.** All randomness comes from an explicit seeded generator. No
  global RNG, no time-seeded behavior. Same seed plus actions equals the same
  state hash.
- **Fixed timestep.** Tick order is explicit and stable. Do not hide updates in
  the renderer or observation adapters.
- **Stable entity IDs.** Never identify entities by list position.
- **Data-driven content.** Recipes, maps, tasks, and versions live in data files
  where practical.
- **Every task has a card.** Phenomenon, observations, actions, label/reward,
  split, metrics, baselines, known pitfalls, version.
- **Every dataset has a card.** Generation config, stats, biases, versions,
  license.
- **Every benchmark has a version.** Frozen tasks, splits, seeds, and expected
  results. Immutable tags.
- **Pre-register experiments.** Question, hypothesis, conditions, seeds, compute,
  analysis, kill criteria.
- **Report negative results first.** Do not bury them.
- **Do not tune the world to make a method win.** If a method needs a different
  regime, state it as a scope condition.
- **No new dependency** without a concrete reason and a docs update.
- **No hidden state.** If it affects an episode, it is in the state, the config,
  or the event log.

## Commands

```bash
./scripts/bootstrap.sh
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src
.venv/bin/python -m fabline smoke --ticks 200
.venv/bin/python -m fabline shared-suite --out results/factory-v0.1
.venv/bin/python -m fabline fault-benchmark --out results/fault-benchmark --episodes 40
.venv/bin/python -m fabline power-benchmark --out results/power-benchmark --episodes 40
FABLINE_PERF=1 .venv/bin/python -m pytest tests/perf -q -s
```

Do not claim a command works until it is tested.

## Change protocol

For anything that changes behavior or scope:

1. Write or update an ADR in `docs/decisions/`.
2. Add or update a test in `tests/`.
3. Run the test suite and a short headless run.
4. Update the relevant docs, task cards, and dataset cards.
5. Report what changed and what was intentionally not changed.

Small refactors and bug fixes do not need an ADR, but they still need tests.

## Style

- Python 3.12, `from __future__ import annotations`, type hints on public
  functions, dataclasses for configuration and records.
- Keep configuration in typed configs or TOML, not magic numbers in systems.
- Prefer explicit names and small functions over clever abstraction.
- Comments explain *why* a choice exists, not what the code does.
- The renderer should reveal dynamics, not hide them.
- Prefer stdlib and NumPy in the core; keep Torch and Pygame optional.

## License

Code is Apache-2.0; docs and generated data are CC-BY-4.0. By contributing, you
agree that your contribution is licensed under the same terms.
