"""VOLPE V0.3c symbolic decision/capacity contract.

No solver variables are created here. This module records what is defined,
what remains unresolved, and the gate preventing unsourced sqft-to-cell
conversion from entering the optimizer.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class DecisionIndex:
    amenity_type: str
    row: int
    col: int
    level: int


@dataclass(frozen=True)
class CapacityReadiness:
    decision_variables: str = "DEFINED_SYMBOLICALLY"
    economic_quantity: str = "ENDOGENOUS_SYMBOLIC"
    profit_formulation: str = "READY"
    footprint_sqft: str = "AVAILABLE"
    volpe_capacity: str = "UNRESOLVED"
    sqft_to_cell_mapping: str = "BLOCKED"
    joint_optimization: str = "BLOCKED_BY_CAPACITY_CONTRACT"
    optimizer_changed: bool = False


READINESS = CapacityReadiness()


def symbolic_quantity_relation() -> str:
    return "q_a = Psi_a(x)"


def require_spatial_capacity_rule(capacity_rule) -> None:
    if capacity_rule is None:
        raise ValueError(
            "Spatial capacity unresolved: no sourced sqft-to-VOLPE capacity "
            "rule is available. footprint_sqft must not be converted to cells."
        )


def assert_no_spatial_consumption(rows: Iterable[Dict]) -> Tuple[int, float]:
    rows = list(rows)
    total_sqft_field_value = sum(float(r["footprint_sqft"]) for r in rows)
    return len(rows), total_sqft_field_value
