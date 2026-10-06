from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict


SQFT_PER_M2 = 10.763910416709722


def load_site_grid(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        grid = json.load(f)

    if grid.get("segments") != [0, 1, 2, 3, 4]:
        raise ValueError(
            "Expected current VOLPE panel segments [0,1,2,3,4]"
        )

    cells = grid.get("valid_cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError("VOLPE grid must contain valid_cells")

    counts = Counter(c["segment"] for c in cells)

    for segment in grid["segments"]:
        if counts[segment] == 0:
            raise ValueError(
                f"VOLPE segment {segment} contains no valid cells"
            )

    return grid


def build_site_authority(grid: Dict[str, Any]) -> Dict[str, Any]:
    counts = Counter(c["segment"] for c in grid["valid_cells"])

    return {
        "volpe_panel": {
            "segment_count": 5,
            "segment_ids": [0, 1, 2, 3, 4],
            "valid_cell_count": len(grid["valid_cells"]),
            "valid_cells_by_segment": {
                str(s): counts[s]
                for s in sorted(counts)
            },
            "segment_semantics": "PANEL_SEGMENT",
            "authority": "CURRENT_VOLPE_GRID_AND_MATTI_SCHEMA",
        },

        "ryan_site": {
            "plot_count": 5,
            "simulation_mode": "INDEPENDENT_PER_PLOT",
            "current_example_plot_area_sqft": 12500.0,
            "exact_plot_areas": "PENDING_RYAN",
            "authority": "RYAN_CLARIFICATION_2026_10_06",
        },

        "plot_segment_mapping": {
            "status": "PENDING_CONFIRMATION",
            "candidate": "ONE_RYAN_PLOT_PER_VOLPE_PANEL_SEGMENT",
        },

        "tangible_block": {
            "nominal_horizontal_area_m2": 500.0,
            "nominal_horizontal_area_sqft": 500.0 * SQFT_PER_M2,
            "authority": "YASUSHI_CLARIFICATION_2026_10_06",
            "computational_cell_equivalence": "UNRESOLVED",
            "vertical_capacity_semantics": "UNRESOLVED",
        },

        "computational_cell": {
            "coordinates": "ROW_COL_SEGMENT",
            "spacing_m_approx": grid.get("cell_spacing_m_approx"),
            "physical_area": "UNRESOLVED",
            "sqft_capacity_per_level": "UNRESOLVED",
        },

        "building_envelope": {
            "ryan_example_footprint_sqft_4000": "NON_AUTHORITATIVE",
            "footprint_decision": "SPATIAL_SOLVER_DECISION",
            "height_cap_required": True,
            "height_cap_value": "PENDING",
        },

        "capacity_gate": {
            "sqft_to_computational_cell_mapping": "BLOCKED",
            "height_feasibility": "BLOCKED",
            "full_spatial_feasibility": "NOT_YET_DETERMINABLE",
        },
    }
