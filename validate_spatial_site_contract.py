from pathlib import Path

from src.spatial_site_contract import (
    build_site_authority,
    load_site_grid,
)


GRID = Path("data/geometry/volpe_site_grid.json")


def main() -> None:
    grid = load_site_grid(GRID)
    c = build_site_authority(grid)

    panel = c["volpe_panel"]
    ryan = c["ryan_site"]
    block = c["tangible_block"]
    cell = c["computational_cell"]
    envelope = c["building_envelope"]
    gate = c["capacity_gate"]

    print("============================================================")
    print("VOLPE V0.4b — SPATIAL SITE AUTHORITY CONTRACT")
    print("============================================================")
    print()

    print("VOLPE PANEL")
    print(f"segments              : {panel['segment_ids']}")
    print(f"valid cells           : {panel['valid_cell_count']}")
    print(f"cells by segment      : {panel['valid_cells_by_segment']}")
    print(f"segment semantics     : {panel['segment_semantics']}")
    print()

    print("RYAN SITE")
    print(f"plots                 : {ryan['plot_count']}")
    print(f"simulation            : {ryan['simulation_mode']}")
    print(
        f"example plot area     : "
        f"{ryan['current_example_plot_area_sqft']:,.3f} sqft"
    )
    print(f"exact plot areas      : {ryan['exact_plot_areas']}")
    print()

    print("PLOT <-> SEGMENT")
    print(
        f"status                : "
        f"{c['plot_segment_mapping']['status']}"
    )
    print(
        f"candidate             : "
        f"{c['plot_segment_mapping']['candidate']}"
    )
    print()

    print("TANGIBLE BLOCK")
    print(
        f"nominal area          : "
        f"{block['nominal_horizontal_area_m2']:,.3f} m2"
    )
    print(
        f"nominal area          : "
        f"{block['nominal_horizontal_area_sqft']:,.3f} sqft"
    )
    print(
        f"block -> cell         : "
        f"{block['computational_cell_equivalence']}"
    )
    print(
        f"vertical semantics    : "
        f"{block['vertical_capacity_semantics']}"
    )
    print()

    print("COMPUTATIONAL CELL")
    print(f"coordinates           : {cell['coordinates']}")
    print(f"spacing approx        : {cell['spacing_m_approx']} m")
    print(f"physical area         : {cell['physical_area']}")
    print(
        f"capacity per level    : "
        f"{cell['sqft_capacity_per_level']}"
    )
    print()

    print("BUILDING ENVELOPE")
    print(
        "Ryan 4000 sqft       : "
        f"{envelope['ryan_example_footprint_sqft_4000']}"
    )
    print(
        f"footprint             : "
        f"{envelope['footprint_decision']}"
    )
    print(
        f"height cap required   : "
        f"{envelope['height_cap_required']}"
    )
    print(
        f"height cap value      : "
        f"{envelope['height_cap_value']}"
    )
    print()

    print("CAPACITY GATE")
    print(
        f"sqft -> cell          : "
        f"{gate['sqft_to_computational_cell_mapping']}"
    )
    print(
        f"height feasibility    : "
        f"{gate['height_feasibility']}"
    )
    print(
        f"full feasibility      : "
        f"{gate['full_spatial_feasibility']}"
    )
    print()

    print("STATUS                : SITE_AUTHORITY_CAPTURED")
    print("OPTIMIZER EXECUTED    : FALSE")
    print("============================================================")


if __name__ == "__main__":
    main()
