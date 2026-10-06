# VOLPE V0.4c — Spatial Feasibility Preflight

## Purpose

V0.4c connects the fixed Ryan spatial-program contract (V0.4a) with
the physical/site authority contract (V0.4b).

It does not execute spatial optimization.

Its purpose is to prevent unresolved physical information from being
silently converted into a feasibility claim.

## Status semantics

### UNKNOWN

One or more physical authorities required to evaluate the fixed program
remain unresolved.

UNKNOWN does not mean infeasible.

### INFEASIBLE

INFEASIBLE may only be returned after the required physical authorities
are available and an explicit capacity or geometric constraint proves
that the fixed Ryan program cannot be spatially realized.

The spatial solver must not remove or reduce Ryan's program in order to
make it feasible.

### FEASIBLE

FEASIBLE may only be returned after the required physical authorities
are available and all implemented physical feasibility checks pass.

V0.4c does not yet implement the final capacity arithmetic. Once all
authorities are present it reports readiness for capacity evaluation
rather than claiming feasibility prematurely.

## Current expected state

With the currently frozen authorities, the expected result is UNKNOWN.

Current unresolved authorities include:

- Ryan plot to VOLPE panel-segment mapping;
- exact physical areas of the five plots;
- sqft capacity of a computational cell per level;
- numerical height cap;
- tangible-block to computational-cell mapping;
- vertical interpretation of the nominal 500 m² tangible-block area.

## Scientific rule

No physical capacity may be inferred from:

- approximate 22 m grid spacing;
- row/column coordinates;
- number of computational cells;
- Ryan's discarded 4,000 sqft example footprint;
- the nominal 500 m² tangible-block area without an explicit mapping to
  the computational representation.

## Decision ownership

Ryan's program remains fixed.

The preflight does not:

- select amenities;
- remove amenities;
- change quantities;
- change typology;
- optimize geometry.

A future spatial solver will determine spatial form, row/column
placement, and vertical level only after the physical authority gate is
satisfied.
