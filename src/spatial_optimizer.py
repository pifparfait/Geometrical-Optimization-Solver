from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class SpatialDemand:
    program_id: str
    area_sqft: float
    typology: str


@dataclass(frozen=True)
class SpatialSlot:
    slot_id: str
    segment: int
    row: int
    col: int
    level: int
    capacity_sqft: float
    allowed_typologies: Tuple[str, ...]


@dataclass(frozen=True)
class AllocationVariable:
    program_id: str
    slot_id: str
    cost_per_sqft: float


def solve_spatial_allocation(
    demands: Sequence[SpatialDemand],
    slots: Sequence[SpatialSlot],
    cost_per_sqft: Dict[Tuple[str, str], float],
) -> Dict:
    """
    Parametric fixed-program spatial allocation kernel.

    Decision variable:
        s[a,j] >= 0
        square feet of program a allocated to spatial slot j.

    Objective:
        minimize sum(cost[a,j] * s[a,j])

    Constraints:
        1. Every fixed program area is allocated exactly.
        2. Every slot respects its supplied physical capacity.
        3. Program can only use slots compatible with its supplied typology.

    Important:
        - This function does not infer physical capacity.
        - This function does not alter Ryan's demand.
        - This function does not infer accessibility costs.
        - This first kernel is continuous-area allocation.
        - Discrete unit integrity and building-form constraints are later layers.
    """

    if not demands:
        raise ValueError("demands must be non-empty")

    if not slots:
        raise ValueError("slots must be non-empty")

    demand_ids = [d.program_id for d in demands]
    slot_ids = [s.slot_id for s in slots]

    if len(set(demand_ids)) != len(demand_ids):
        raise ValueError("program_id values must be unique")

    if len(set(slot_ids)) != len(slot_ids):
        raise ValueError("slot_id values must be unique")

    for d in demands:
        if d.area_sqft <= 0:
            raise ValueError(
                f"{d.program_id}: area_sqft must be > 0"
            )

    for s in slots:
        if s.capacity_sqft <= 0:
            raise ValueError(
                f"{s.slot_id}: capacity_sqft must be > 0"
            )

    variables: List[AllocationVariable] = []

    for demand in demands:
        for slot in slots:
            if demand.typology not in slot.allowed_typologies:
                continue

            key = (demand.program_id, slot.slot_id)

            if key not in cost_per_sqft:
                raise ValueError(
                    "Missing explicit cost_per_sqft for compatible "
                    f"assignment {key}"
                )

            cost = float(cost_per_sqft[key])

            if not np.isfinite(cost) or cost < 0:
                raise ValueError(
                    f"{key}: cost_per_sqft must be finite and >= 0"
                )

            variables.append(
                AllocationVariable(
                    program_id=demand.program_id,
                    slot_id=slot.slot_id,
                    cost_per_sqft=cost,
                )
            )

    if not variables:
        return {
            "status": "INFEASIBLE",
            "reason": "NO_COMPATIBLE_ASSIGNMENTS",
            "objective": None,
            "allocations": [],
            "backend": "SCIPY_HIGHS",
            "global_optimality_claim": False,
        }

    var_index = {
        (v.program_id, v.slot_id): i
        for i, v in enumerate(variables)
    }

    n = len(variables)

    c = np.array(
        [v.cost_per_sqft for v in variables],
        dtype=float,
    )

    # Continuous square-foot allocation.
    integrality = np.zeros(n, dtype=int)

    bounds = Bounds(
        lb=np.zeros(n),
        ub=np.full(n, np.inf),
    )

    rows = []
    lower = []
    upper = []

    # Exact fixed-program conservation.
    for demand in demands:
        row = np.zeros(n)

        for slot in slots:
            idx = var_index.get(
                (demand.program_id, slot.slot_id)
            )
            if idx is not None:
                row[idx] = 1.0

        if not np.any(row):
            return {
                "status": "INFEASIBLE",
                "reason": (
                    "NO_COMPATIBLE_SLOT_FOR_PROGRAM:"
                    f"{demand.program_id}"
                ),
                "objective": None,
                "allocations": [],
                "backend": "SCIPY_HIGHS",
                "global_optimality_claim": False,
            }

        rows.append(row)
        lower.append(demand.area_sqft)
        upper.append(demand.area_sqft)

    # Explicit slot capacity.
    for slot in slots:
        row = np.zeros(n)

        for demand in demands:
            idx = var_index.get(
                (demand.program_id, slot.slot_id)
            )
            if idx is not None:
                row[idx] = 1.0

        if np.any(row):
            rows.append(row)
            lower.append(-np.inf)
            upper.append(slot.capacity_sqft)

    A = np.vstack(rows)

    constraints = LinearConstraint(
        A,
        lb=np.array(lower, dtype=float),
        ub=np.array(upper, dtype=float),
    )

    result = milp(
        c=c,
        integrality=integrality,
        bounds=bounds,
        constraints=constraints,
        options={"disp": False},
    )

    if result.status == 2:
        return {
            "status": "INFEASIBLE",
            "reason": str(result.message),
            "objective": None,
            "allocations": [],
            "backend": "SCIPY_HIGHS",
            "solver_status": int(result.status),
            "global_optimality_claim": False,
        }

    if not result.success:
        return {
            "status": "SOLVER_FAILURE",
            "reason": str(result.message),
            "objective": None,
            "allocations": [],
            "backend": "SCIPY_HIGHS",
            "solver_status": int(result.status),
            "global_optimality_claim": False,
        }

    slot_by_id = {s.slot_id: s for s in slots}

    allocations = []

    for variable, value in zip(variables, result.x):
        if value <= 1e-8:
            continue

        slot = slot_by_id[variable.slot_id]

        allocations.append({
            "program_id": variable.program_id,
            "slot_id": variable.slot_id,
            "segment": slot.segment,
            "row": slot.row,
            "col": slot.col,
            "level": slot.level,
            "area_sqft": float(value),
            "cost_per_sqft": variable.cost_per_sqft,
        })

    allocations.sort(
        key=lambda x: (
            x["program_id"],
            x["segment"],
            x["row"],
            x["col"],
            x["level"],
        )
    )

    return {
        "status": "OPTIMAL",
        "reason": str(result.message),
        "objective": float(result.fun),
        "allocations": allocations,
        "backend": "SCIPY_HIGHS",
        "solver_status": int(result.status),
        "global_optimality_claim": True,
        "claim_scope": (
            "continuous linear allocation model supplied to HiGHS"
        ),
    }
