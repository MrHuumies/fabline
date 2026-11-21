# Examples

From the repository root:

```bash
.venv/bin/python examples/quickstart.py
.venv/bin/python examples/generate_data.py --out datasets/example
.venv/bin/python examples/fault_demo.py
.venv/bin/python examples/power_demo.py
```

The generated dataset is ignored by git. `generate_data.py` writes observations,
labels, manifests, replays, and a dataset card.

## Pre-generated sample

The release also includes `fabline-example-data-v0.1.zip` with:

- a core factory dataset with vector observations and future-score labels;
- a faults dataset with vector and diagnostics views;
- a power dataset with vector and power views.

Each directory has a manifest, dataset card, per-episode observations, and
validated replays. Unzip it into a working directory, then point the harness at
the dataset directory.
