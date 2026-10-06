# VOLPE V0.4b — Spatial Site Authority Contract

## Purpose

V0.4b separates physical facts from unresolved mappings before
square-foot program demand is introduced into the computational grid.

## Current authorities

### VOLPE computational representation

The current VOLPE grid contains five panel segments, indexed 0 through 4,
and 112 valid computational cells.

The grid contains row, column, segment, and approximate spacing
information.

The approximate spacing is not interpreted as physical cell area.

### Ryan site representation

Ryan clarified on 2026-10-06 that:

- VOLPE is split into five plots;
- the plots are simulated independently;
- 12,500 sqft is the current example size of one plot;
- exact dimensions of all five plots will be supplied later;
- the 4,000 sqft podium/tower footprint in the dummy model is arbitrary.

Therefore the 4,000 sqft value is not a physical authority for the
spatial solver.

### Height

Ryan confirmed that a physical height cap is required.

No numerical height cap is currently available.

### Tangible block

Yasushi clarified on 2026-10-06 that the current tangible block should
be interpreted nominally as approximately 500 m².

This contract does not assume that one tangible block equals one
computational grid cell.

It also does not yet assume that 500 m² represents floor capacity at
every vertical level.

## Unresolved mapping

The repository defines five panel segments and Ryan defines five
independently simulated plots.

A one-to-one plot-to-segment relationship is the current candidate
interpretation, but remains pending explicit confirmation.

## Capacity gate

Until the tangible-block/computational-cell relationship and height
limit are resolved, the solver must not claim physical sqft capacity or
full physical feasibility.

## Decision ownership

Ryan determines:

- what is built;
- how much is built;
- open-space / podium / tower typology.

The spatial solver determines:

- footprint / spatial form;
- row and column placement;
- vertical level.

The final optimization objective is being aligned with the upstream
agent model. The current intended formulation is to minimize agent
movement/accessibility cost subject to physical and program constraints.

The V0.2 compactness objective remains a technical baseline and is not
treated as the final urban-performance objective.
