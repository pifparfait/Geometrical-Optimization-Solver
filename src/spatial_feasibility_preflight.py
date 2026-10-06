from __future__ import annotations

from typing import Any, Dict, List


def _is_positive_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value > 0
    )


def evaluate_spatial_feasibility(
    program_summary: Dict[str, Any],
    site_authority: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate whether the current authorities are sufficient to make a
    physical feasibility claim.

    This preflight does NOT optimize geometry and does NOT infer missing
    physical quantities.

    Status semantics
    ----------------
    FEASIBLE:
        All required physical authorities are available and the explicit
        capacity checks pass.

    INFEASIBLE:
        Required physical authorities are available and at least one
        explicit physical capacity check proves the fixed Ryan program
        cannot fit.

    UNKNOWN:
        One or more authorities required for a physical feasibility claim
        are unresolved.

    V0.4c intentionally remains conservative. It must never turn missing
    physical information into a feasibility claim.
    """

    blockers: List[str] = []
    checks: Dict[str, str] = {}

    mapping = site_authority["plot_segment_mapping"]
    cell = site_authority["computational_cell"]
    envelope = site_authority["building_envelope"]
    ryan_site = site_authority["ryan_site"]

    # ---------------------------------------------------------
    # Contract-level facts
    # ---------------------------------------------------------

    checks["program_contract"] = "PASS"
    checks["site_contract"] = "PASS"

    program_area = float(program_summary["total_program_area_sqft"])

    if program_area <= 0:
        raise ValueError("Fixed Ryan program area must be positive")

    # ---------------------------------------------------------
    # Plot <-> segment authority
    # ---------------------------------------------------------

    if mapping.get("status") != "CONFIRMED":
        checks["plot_segment_mapping"] = "UNRESOLVED"
        blockers.append("PLOT_SEGMENT_MAPPING")
    else:
        checks["plot_segment_mapping"] = "PASS"

    # ---------------------------------------------------------
    # Exact plot geometry / area
    # ---------------------------------------------------------

    exact_plot_areas = ryan_site.get("exact_plot_areas")

    if not (
        isinstance(exact_plot_areas, list)
        and len(exact_plot_areas) == ryan_site.get("plot_count")
        and all(_is_positive_number(x) for x in exact_plot_areas)
    ):
        checks["exact_plot_areas"] = "UNRESOLVED"
        blockers.append("EXACT_PLOT_AREAS")
    else:
        checks["exact_plot_areas"] = "PASS"

    # ---------------------------------------------------------
    # Computational cell physical capacity
    # ---------------------------------------------------------

    cell_capacity = cell.get("sqft_capacity_per_level")

    if not _is_positive_number(cell_capacity):
        checks["sqft_to_cell_capacity"] = "UNRESOLVED"
        blockers.append("SQFT_TO_CELL_CAPACITY")
    else:
        checks["sqft_to_cell_capacity"] = "PASS"

    # ---------------------------------------------------------
    # Height authority
    # ---------------------------------------------------------

    height_cap = envelope.get("height_cap_value")

    if not (
        isinstance(height_cap, int)
        and not isinstance(height_cap, bool)
        and height_cap > 0
    ):
        checks["height_cap"] = "UNRESOLVED"
        blockers.append("HEIGHT_CAP")
    else:
        checks["height_cap"] = "PASS"

    # ---------------------------------------------------------
    # Tangible block -> computational cell semantics
    # ---------------------------------------------------------

    block = site_authority["tangible_block"]

    if block.get("computational_cell_equivalence") == "UNRESOLVED":
        checks["tangible_block_cell_mapping"] = "UNRESOLVED"
        blockers.append("TANGIBLE_BLOCK_CELL_MAPPING")
    else:
        checks["tangible_block_cell_mapping"] = "PASS"

    if block.get("vertical_capacity_semantics") == "UNRESOLVED":
        checks["vertical_capacity_semantics"] = "UNRESOLVED"
        blockers.append("VERTICAL_CAPACITY_SEMANTICS")
    else:
        checks["vertical_capacity_semantics"] = "PASS"

    # ---------------------------------------------------------
    # Conservative V0.4c decision
    # ---------------------------------------------------------

    if blockers:
        status = "UNKNOWN"
        reason = (
            "Physical feasibility cannot yet be determined because "
            "required spatial authorities remain unresolved."
        )
    else:
        # V0.4c deliberately does not implement the final capacity
        # arithmetic yet. Reaching this state means the authorities are
        # ready for the next physical-capacity implementation.
        status = "READY_FOR_CAPACITY_EVALUATION"
        reason = (
            "All required spatial authorities are available; explicit "
            "capacity arithmetic can now be evaluated."
        )

    return {
        "status": status,
        "reason": reason,
        "program_area_sqft": program_area,
        "open_space_area_sqft": float(
            program_summary["open_space_area_sqft"]
        ),
        "podium_area_sqft": float(
            program_summary["podium_area_sqft"]
        ),
        "tower_area_sqft": float(
            program_summary["tower_area_sqft"]
        ),
        "checks": checks,
        "blockers": blockers,
        "optimizer_executed": False,
        "program_modified": False,
        "physical_capacity_inferred": False,
    }
