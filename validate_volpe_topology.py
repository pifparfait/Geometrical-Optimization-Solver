from src.volpe_topology import load_volpe_topology


GRID = "data/geometry/volpe_site_grid.json"

EXPECTED_COUNTS = {
    "0": 22,
    "1": 22,
    "2": 24,
    "3": 24,
    "4": 20,
}


def main() -> None:
    topology, summary = load_volpe_topology(GRID)

    print("============================================================")
    print("VOLPE V0.4f — SPATIAL TOPOLOGY")
    print("HORIZONTAL TOPOLOGY ONLY")
    print("============================================================")
    print()

    print(f"valid cells           : {summary['cell_count']}")
    print(f"segments              : {summary['segments']}")
    print(f"cells by segment      : {summary['cells_by_segment']}")
    print(f"coordinates           : {summary['coordinate_system']}")

    print()
    print("FIRST CANONICAL CELLS")

    for cell in topology[:5]:
        print(
            f"{cell.cell_id:<18} "
            f"segment={cell.segment} "
            f"row={cell.row} "
            f"col={cell.col}"
        )

    if summary["cell_count"] != 112:
        raise AssertionError(
            f"Expected 112 valid cells, got {summary['cell_count']}"
        )

    if summary["segments"] != [0, 1, 2, 3, 4]:
        raise AssertionError(
            f"Unexpected segments: {summary['segments']}"
        )

    if summary["cells_by_segment"] != EXPECTED_COUNTS:
        raise AssertionError(
            "Unexpected cells-by-segment distribution: "
            f"{summary['cells_by_segment']}"
        )

    if len({c.cell_id for c in topology}) != len(topology):
        raise AssertionError("Topology cell IDs are not unique")

    coordinates = {
        (c.segment, c.row, c.col)
        for c in topology
    }

    if len(coordinates) != len(topology):
        raise AssertionError(
            "Topology coordinates are not unique"
        )

    forbidden_attributes = (
        "capacity_sqft",
        "area_sqft",
        "level",
        "height",
        "typology",
    )

    for cell in topology:
        for attribute in forbidden_attributes:
            if hasattr(cell, attribute):
                raise AssertionError(
                    "TopologyCell unexpectedly contains "
                    f"physical attribute {attribute!r}"
                )

    print()
    print("CELL COUNT             : PASS")
    print("SEGMENT DISTRIBUTION   : PASS")
    print("COORDINATE UNIQUENESS  : PASS")
    print("CANONICAL IDS          : PASS")
    print("PHYSICAL AREA INFERRED : FALSE")
    print("CAPACITY INFERRED      : FALSE")
    print("LEVELS GENERATED       : FALSE")
    print("HEIGHT INFERRED        : FALSE")
    print("PLOT MAPPING INFERRED  : FALSE")
    print("OPTIMIZER EXECUTED     : FALSE")
    print("TOPOLOGY               : PASS")
    print("============================================================")


if __name__ == "__main__":
    main()
