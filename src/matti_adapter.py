from collections import defaultdict


def to_matti_programs(scenario_id, placements, variant="optimized"):
    """Convert canonical placements into Matti development-program JSON."""
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
            "id": f"{scenario_id}-{variant}",
            "name": f"Geometry optimizer V0.2 — {variant}",
            "summary": (
                "V0.2 baseline geometry."
                if variant == "baseline"
                else "V0.2 technical compactness demo; no urban-performance or global-optimality claim."
            ),
            "segment": segment,
            "buildings": buildings,
        })
    return outputs
