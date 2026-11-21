# ADR 0008 — M2 task suite and observation additions

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0003, ADR 0005, ADR 0007

## Context

M1 had one supervised task and two observation views. M2 needed to demonstrate
that the testbed supports multiple task families and observation structures
without changing the world. The milestone also needed a control task and
stronger baselines.

The full design space includes a GNN baseline, a PPO baseline on the full grid
action space, and shared episode projections. All three are larger than the M2
budget.

## Decision

1. Add `entities.v1`: a padded entity feature matrix, entity mask, and adjacency
   matrix. Tabular baselines consume a flattened form; a GNN can consume the
   arrays directly.
2. Add `factory.next_state.predict.v1`: passive next-observation prediction on
   the vector view.
3. Add `factory.expand.control.v1`: a constrained six-tile line-building task
   with six macro actions, a build penalty, and a success threshold. Use
   scripted, random, tabular Q, and behavior-cloning baselines.
4. Add gradient-boosting and MLP baselines for tabular tasks. Keep scikit-learn
   in the optional harness layer, not the core.
5. For M2, each offline task generates its own episodes. Shared episode
   projections remain the target architecture and move to M3.

## Alternatives considered

- **PPO on the full grid action space.** Rejected for M2: the 82k-action space
  and long horizon would dominate the milestone.
- **A GNN baseline.** Rejected for M2: the graph format is ready, but a GNN is a
  separate modeling effort. Flattened tabular baselines are enough to prove the
  view.
- **Shared episodes now.** Rejected for M2: it requires a multi-target dataset
  format and a projection layer. It is the main M3 deliverable.
- **A bottleneck-classification task.** Deferred: counterfactual labels are
  useful but expensive, and the milestone already has five tasks.

## Consequences

- M2 has five tasks and a one-command suite.
- The graph view is supported but not yet tested with a relational model.
- Next-state is saturated by copy/linear; M3 needs harder self-supervised
  variants.
- Control is a constrained puzzle, not general factory building.
- Per-task datasets duplicate some world rollouts; M3 should unify them.
- The suite is a debug suite, not a frozen benchmark.
