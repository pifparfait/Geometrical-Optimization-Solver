from collections import defaultdict


def expand_program(program, catalog):
    """Expand integer demo demand and attach catalog metadata."""
    catalog_by_type = {a["amenity_type"]: a for a in catalog["amenities"]}
    items = []
    for entry in program:
        ptype = entry["program_type"]
        qty = entry["quantity"]
        if ptype not in catalog_by_type:
            raise ValueError(f"Unknown program_type: {ptype}")
        if not isinstance(qty, int) or qty < 0:
            raise ValueError(
                f"V0.2 requires non-negative integer quantities; got {ptype}={qty!r}"
            )
        for i in range(qty):
            items.append({
                "program_type": ptype,
                "instance": i + 1,
                "ground_level": bool(catalog_by_type[ptype].get("ground_level", False)),
            })
    return items


def _prepare_cells(valid_cells):
    cells = [dict(c) for c in valid_cells]
    cells.sort(key=lambda c: (c["segment"], c["row"], c["col"]))
    return cells


def _build_placements(items, anchor_cells):
    ground_items = [x for x in items if x["ground_level"]]
    flexible_items = [x for x in items if not x["ground_level"]]

    if not anchor_cells and items:
        raise RuntimeError("No anchor cells available.")

    placements = []

    # Each ground-required item gets one distinct level-0 anchor.
    for item, cell in zip(ground_items, anchor_cells):
        placements.append({**item, **cell, "level": 0})

    # If no item requires ground level, place one flexible item at level 0
    # to create physical support for the remaining stack.
    if not ground_items and flexible_items:
        item = flexible_items.pop(0)
        placements.append({**item, **anchor_cells[0], "level": 0})

    # Stack flexible items above existing anchors.
    for n, item in enumerate(flexible_items):
        anchor = anchor_cells[n % len(anchor_cells)]
        level = 1 + (n // len(anchor_cells))
        placements.append({**item, **anchor, "level": level})

    return placements


def _required_anchor_count(items):
    ground_count = sum(1 for x in items if x["ground_level"])
    if ground_count:
        return ground_count
    return 1 if items else 0


def dispersion_objective(cells):
    """
    Pairwise squared grid-distance across occupied footprint cells.

    This is a technical compactness objective for V0.2 only:
        sum_{i<j} ((row_i-row_j)^2 + (col_i-col_j)^2)

    It is NOT an urban-performance claim.
    """
    total = 0
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            dr = cells[i]["row"] - cells[j]["row"]
            dc = cells[i]["col"] - cells[j]["col"]
            total += dr * dr + dc * dc
    return total


def baseline_solve(program, valid_cells, catalog):
    """Reproduce the V0.1 round-robin anchor logic."""
    items = expand_program(program, catalog)
    k = _required_anchor_count(items)
    if k == 0:
        return [], []

    by_segment = defaultdict(list)
    for cell in _prepare_cells(valid_cells):
        by_segment[cell["segment"]].append(cell)

    segments = sorted(by_segment)
    cursors = {s: 0 for s in segments}
    anchors = []

    for n in range(k):
        candidate_segments = segments[n % len(segments):] + segments[:n % len(segments)]
        segment = next((s for s in candidate_segments if cursors[s] < len(by_segment[s])), None)
        if segment is None:
            raise RuntimeError("Not enough valid VOLPE cells for baseline demand.")
        cell = by_segment[segment][cursors[segment]]
        cursors[segment] += 1
        anchors.append(cell)

    return _build_placements(items, anchors), anchors


def optimize_solve(program, valid_cells, catalog):
    """
    V0.2 deterministic 1-swap local search over footprint cells.

    Starts from the V0.1 baseline. At every iteration, replace one selected
    footprint cell with one unused valid site cell if that strictly reduces
    pairwise squared grid dispersion. Stop at a 1-swap local optimum.

    No global optimality claim is made.
    """
    items = expand_program(program, catalog)
    baseline_placements, baseline_cells = baseline_solve(program, valid_cells, catalog)
    if not baseline_cells:
        return [], [], {
            "baseline_objective": 0,
            "optimized_objective": 0,
            "iterations": 0,
            "single_swap_local_optimum": True,
        }

    all_cells = _prepare_cells(valid_cells)
    selected = [dict(c) for c in baseline_cells]
    best_score = dispersion_objective(selected)
    iterations = 0

    while True:
        selected_keys = {(c["segment"], c["row"], c["col"]) for c in selected}
        best_move = None

        for out_idx in range(len(selected)):
            for candidate in all_cells:
                key = (candidate["segment"], candidate["row"], candidate["col"])
                if key in selected_keys:
                    continue

                trial = [dict(c) for c in selected]
                trial[out_idx] = dict(candidate)

                # No duplicate footprint cells.
                trial_keys = {(c["segment"], c["row"], c["col"]) for c in trial}
                if len(trial_keys) != len(trial):
                    continue

                score = dispersion_objective(trial)
                move_key = (
                    score,
                    candidate["row"],
                    candidate["col"],
                    candidate["segment"],
                    out_idx,
                )
                if score < best_score and (best_move is None or move_key < best_move[0]):
                    best_move = (move_key, trial)

        if best_move is None:
            break

        best_score = best_move[0][0]
        selected = best_move[1]
        iterations += 1

    # Stable assignment of program instances to optimized cells.
    selected.sort(key=lambda c: (c["row"], c["col"], c["segment"]))
    placements = _build_placements(items, selected)

    return placements, selected, {
        "baseline_objective": dispersion_objective(baseline_cells),
        "optimized_objective": best_score,
        "iterations": iterations,
        "single_swap_local_optimum": True,
    }
