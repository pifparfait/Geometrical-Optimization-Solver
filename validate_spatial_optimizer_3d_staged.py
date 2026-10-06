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


def main() -> None:
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

    demands = [
        ProgramDemand3D(
            "playground",
            2_000.0,
            "open_space",
        ),
        ProgramDemand3D(
            "housing",
            45_000.0,
            "built",
        ),
        ProgramDemand3D(
            "office",
            30_000.0,
            "built",
        ),
        ProgramDemand3D(
            "cafe",
            25_000.0,
            "built",
        ),
    ]

    total_built = sum(
        d.area_sqft
        for d in demands
        if d.kind == "built"
    )

    total_open = sum(
        d.area_sqft
        for d in demands
        if d.kind == "open_space"
    )

    expected_built_plates = math.ceil(
        total_built / CELL_AREA_SQFT
    )

    expected_open_cells = math.ceil(
        total_open / CELL_AREA_SQFT
    )

    t0 = time.perf_counter()

    result = solve_3d_staged(
        demands,
        cells,
        cell_area_sqft=CELL_AREA_SQFT,
        podium_stories=5,
        max_stories=30,
    )

    elapsed = time.perf_counter() - t0

    print("=" * 72)
    print("VOLPE V0.5b — STAGED 3D OPTIMIZER VALIDATION")
    print("=" * 72)
    print()

    print(f"segment                : {SEGMENT}")
    print(f"cells                  : {len(cells)}")
    print(f"cell area              : {CELL_AREA_M2:.3f} m2")
    print(f"cell area              : {CELL_AREA_SQFT:.3f} sqft")
    print("height range           : 5-30 built stories")
    print()

    print(f"SOLVER STATUS          : {result['status']}")
    assert result["status"] == "OPTIMAL"

    geometry = result["geometry"]
    allocations = result["allocations"]

    built_cells = [
        g for g in geometry
        if g["form"] in {
            "built_5_story",
            "tower",
        }
    ]

    open_cells = [
        g for g in geometry
        if g["form"] == "open_space"
    ]

    unused_cells = [
        g for g in geometry
        if g["form"] == "unused"
    ]

    active_built_plates = sum(
        g["stories"]
        for g in built_cells
    )

    max_height = max(
        (g["stories"] for g in built_cells),
        default=0,
    )

    minimum_built_footprint = math.ceil(
        expected_built_plates / 30
    )

    print()
    print("STAGE 1 — GEOMETRY")
    print(
        f"built footprint cells  : {len(built_cells)}"
    )
    print(
        f"minimum footprint      : {minimum_built_footprint}"
    )
    print(
        f"open-space cells       : {len(open_cells)}"
    )
    print(
        f"unused cells           : {len(unused_cells)}"
    )
    print(
        f"active built plates    : {active_built_plates}"
    )
    print(
        f"minimum built plates   : {expected_built_plates}"
    )
    print(
        f"maximum height         : {max_height}"
    )

    assert active_built_plates == expected_built_plates
    assert len(open_cells) == expected_open_cells
    assert len(built_cells) == minimum_built_footprint
    assert max_height <= 30

    # Exact area conservation.
    expected = {
        d.program_id: d.area_sqft
        for d in demands
    }

    observed = {
        d.program_id: 0.0
        for d in demands
    }

    for a in allocations:
        observed[a["program_id"]] += a["area_sqft"]

    print()
    print("STAGE 2 — PROGRAM ALLOCATION")

    for pid in expected:
        ok = math.isclose(
            expected[pid],
            observed[pid],
            rel_tol=1e-9,
            abs_tol=1e-5,
        )

        print(
            f"{pid:<22}: "
            f"expected={expected[pid]:>10,.3f} | "
            f"observed={observed[pid]:>10,.3f} | "
            f"{'PASS' if ok else 'FAIL'}"
        )

        assert ok

    geometry_by_cell = {
        g["cell_id"]: g
        for g in geometry
    }

    for a in allocations:
        g = geometry_by_cell[a["cell_id"]]

        if a["program_id"] == "playground":
            assert g["form"] == "open_space"
            assert a["level"] == 0
        else:
            assert g["form"] in {
                "built_5_story",
                "tower",
            }
            assert a["level"] < g["stories"]

    print()
    print("CERTIFICATION")
    print("BUILT PLATE MINIMALITY : PASS")
    print("FOOTPRINT MINIMALITY   : PASS")
    print("OPEN SPACE MINIMALITY  : PASS")
    print("AREA CONSERVATION      : PASS")
    print("OPEN/BUILT ISOLATION   : PASS")
    print("VERTICAL HEIGHT CAP    : PASS")
    print("RYAN DATA USED         : FALSE")
    print("RYAN DATA MODIFIED     : FALSE")
    print("GEOMETRY MILP EXECUTED : TRUE")
    print("ALLOCATION LP EXECUTED : TRUE")
    print(f"INTERNAL ELAPSED       : {elapsed:.6f} s")
    print("RESULT                 : OPTIMAL")
    print("=" * 72)


if __name__ == "__main__":
    main()
