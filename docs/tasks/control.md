# Task card — line expansion control

- **Task ID:** `factory.expand.control.v1`
- **Version:** 0.1.0
- **Status:** debug task, not a frozen benchmark
- **World:** factory-0.1.0
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Build a working production line on a fixed six-tile path from an ore tile to a
depot. The agent chooses the entity type at the next path tile, or removes the
most recent entity to retry. The task tests sequential construction, delayed
reward, and credit assignment.

## Contract

- **Observation:** 49 features — 18 vector statistics, 6×5 path one-hot
  (empty/miner/belt/furnace/assembler), and path progress.
- **Actions:** `noop`, `build_miner`, `build_belt`, `build_furnace`,
  `build_assembler`, `remove` (6 macro actions).
- **Reward:** depot score gained over the decision interval minus a 0.05 build
  penalty. Illegal actions incur an additional penalty and advance time.
- **Decision interval:** 10 ticks.
- **Episode length:** 300 ticks (30 decisions).
- **Success:** final depot score ≥ 20.
- **Path:** ore at (1,4), six path tiles (1..6,4), depot at (7,4), 16×8 world.

## Data

- Online task; no offline dataset in M2.
- Suite evaluation: 5 episodes per seed, seeds (0,1,2); training budget 200
  episodes for tabular Q, 40 episodes for behavior cloning.

## Metrics

- Mean final score.
- Success rate (score ≥ 20).
- Mean reward.
- Path completion rate.
- Steps (fixed at 30 in the current episode length).

## Baselines

| Policy | Notes |
|---|---|
| scripted | Build the known optimal sequence |
| random | Uniform over legal macro actions |
| tabular Q | Q-learning over `(path_index, path_types)` |
| behavior cloning | Decision tree on scripted trajectories with 20% exploration |

## Results — `factory-v0.1` (pooled seeds 0–2, 95% bootstrap CIs)

| policy | mean score | success rate | mean reward | path complete |
|---|---:|---:|---:|---:|
| scripted | 140.00 [140.00, 140.00] | 1.00 [1.00, 1.00] | 139.70 | 1.00 |
| random | 2.00 [0.00, 6.00] | 0.07 [0.00, 0.20] | 0.99 | 0.53 |
| tabular Q | 143.33 [141.33, 146.00] | 1.00 [1.00, 1.00] | 143.03 | 1.00 |
| behavior cloning | 140.00 [140.00, 140.00] | 1.00 [1.00, 1.00] | 139.70 | 1.00 |

## Known pitfalls

- **Fixed path:** the task is a constrained construction puzzle, not general
  factory building. It does not test spatial planning over the full grid.
- **Scripted expert:** behavior cloning learns from a known optimal sequence;
  it is a sanity check, not a hard imitation result.
- **Tabular Q is seed-sensitive:** some seeds fail or learn a worse line. The
  table pools three seeds; report per-seed results before making claims.
- **Reward shaping:** none beyond the build penalty. The task is sparse until
  production starts.
- **No PPO:** tabular Q and behavior cloning are the learned baselines. PPO on
  the full action space is future work.
- **No faults or power:** the environment is deterministic and fully
  observable along the path.

## Negative controls

- Random should fail to build a working line.
- A policy that builds a valid but wrong-order line should score below the
  scripted line.

## Next variants (M3+)

- Full `grid_build` action space with a PPO baseline.
- Multiple paths, obstacles, and ore choices.
- Faults and power constraints.
- Held-out path lengths and layouts.

## Changelog

- 2026-11-21 — card created; M2 suite results added.
