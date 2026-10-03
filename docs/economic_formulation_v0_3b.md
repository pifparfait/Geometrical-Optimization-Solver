# VOLPE V0.3b — Economic Formulation Contract

## Status

This document defines the minimum economic semantics needed before profit is allowed to affect the VOLPE optimizer. It does **not** execute an optimization and it does **not** convert square feet into VOLPE cells.

## Inputs from Ryan

For each amenity/program type `a`: `amenity_type`, `footprint_sqft`, `profit_usd`, and `basis_unit`.

The `basis_unit` is authoritative. `profit_usd` and `footprint_sqft` must refer to the same decision unit before the row can be used in a joint optimization.

## Decision semantics

Let `q_a` denote the number of economic basis units of amenity/program type `a` selected by the future joint optimizer. At V0.3b, `q_a` is a **symbolic endogenous decision quantity**. It is not supplied by Ryan and is not inferred from the legacy `ryan_program.json` fixture.

For a compatible basis, `P_a(q_a) = p_a * q_a`, where `p_a` is `profit_usd`. Total profit is `P(q) = sum_a p_a * q_a`. This is a bookkeeping identity, not yet an optimization objective.

## Unit invariant

A row may contribute to `P(q)` only when `q_a` is expressed in the same basis represented by `basis_unit`. V0.3b does not silently convert among per-facility, per-square-foot, per-dwelling-unit, per-commercial-bay, or other bases.

## Footprint semantics

`footprint_sqft` is retained as input, but V0.3b does not map it to VOLPE cells, floors, or capacity. The approximately 22 m grid spacing is not treated as a cell area. A sourced spatial-capacity rule is required before footprint can constrain geometry.

## Relationship to V0.2 geometry

The V0.2 compactness score remains a technical geometric regularizer only. It is not a proxy for profit, livability, urban performance, or social welfare.

## Future joint problem

The intended architecture allows the optimizer eventually to decide WHAT, HOW MUCH, WHERE, and LEVEL jointly, with economic value `P(x)`, social/livability value `L(x)`, geometric regularization `G(x)`, and feasibility/capacity constraints `C(x)`.

No weights, normalization scales, Pareto preferences, or scalarization method are fixed in V0.3b.

## V0.3b non-claims

V0.3b does not claim that Ryan has supplied final economic values, that placeholder values are empirical, that profit is the sole/preferred objective, that square feet can yet be converted to VOLPE capacity, that quantities are exogenous, that a weighted-sum objective has been selected, or that economic optimization has run.
