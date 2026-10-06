from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from src.matti_3d_adapter import to_matti_3d_programs
from src.spatial_optimizer_3d_staged import (
    Cell3D,
    ProgramDemand3D,
    solve_3d_staged,
)
from src.volpe_topology import load_volpe_topology


ROOT = Path(__file__).resolve().parent

GRID = ROOT / "data" / "geometry" / "volpe_site_grid.json"
SCHEMA = ROOT / "schemas" / "development-program.schema.json"

OUT = ROOT / "outputs" / "v0_5c"
MATTI_OUT = OUT / "matti"

SCENARIO_ID = "v0-5c-synthetic"
SEGMENT = 2

CELL_AREA_M2 = 50.0
SQFT_PER_M2 = 10.763910416709722
CELL_AREA_SQFT = CELL_AREA_M2 * SQFT_PER_M2

PODIUM_STORIES = 5
MAX_STORIES = 30


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    topology, topology_summary = load_volpe_topology(GRID)

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

    demands = [
        ProgramDemand3D(
            program_id="playground",
            area_sqft=2_000.0,
            kind="open_space",
        ),
        ProgramDemand3D(
            program_id="housing",
            area_sqft=45_000.0,
            kind="built",
        ),
        ProgramDemand3D(
            program_id="office",
            area_sqft=30_000.0,
            kind="built",
        ),
        ProgramDemand3D(
            program_id="cafe",
            area_sqft=25_000.0,
            kind="built",
        ),
    ]

    result = solve_3d_staged(
        demands,
        cells,
        cell_area_sqft=CELL_AREA_SQFT,
        podium_stories=PODIUM_STORIES,
        max_stories=MAX_STORIES,
    )

    if result.get("status") != "OPTIMAL":
        raise RuntimeError(
            f"V0.5b did not return OPTIMAL: {result}"
        )

    canonical = {
        "scenario_id": SCENARIO_ID,
        "model": "volpe_spatial_optimizer_v0_5b_staged",
        "integration_version": "v0.5c",
        "status": result["status"],
        "scientific_scope": {
            "optimization": (
                "Staged 3D spatial geometry and exact program-area allocation"
            ),
            "renderer": (
                "Matti development-program geometry projection only"
            ),
            "rendering_convention": {
                "built_5_story": "podium",
                "tower": "tower",
                "note": (
                    "The built_5_story -> podium mapping is visualization-only. "
                    "The canonical solver result retains built_5_story because "
                    "5 stories is architecturally ambiguous under current rules."
                ),
            },
            "program_semantics_mapped_to_renderer": False,
        },
        "physical_assumptions": {
            "cell_area_m2": CELL_AREA_M2,
            "cell_area_sqft": CELL_AREA_SQFT,
            "podium_stories": PODIUM_STORIES,
            "max_stories": MAX_STORIES,
            "cell_area_authority": (
                "Friday team convention for optimization capacity"
            ),
            "viewer_geometry_used_for_capacity": False,
        },
        "topology": {
            "segment": SEGMENT,
            "segment_cell_count": len(cells),
            "full_site_cell_count": topology_summary["cell_count"],
            "coordinate_system": topology_summary["coordinate_system"],
        },
        "demands": [
            {
                "program_id": d.program_id,
                "area_sqft": d.area_sqft,
                "kind": d.kind,
            }
            for d in demands
        ],
        "solver_result": result,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    MATTI_OUT.mkdir(parents=True, exist_ok=True)

    canonical_path = OUT / "canonical_3d_solution.json"
    canonical_path.write_text(
        json.dumps(canonical, indent=2),
        encoding="utf-8",
    )

    matti_programs = to_matti_3d_programs(
        SCENARIO_ID,
        result,
    )

    schema = load_json(SCHEMA)
    validator = Draft202012Validator(schema)

    for program in matti_programs:
        errors = sorted(
            validator.iter_errors(program),
            key=lambda e: list(e.path),
        )

        if errors:
            details = "\n".join(
                f"- {'/'.join(map(str, e.path))}: {e.message}"
                for e in errors
            )
            raise ValueError(
                "Matti schema rejected V0.5c output:\n"
                + details
            )

        path = (
            MATTI_OUT
            / f"{SCENARIO_ID}-segment-{program['segment']}.json"
        )

        path.write_text(
            json.dumps(program, indent=2),
            encoding="utf-8",
        )

    print("=" * 72)
    print("VOLPE V0.5c — CANONICAL 3D -> MATTI GEOMETRY")
    print("=" * 72)
    print(f"scenario               : {SCENARIO_ID}")
    print(f"segment                : {SEGMENT}")
    print(f"segment cells          : {len(cells)}")
    print(f"cell area              : {CELL_AREA_M2:.3f} m2")
    print(f"cell area              : {CELL_AREA_SQFT:.3f} sqft")
    print(f"solver status          : {result['status']}")
    print(f"built floor plates     : {result['built_floor_plates']}")
    print(f"open cells             : {result['open_cells']}")
    print(f"Matti programs         : {len(matti_programs)}")
    print("Matti schema           : PASS")
    print(f"canonical output       : {canonical_path}")
    print(f"Matti output           : {MATTI_OUT}")
    print("=" * 72)


if __name__ == "__main__":
    main()
