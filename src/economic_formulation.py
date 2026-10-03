"""V0.3b economic formulation helpers.

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
