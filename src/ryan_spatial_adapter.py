from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.spatial_optimizer import SpatialDemand
from src.spatial_program_contract import (
    load_spatial_program,
    summarize_spatial_program,
)


def adapt_spatial_program(
    payload: Dict[str, Any],
) -> Tuple[List[SpatialDemand], Dict[str, Any]]:
    """
    Convert Ryan's fixed spatial program into solver SpatialDemand objects.

    Ownership is preserved:
        Ryan    -> WHAT + HOW MUCH + TYPOLOGY
        Solver  -> WHERE + LEVEL

    podium_and_tower is not treated as a third physical slot typology.
    It is decomposed into two solver demands using Ryan's explicit split.

    This adapter:
        - does not change total program area;
        - does not infer physical capacity;
        - does not infer height;
        - does not infer accessibility cost;
        - does not execute the optimizer.
    """

    if payload.get("status") != "allocated":
        raise ValueError(
            "Ryan spatial program must have status='allocated'"
        )

    allocation = payload.get("allocation")

    if not isinstance(allocation, list) or not allocation:
        raise ValueError(
            "Ryan spatial program must contain a non-empty allocation"
        )

    demands: List[SpatialDemand] = []
    metadata: Dict[str, Dict[str, Any]] = {}

    def add_demand(
        *,
        demand_id: str,
        amenity_type: str,
        area_sqft: float,
        typology: str,
        source_location: str,
        program_unit: str,
        quantity: float,
        split_component: str | None,
    ) -> None:
        if demand_id in metadata:
            raise ValueError(
                f"Duplicate generated solver demand_id: {demand_id}"
            )

        area = float(area_sqft)

        if not math.isfinite(area) or area <= 0:
            raise ValueError(
                f"{demand_id}: area_sqft must be finite and > 0"
            )

        demands.append(
            SpatialDemand(
                program_id=demand_id,
                area_sqft=area,
                typology=typology,
            )
        )

        metadata[demand_id] = {
            "source_amenity_type": amenity_type,
            "source_location": source_location,
            "program_unit": program_unit,
            "quantity": float(quantity),
            "split_component": split_component,
            "area_sqft": area,
        }

    for program in allocation:
        amenity = program["amenity_type"]
        location = program["location"]
        area = float(program["area_sqft"])
        program_unit = program["program_unit"]
        quantity = float(program["quantity"])

        if location == "podium_and_tower":
            podium_area = float(program["podium_area_sqft"])
            tower_area = float(program["tower_area_sqft"])

            if (
                not math.isfinite(podium_area)
                or podium_area <= 0
                or not math.isfinite(tower_area)
                or tower_area <= 0
            ):
                raise ValueError(
                    f"{amenity}: mixed split components must be finite and > 0"
                )

            if not math.isclose(
                podium_area + tower_area,
                area,
                rel_tol=1e-9,
                abs_tol=1e-6,
            ):
                raise ValueError(
                    f"{amenity}: mixed split does not conserve source area"
                )

            add_demand(
                demand_id=f"{amenity}::podium",
                amenity_type=amenity,
                area_sqft=podium_area,
                typology="podium",
                source_location=location,
                program_unit=program_unit,
                quantity=quantity,
                split_component="podium",
            )

            add_demand(
                demand_id=f"{amenity}::tower",
                amenity_type=amenity,
                area_sqft=tower_area,
                typology="tower",
                source_location=location,
                program_unit=program_unit,
                quantity=quantity,
                split_component="tower",
            )

        else:
            add_demand(
                demand_id=amenity,
                amenity_type=amenity,
                area_sqft=area,
                typology=location,
                source_location=location,
                program_unit=program_unit,
                quantity=quantity,
                split_component=None,
            )

    source_summary = summarize_spatial_program(payload)

    solver_total = sum(d.area_sqft for d in demands)

    solver_by_typology = {
        typology: sum(
            d.area_sqft
            for d in demands
            if d.typology == typology
        )
        for typology in ("open_space", "podium", "tower")
    }

    if not math.isclose(
        solver_total,
        source_summary["total_program_area_sqft"],
        rel_tol=1e-9,
        abs_tol=1e-6,
    ):
        raise ValueError(
            "Ryan -> solver adapter failed total area conservation"
        )

    expected_by_typology = {
        "open_space": source_summary["open_space_area_sqft"],
        "podium": source_summary["podium_area_sqft"],
        "tower": source_summary["tower_area_sqft"],
    }

    for typology, expected in expected_by_typology.items():
        actual = solver_by_typology[typology]

        if not math.isclose(
            actual,
            expected,
            rel_tol=1e-9,
            abs_tol=1e-6,
        ):
            raise ValueError(
                f"{typology}: adapter area mismatch "
                f"{actual} != {expected}"
            )

    report = {
        "source_program_count": len(allocation),
        "solver_demand_count": len(demands),
        "source_total_area_sqft": source_summary[
            "total_program_area_sqft"
        ],
        "solver_total_area_sqft": solver_total,
        "solver_area_by_typology_sqft": solver_by_typology,
        "metadata": metadata,
        "what": "FIXED_BY_RYAN",
        "how_much": "FIXED_BY_RYAN",
        "typology": "FIXED_BY_RYAN",
        "where": "SOLVER_DECISION",
        "level": "SOLVER_DECISION",
        "physical_capacity_inferred": False,
        "optimizer_executed": False,
    }

    return demands, report


def load_ryan_spatial_demands(
    path: str | Path,
) -> Tuple[List[SpatialDemand], Dict[str, Any]]:
    payload = load_spatial_program(path)
    return adapt_spatial_program(payload)
