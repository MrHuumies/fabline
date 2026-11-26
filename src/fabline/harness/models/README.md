# Public baseline models

This package contains original FABLINE baseline implementations for structured
observation views:

| Model | Input | Purpose |
|---|---|---|
| `CNNRegressor` | `(N, H, W, C)` grid | spatial inductive bias |
| `MPNNRegressor` | `(N, M, F)`, `(N, M)`, `(N, M, M)` | relational message passing |
| `GRURegressor` | `(N, T, F)` sequence | temporal memory |
| `TransformerRegressor` | `(N, T, F)` sequence | attention over a window |

## Public-tree policy

- The implementations are original FABLINE code, licensed under Apache-2.0 with
  the rest of the repository.
- No proprietary code is copied or vendored.
- The models use only PyTorch core. They do not require PyTorch Geometric or any
  other graph/model library.
- Torch remains an optional `train` extra. The benchmark core stays runnable
  with NumPy and scikit-learn; tests for these models skip when Torch is absent.

## Budget and reporting

Each model takes a `TorchTrainConfig` with a fixed epoch/batch/learning-rate
budget and a deterministic seed. Fitted models expose a `TorchTrainReport` with
sample count, parameter count, training seconds, and final loss. Report these
with every benchmark result; do not compare models at different budgets.

## Minimal use

```python
from fabline.harness.models import CNNRegressor, TorchTrainConfig

model = CNNRegressor(TorchTrainConfig(epochs=20, seed=0)).fit(grids, targets)
predictions = model.predict(test_grids)
print(model.report.as_dict())
```

Graph and sequence models have the obvious corresponding `fit`/`predict`
signatures; see their docstrings.
