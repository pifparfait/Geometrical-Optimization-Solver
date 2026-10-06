from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


def to_matti_3d_programs(
    scenario_id: str,
    solver_result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Project a canonical V0.5b 3D geometry into Matti's development-program
    representation.

    IMPORTANT:
    - This is a visualization adapter only.
    - It does not alter or reinterpret solver capacity.
    - open_space and unused cells do not create buildings.
    - built_5_story -> podium is a rendering convention only.
    - tower -> tower.
    - Program semantics are intentionally NOT mapped to Matti amenities/units.
    """

    if solver_result.get("status") != "OPTIMAL":
        raise ValueError(
            "Matti projection requires an OPTIMAL solver result"
        )

    by_segment = defaultdict(list)

    for g in solver_result["geometry"]:
        form = g["form"]

        if form in {"open_space", "unused"}:
            continue

        if form == "built_5_story":
            render_type = "podium"
        elif form == "tower":
            render_type = "tower"
        else:
            raise ValueError(
                f"Unsupported canonical geometry form: {form!r}"
            )

        stories = int(g["stories"])

        if stories <= 0:
            raise ValueError(
                f"Built cell {g['cell_id']} has invalid stories={stories}"
            )

        by_segment[int(g["segment"])].append(
            {
                "cell_id": g["cell_id"],
                "row": int(g["row"]),
                "col": int(g["col"]),
                "stories": stories,
                "canonical_form": form,
                "render_type": render_type,
            }
        )

    outputs: List[Dict[str, Any]] = []

    for segment in sorted(by_segment):
        buildings = []

        cells = sorted(
            by_segment[segment],
            key=lambda x: (x["row"], x["col"]),
        )

        for n, cell in enumerate(cells, start=1):
            last_level = cell["stories"] - 1

            levels = (
                [0]
                if last_level == 0
                else [0, last_level]
            )

            buildings.append(
                {
                    "id": f"optimized-stack-{n}",
                    "type": cell["render_type"],
                    "footprint": [
                        {
                            "row": cell["row"],
                            "col": cell["col"],
                        }
                    ],
                    "floors": [
                        {
                            "levels": levels,
                        }
                    ],
                }
            )

        outputs.append(
            {
                "id": scenario_id,
                "name": "VOLPE V0.5c optimized geometry",
                "summary": (
                    "Visualization of the geometry produced by the "
                    "VOLPE staged 3D spatial optimizer. Program semantics "
                    "are intentionally omitted in this geometry-only adapter."
                ),
                "segment": segment,
                "buildings": buildings,
            }
        )

    return outputs
