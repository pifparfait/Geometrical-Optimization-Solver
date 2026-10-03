#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent

required = [
    ROOT / "src" / "economic_contract.py",
    ROOT / "schemas" / "ryan_economic_input.schema.json",
    ROOT / "data" / "mock" / "ryan_economic_placeholder.json",
]
missing = [str(x.relative_to(ROOT)) for x in required if not x.exists()]
if missing:
    raise SystemExit("Missing V0.3a prerequisites: " + ", ".join(missing))

files = {
"docs/economic_formulation_v0_3b.md": '''# VOLPE V0.3b — Economic Formulation Contract

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
''',
"src/economic_formulation.py": '''"""V0.3b economic formulation helpers.

Evaluates P(q) = sum_a p_a q_a only when quantities are explicitly supplied in the same basis as each economic row.
Does not optimize q, convert sqft to VOLPE cells, or choose objective weights.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Sequence

@dataclass(frozen=True)
class EconomicRow:
    amenity_type: str
    footprint_sqft: float
    profit_usd: float
    basis_unit: str

def rows_from_contract(contract: Mapping) -> list[EconomicRow]:
    return [EconomicRow(str(i["amenity_type"]), float(i["footprint_sqft"]), float(i["profit_usd"]), str(i["basis_unit"])) for i in contract["amenities"]]

def profit_accounting(rows: Sequence[EconomicRow], quantities: Mapping[str, float], quantity_basis: Mapping[str, str]) -> float:
    """Return sum(profit_usd * quantity) after exact basis checks."""
    total = 0.0
    row_types = {row.amenity_type for row in rows}
    extra = (set(quantities) | set(quantity_basis)) - row_types
    if extra:
        raise ValueError(f"Unknown amenity types in quantity inputs: {sorted(extra)}")
    for row in rows:
        if row.amenity_type not in quantities:
            raise ValueError(f"Missing quantity for {row.amenity_type}")
        if row.amenity_type not in quantity_basis:
            raise ValueError(f"Missing quantity basis for {row.amenity_type}")
        supplied_basis = quantity_basis[row.amenity_type]
        if supplied_basis != row.basis_unit:
            raise ValueError(f"Basis mismatch for {row.amenity_type}: economic={row.basis_unit!r}, quantity={supplied_basis!r}")
        q = float(quantities[row.amenity_type])
        if q < 0:
            raise ValueError(f"Negative quantity for {row.amenity_type}: {q}")
        total += row.profit_usd * q
    return total
''',
"validate_economic_formulation.py": '''#!/usr/bin/env python3
import json
from pathlib import Path
from src.economic_formulation import profit_accounting, rows_from_contract

ROOT = Path(__file__).resolve().parent
with (ROOT / "data" / "mock" / "ryan_economic_placeholder.json").open("r", encoding="utf-8") as f:
    contract = json.load(f)
rows = rows_from_contract(contract)

# Unit test only: q=1 in each row's explicitly declared basis.
# This is not a planning scenario and is not an optimizer decision.
q_test = {row.amenity_type: 1.0 for row in rows}
basis_test = {row.amenity_type: row.basis_unit for row in rows}
observed = profit_accounting(rows, q_test, basis_test)
expected = sum(row.profit_usd for row in rows)
assert observed == expected

first = rows[0]
bad_basis = dict(basis_test)
bad_basis[first.amenity_type] = "__INTENTIONAL_MISMATCH__"
try:
    profit_accounting(rows, q_test, bad_basis)
except ValueError:
    mismatch_gate = "PASS"
else:
    raise AssertionError("Basis mismatch was not rejected")

print("VOLPE V0.3b — ECONOMIC FORMULATION CONTRACT")
print(f"economic rows       : {len(rows)}")
print("profit identity     : PASS")
print(f"basis mismatch gate : {mismatch_gate}")
print("quantity semantics  : ENDOGENOUS / SYMBOLIC")
print("sqft spatial use    : NOT YET")
print("optimizer changed   : NO")
print("optimization run    : NO")
print("weights/scaling     : NOT DEFINED")
print("STATUS              : ECONOMIC_FORMULATION_READY")
'''
}

for rel, content in files.items():
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {rel}")
    path.write_text(content, encoding="utf-8")
    print(f"CREATED: {rel}")

print()
print("V0.3b ECONOMIC FORMULATION SCAFFOLD: PASS")
print("No optimizer logic was changed.")
