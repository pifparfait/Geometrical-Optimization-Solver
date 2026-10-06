from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from src.spatial_site_contract import load_site_grid


@dataclass(frozen=True)
class TopologyCell:
    """
    One valid horizontal computational location in the VOLPE panel.

    This object intentionally contains no physical area, floor capacity,
    building level, height, or program typology.
    """
    cell_id: str
    segment: int
    row: int
    col: int


def build_volpe_topology(
    grid: Dict[str, Any],
) -> List[TopologyCell]:
    """
    Convert the validated VOLPE grid into canonical horizontal topology.

    No physical interpretation is introduced here.

    In particular, this function does NOT infer:
        - cell area from approximate 22 m spacing;
        - capacity from the nominal 500 m2 tangible block;
        - footprint from Ryan's historical 4000 sqft values;
        - plot <-> segment equivalence;
        - vertical levels or height;
        - program compatibility.
    """

    cells = grid.get("valid_cells")

    if not isinstance(cells, list) or not cells:
        raise ValueError(
            "VOLPE grid must contain non-empty valid_cells"
        )

    topology: List[TopologyCell] = []
    seen_coordinates = set()
    seen_ids = set()

    for i, cell in enumerate(cells):
        for field in ("segment", "row", "col"):
            if field not in cell:
                raise ValueError(
                    f"valid_cells[{i}] missing {field!r}"
                )

            if not isinstance(cell[field], int):
                raise ValueError(
                    f"valid_cells[{i}].{field} must be int"
                )

        segment = cell["segment"]
        row = cell["row"]
        col = cell["col"]

        if segment not in grid["segments"]:
            raise ValueError(
                f"valid_cells[{i}] uses unknown segment {segment}"
            )

        coordinate = (segment, row, col)

        if coordinate in seen_coordinates:
            raise ValueError(
                "Duplicate VOLPE topology coordinate: "
                f"{coordinate}"
            )

        seen_coordinates.add(coordinate)

        cell_id = f"seg{segment}:r{row}:c{col}"

        if cell_id in seen_ids:
            raise ValueError(
                f"Duplicate generated cell_id: {cell_id}"
            )

        seen_ids.add(cell_id)

        topology.append(
            TopologyCell(
                cell_id=cell_id,
                segment=segment,
                row=row,
                col=col,
            )
        )

    topology.sort(
        key=lambda x: (
            x.segment,
            x.row,
            x.col,
        )
    )

    return topology


def summarize_volpe_topology(
    topology: List[TopologyCell],
) -> Dict[str, Any]:
    counts = Counter(cell.segment for cell in topology)

    return {
        "cell_count": len(topology),
        "segments": sorted(counts),
        "cells_by_segment": {
            str(segment): counts[segment]
            for segment in sorted(counts)
        },
        "coordinate_system": "ROW_COL_SEGMENT",
        "horizontal_topology_only": True,
        "physical_area_inferred": False,
        "capacity_inferred": False,
        "levels_generated": False,
        "height_inferred": False,
        "plot_segment_mapping_inferred": False,
        "optimizer_executed": False,
    }


def load_volpe_topology(
    path: str | Path,
) -> tuple[List[TopologyCell], Dict[str, Any]]:
    grid = load_site_grid(path)
    topology = build_volpe_topology(grid)
    summary = summarize_volpe_topology(topology)

    return topology, summary
