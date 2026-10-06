from pathlib import Path

from src.spatial_program_contract import (
    load_spatial_program,
    summarize_spatial_program,
)
from src.spatial_site_contract import (
    build_site_authority,
    load_site_grid,
)
from src.spatial_feasibility_preflight import (
    evaluate_spatial_feasibility,
)


PROGRAM = Path("data/external/ryan/building_use_example.json")
GRID = Path("data/geometry/volpe_site_grid.json")


def fmt(value: float) -> str:
    return f"{value:,.3f}"


def main() -> None:
    program = load_spatial_program(PROGRAM)
    program_summary = summarize_spatial_program(program)

    grid = load_site_grid(GRID)
    site_authority = build_site_authority(grid)

    result = evaluate_spatial_feasibility(
        program_summary,
        site_authority,
    )

    print("============================================================")
    print("VOLPE V0.4c — SPATIAL FEASIBILITY PREFLIGHT")
    print("============================================================")
    print()

    print("PROGRAM CONTRACT")
    print(f"status                : {result['checks']['program_contract']}")
    print(
        f"program area          : "
        f"{fmt(result['program_area_sqft'])} sqft"
    )
    print(
        f"open space            : "
        f"{fmt(result['open_space_area_sqft'])} sqft"
    )
    print(
        f"podium                : "
        f"{fmt(result['podium_area_sqft'])} sqft"
    )
    print(
        f"tower                 : "
        f"{fmt(result['tower_area_sqft'])} sqft"
    )
    print("quantities             : FIXED_BY_RYAN")
    print("typology               : FIXED_BY_RYAN")
    print()

    print("SITE CONTRACT")
    print(f"status                : {result['checks']['site_contract']}")
    print(
        f"plots                 : "
        f"{site_authority['ryan_site']['plot_count']}"
    )
    print(
        f"segments              : "
        f"{site_authority['volpe_panel']['segment_count']}"
    )
    print()

    print("PHYSICAL PREFLIGHT")

    labels = [
        ("plot <-> segment", "plot_segment_mapping"),
        ("exact plot areas", "exact_plot_areas"),
        ("sqft -> cell capacity", "sqft_to_cell_capacity"),
        ("height cap", "height_cap"),
        ("block -> cell", "tangible_block_cell_mapping"),
        ("vertical capacity", "vertical_capacity_semantics"),
    ]

    for label, key in labels:
        print(f"{label:<22}: {result['checks'][key]}")

    print()
    print("BLOCKERS")

    for blocker in result["blockers"]:
        print(f"- {blocker}")

    if not result["blockers"]:
        print("- NONE")

    print()
    print(f"RESULT                : {result['status']}")
    print(f"REASON                : {result['reason']}")
    print()
    print(
        f"optimizer executed    : "
        f"{str(result['optimizer_executed']).upper()}"
    )
    print(
        f"Ryan program modified : "
        f"{str(result['program_modified']).upper()}"
    )
    print(
        f"capacity inferred     : "
        f"{str(result['physical_capacity_inferred']).upper()}"
    )
    print("============================================================")

    # Current frozen authorities must NOT support a physical
    # feasibility claim yet.
    if result["status"] != "UNKNOWN":
        raise AssertionError(
            "Current V0.4b authorities should produce UNKNOWN feasibility"
        )

    expected_blockers = {
        "PLOT_SEGMENT_MAPPING",
        "EXACT_PLOT_AREAS",
        "SQFT_TO_CELL_CAPACITY",
        "HEIGHT_CAP",
        "TANGIBLE_BLOCK_CELL_MAPPING",
        "VERTICAL_CAPACITY_SEMANTICS",
    }

    if set(result["blockers"]) != expected_blockers:
        raise AssertionError(
            "Unexpected V0.4c blocker set: "
            f"{result['blockers']}"
        )

    print("CURRENT-STATE ASSERTION : PASS")


if __name__ == "__main__":
    main()
