from __future__ import annotations

import math
import time
from pathlib import Path

from src.spatial_optimizer_3d_staged import (
    Cell3D,
    ProgramDemand3D,
    solve_3d_staged,
)
from src.volpe_topology import load_volpe_topology


GRID = Path("data/geometry/volpe_site_grid.json")

CELL_AREA_M2 = 50.0
SQFT_PER_M2 = 10.763910416709722
CELL_AREA_SQFT = CELL_AREA_M2 * SQFT_PER_M2

SEGMENT = 2

RYAN_BUILT_SQFT = 604_077.297
RYAN_OPEN_SQFT = 2_500.0


def run_case(cells, max_stories: int):
    demands = [
        ProgramDemand3D(
            "legacy_ryan_open_space",
            RYAN_OPEN_SQFT,
            "open_space",
        ),
        ProgramDemand3D(
            "legacy_ryan_built_program",
            RYAN_BUILT_SQFT,
            "built",
        ),
    ]

    t0 = time.perf_counter()

    result = solve_3d_staged(
        demands,
        cells,
        cell_area_sqft=CELL_AREA_SQFT,
        podium_stories=5,
        max_stories=max_stories,
    )

    elapsed = time.perf_counter() - t0

    return result, elapsed


def main():
    topology, _ = load_volpe_topology(GRID)

    cells = [
        Cell3D(
            cell_id=c.cell_id,
            segment=c.segment,
            row=c.row,
            col=c.col,
        )
        for c in topology
        if c.segment == SEGMENT
    ]

    assert len(cells) == 24

    required_open_cells = math.ceil(
        RYAN_OPEN_SQFT / CELL_AREA_SQFT
    )

    required_built_plates = math.ceil(
        RYAN_BUILT_SQFT / CELL_AREA_SQFT
    )

    max_buildable_cells = (
        len(cells) - required_open_cells
    )

    print("=" * 72)
    print("VOLPE V0.5b-R1 — 3D HEIGHT BOUNDARY TEST")
    print("=" * 72)

    print()
    print(f"segment                : {SEGMENT}")
    print(f"total cells            : {len(cells)}")
    print(f"cell area              : {CELL_AREA_SQFT:.3f} sqft")
    print(f"Ryan open space        : {RYAN_OPEN_SQFT:,.3f} sqft")
    print(f"Ryan built program     : {RYAN_BUILT_SQFT:,.3f} sqft")
    print(f"required open cells    : {required_open_cells}")
    print(f"max buildable cells    : {max_buildable_cells}")
    print(f"required built plates  : {required_built_plates}")

    assert required_open_cells == 5
    assert required_built_plates == 1123
    assert max_buildable_cells == 19

    print()
    print("CASE A — H=30")

    r30, t30 = run_case(cells, 30)

    capacity30 = (
        max_buildable_cells
        * 30
    )

    print(
        f"available built plates : {capacity30}"
    )
    print(
        f"required built plates  : {required_built_plates}"
    )
    print(
        f"solver status          : {r30['status']}"
    )
    print(
        f"elapsed                : {t30:.6f} s"
    )

    assert capacity30 < required_built_plates
    assert r30["status"] == "INFEASIBLE"

    print()
    print("CASE B — H=65")

    r65, t65 = run_case(cells, 65)

    capacity65 = (
        max_buildable_cells
        * 65
    )

    print(
        f"available built plates : {capacity65}"
    )
    print(
        f"required built plates  : {required_built_plates}"
    )
    print(
        f"solver status          : {r65['status']}"
    )
    print(
        f"elapsed                : {t65:.6f} s"
    )

    assert capacity65 >= required_built_plates
    assert r65["status"] == "OPTIMAL"

    geometry = r65["geometry"]

    built = [
        g for g in geometry
        if g["form"] in {
            "built_5_story",
            "tower",
        }
    ]

    opened = [
        g for g in geometry
        if g["form"] == "open_space"
    ]

    unused = [
        g for g in geometry
        if g["form"] == "unused"
    ]

    built_plates = sum(
        g["stories"] for g in built
    )

    max_height = max(
        g["stories"] for g in built
    )

    expected_footprint = math.ceil(
        required_built_plates / 65
    )

    print()
    print("H=65 GEOMETRY")
    print(
        f"built footprint cells  : {len(built)}"
    )
    print(
        f"minimum footprint      : {expected_footprint}"
    )
    print(
        f"open-space cells       : {len(opened)}"
    )
    print(
        f"unused cells           : {len(unused)}"
    )
    print(
        f"active built plates    : {built_plates}"
    )
    print(
        f"maximum height         : {max_height}"
    )

    assert expected_footprint == 18
    assert len(built) == 18
    assert len(opened) == 5
    assert len(unused) == 1
    assert built_plates == 1123
    assert max_height <= 65

    print()
    print("CERTIFICATION")
    print("H=30 INFEASIBILITY     : PASS")
    print("H=65 FEASIBILITY       : PASS")
    print("HEIGHT BOUNDARY FLIP   : PASS")
    print("PROGRAM MODIFIED       : FALSE")
    print("RYAN LEGACY AREA USED  : TRUE")
    print("3D SOLVER EXECUTED     : TRUE")
    print("RESULT                  : PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
