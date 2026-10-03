# VOLPE V0.3c — Decision & Capacity Contract

## Status
This document defines the symbolic decision layer connecting the economic
formulation to the future joint VOLPE optimizer. It does **not** define a
physical square-foot-to-cell conversion and does **not** execute optimization.

## 1. Decision variable
For program type `a`, grid row `r`, column `c`, and level `l`:

    x[a,r,c,l] in {0,1}

`x=1` means program type `a` is assigned to that VOLPE spatial position and
level, subject to future feasibility rules. In V0.3c this is symbolic only.

## 2. Endogenous economic quantity
For each program type `a`, q[a] >= 0 denotes the economic quantity used by the
profit formulation. The relation is deliberately unresolved:

    q[a] = Psi_a(x)

The form of Psi depends on the economic basis and physical-capacity semantics.
V0.3c does not choose among per-facility, per-square-foot, per-unit, or other
bases.

## 3. Economic objective identity
Once q[a] is validly defined on the same basis as the economic input:

    P(q) = sum_a p[a] * q[a]

This identity does not by itself authorize optimization.

## 4. Spatial capacity gate
Ryan input contains `footprint_sqft`, but V0.3c has no sourced rule for:

    footprint_sqft -> VOLPE spatial capacity

Therefore V0.3c forbids:
- treating one amenity instance as one VOLPE cell;
- inferring cell area from approximate grid-point spacing;
- deriving floors, FAR, height, or capacity from absent data;
- consuming `footprint_sqft` as a solver constraint.

`footprint_sqft` is available data but is not yet spatially actionable.

## 5. Readiness states
- decision variables: DEFINED SYMBOLICALLY
- economic quantity: ENDOGENOUS / SYMBOLIC
- profit formulation: READY
- footprint sqft: AVAILABLE
- VOLPE capacity: UNRESOLVED
- sqft-to-cell mapping: BLOCKED
- joint optimization: BLOCKED BY CAPACITY CONTRACT
- optimizer changed: NO

## 6. What unlocks joint optimization
A later version may unlock spatial capacity only after an explicit, provenanced
rule defines how physical program demand consumes VOLPE capacity. The rule must
specify units and basis and must not be inferred from the placeholder fixture.

Objective normalization, livability/social utility, Pareto/weighted
multi-objective choices, and final solver technology are outside V0.3c.
