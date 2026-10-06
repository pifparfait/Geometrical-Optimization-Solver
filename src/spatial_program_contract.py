from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Dict


ALLOWED_LOCATIONS = {
    "open_space",
    "podium",
    "tower",
    "podium_and_tower",
}

REQUIRED_PROGRAM_FIELDS = {
    "amenity_type",
    "location",
    "program_unit",
    "quantity",
    "area_sqft",
}


def load_spatial_program(path: str | Path) -> Dict[str, Any]:
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if payload.get("status") != "allocated":
        raise ValueError(
            f"Expected Ryan program status='allocated', got {payload.get('status')!r}"
        )

    allocation = payload.get("allocation")

    if not isinstance(allocation, list) or not allocation:
        raise ValueError("Ryan program must contain a non-empty 'allocation' list")

    seen = set()

    for i, program in enumerate(allocation):
        missing = REQUIRED_PROGRAM_FIELDS - set(program)
        if missing:
            raise ValueError(
                f"Program row {i} missing required fields: {sorted(missing)}"
            )

        amenity = program["amenity_type"]

        if amenity in seen:
            raise ValueError(
                f"Duplicate amenity_type in fixed spatial program: {amenity}"
            )
        seen.add(amenity)

        location = program["location"]
        if location not in ALLOWED_LOCATIONS:
            raise ValueError(
                f"{amenity}: unsupported location/typology {location!r}"
            )

        area = float(program["area_sqft"])
        if not math.isfinite(area) or area <= 0:
            raise ValueError(
                f"{amenity}: area_sqft must be finite and > 0"
            )

        quantity = float(program["quantity"])
        if not math.isfinite(quantity) or quantity <= 0:
            raise ValueError(
                f"{amenity}: quantity must be finite and > 0"
            )

        # Mixed podium+tower allocations supplied by Ryan must reconcile
        # exactly to the fixed total program area.
        if location == "podium_and_tower":
            if (
                "podium_area_sqft" not in program
                or "tower_area_sqft" not in program
            ):
                raise ValueError(
                    f"{amenity}: podium_and_tower requires explicit area split"
                )

            split = (
                float(program["podium_area_sqft"])
                + float(program["tower_area_sqft"])
            )

            if not math.isclose(
                split,
                area,
                rel_tol=1e-9,
                abs_tol=1e-6,
            ):
                raise ValueError(
                    f"{amenity}: podium+tower split does not equal area_sqft"
                )

    return payload


def summarize_spatial_program(payload: Dict[str, Any]) -> Dict[str, Any]:
    allocation = payload["allocation"]

    counts = Counter(p["location"] for p in allocation)

    total_program_area = sum(
        float(p["area_sqft"]) for p in allocation
    )

    open_space_area = sum(
        float(p["area_sqft"])
        for p in allocation
        if p["location"] == "open_space"
    )

    podium_area = sum(
        (
            float(p["podium_area_sqft"])
            if p["location"] == "podium_and_tower"
            else float(p["area_sqft"])
        )
        for p in allocation
        if p["location"] in {"podium", "podium_and_tower"}
    )

    tower_area = sum(
        (
            float(p["tower_area_sqft"])
            if p["location"] == "podium_and_tower"
            else float(p["area_sqft"])
        )
        for p in allocation
        if p["location"] in {"tower", "podium_and_tower"}
    )

    return {
        "program_count": len(allocation),
        "location_counts": dict(sorted(counts.items())),
        "total_program_area_sqft": total_program_area,
        "open_space_area_sqft": open_space_area,
        "podium_area_sqft": podium_area,
        "tower_area_sqft": tower_area,
        "what": "FIXED_BY_RYAN",
        "how_much": "FIXED_BY_RYAN",
        "typology": "FIXED_BY_RYAN",
        "where": "SOLVER_DECISION",
        "level": "SOLVER_DECISION",
    }
