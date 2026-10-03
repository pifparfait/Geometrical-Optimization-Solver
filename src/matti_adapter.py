from collections import defaultdict


def to_matti_programs(scenario_id, placements):
    """
    Convert canonical V0.1 placements into Matti development-program JSON.
    Placements sharing a cell become floors of the same single-cell plinth.
    """
    stacks = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for p in placements:
        key = (p["segment"], p["row"], p["col"])
        stacks[key][p["level"]][p["program_type"]] += 1

    by_segment = defaultdict(list)
    for (segment, row, col), levels in stacks.items():
        by_segment[segment].append((row, col, levels))

    outputs = []
    for segment in sorted(by_segment):
        buildings = []
        for n, (row, col, levels) in enumerate(
            sorted(by_segment[segment], key=lambda x: (x[0], x[1])), start=1
        ):
            floor_records = []
            max_level = max(levels)
            for level in range(max_level + 1):
                if level not in levels:
                    raise ValueError(
                        f"Vertical gap at segment={segment}, row={row}, col={col}, level={level}"
                    )
                floor_records.append({
                    "levels": [level],
                    "amenities": dict(sorted(levels[level].items()))
                })

            buildings.append({
                "id": f"stack-{n}",
                "type": "plinth",
                "footprint": [{"row": row, "col": col}],
                "floors": floor_records
            })

        outputs.append({
            "id": scenario_id,
            "name": "Geometry optimizer V0.1",
            "summary": "Deterministic horizontal and vertical interface test.",
            "segment": segment,
            "buildings": buildings,
        })
    return outputs
