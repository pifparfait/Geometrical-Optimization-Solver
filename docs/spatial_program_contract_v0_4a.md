# VOLPE V0.4a — Ryan → Parfait Spatial Program Contract

## Purpose

V0.4 separates program selection from spatial optimization.

The upstream economic/developer model determines:

- **WHAT** is built;
- **HOW MUCH** is built;
- **TYPOLOGY**: `open_space`, `podium`, `tower`, or
  `podium_and_tower`.

The VOLPE Geometrical Optimization Solver receives that program as fixed
input and determines:

- **WHERE** the program is placed in the VOLPE grid;
- **LEVEL** at which the program is placed.

## Decision boundary

Ryan:

    WHAT + HOW MUCH + TYPOLOGY

Parfait:

    WHERE + LEVEL

Matti:

    VISUALIZATION

## V0.4a scope

V0.4a validates only the Ryan → Parfait handoff.

It does **not**:

- rerun economic optimization;
- change Ryan's selected quantities;
- change Ryan's typology assignments;
- assume a sqft-to-grid-cell conversion;
- execute the spatial optimizer;
- modify the Matti adapter.

## Capacity

Physical spatial capacity remains a separate contract.

The current project clarification proposes approximately 500 m² per
VOLPE tangible/grid block. Whether this represents usable floor capacity
at every vertical level must be treated as a configurable physical-model
parameter until its vertical semantics are frozen.

## Scientific interpretation

The spatial problem is conditional on a fixed development program.

Given fixed program Q, the downstream solver searches for a feasible
and optimized 3D spatial realization.

If no spatial realization satisfies the physical constraints, the
spatial solver must be permitted to return INFEASIBLE rather than alter
the upstream program silently.
