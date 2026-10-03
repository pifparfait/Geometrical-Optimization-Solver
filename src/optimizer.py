from collections import defaultdict


def expand_program(program, catalog):
    """Expand integer V0.1 demand and attach catalog metadata."""
    catalog_by_type = {a["amenity_type"]: a for a in catalog["amenities"]}
    items = []
    for entry in program:
        ptype = entry["program_type"]
        qty = entry["quantity"]
        if ptype not in catalog_by_type:
            raise ValueError(f"Unknown program_type: {ptype}")
        if not isinstance(qty, int) or qty < 0:
            raise ValueError(
                f"V0.1 requires non-negative integer quantities; got {ptype}={qty!r}"
            )
        for i in range(qty):
            items.append({
                "program_type": ptype,
                "instance": i + 1,
                "ground_level": bool(catalog_by_type[ptype].get("ground_level", False)),
            })
    return items


def solve(program, valid_cells, catalog):
    """
    Deterministic V0.1 horizontal + vertical allocator.

    Demo rules only:
    - ground_level=true items are placed at level 0;
    - remaining items are stacked above existing anchors when possible;
    - one footprint cell per vertical stack;
    - no area/FAR/height assumptions;
    - no optimality claim.
    """
    items = expand_program(program, catalog)
    ground_items = [x for x in items if x["ground_level"]]
    flexible_items = [x for x in items if not x["ground_level"]]

    by_segment = defaultdict(list)
    for cell in valid_cells:
        by_segment[cell["segment"]].append(cell)
    segments = sorted(by_segment)
    for s in segments:
        by_segment[s].sort(key=lambda c: (c["row"], c["col"]))

    cursors = {s: 0 for s in segments}
    anchors = []
    placements = []

    # First create level-0 anchors, round-robin across the five segments.
    for n, item in enumerate(ground_items):
        candidate_segments = segments[n % len(segments):] + segments[:n % len(segments)]
        segment = next((s for s in candidate_segments if cursors[s] < len(by_segment[s])), None)
        if segment is None:
            raise RuntimeError("Not enough valid VOLPE cells for V0.1 ground demand.")

        cell = by_segment[segment][cursors[segment]]
        cursors[segment] += 1
        anchor = {"segment": segment, "row": cell["row"], "col": cell["col"]}
        anchors.append(anchor)
        placements.append({
            **item, **anchor, "level": 0
        })

    # If there are no required-ground items, create one ground anchor from a flexible item.
    if not anchors and flexible_items:
        item = flexible_items.pop(0)
        segment = segments[0]
        cell = by_segment[segment][0]
        cursors[segment] = 1
        anchor = {"segment": segment, "row": cell["row"], "col": cell["col"]}
        anchors.append(anchor)
        placements.append({**item, **anchor, "level": 0})

    # Stack flexible items. Round-robin guarantees support on every lower level.
    for n, item in enumerate(flexible_items):
        anchor = anchors[n % len(anchors)]
        level = 1 + (n // len(anchors))
        placements.append({
            **item, **anchor, "level": level
        })

    return placements
