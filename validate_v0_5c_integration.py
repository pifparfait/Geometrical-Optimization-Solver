from __future__ import annotations

import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parent

CANONICAL = (
    ROOT
    / "outputs"
    / "v0_5c"
    / "canonical_3d_solution.json"
)

MATTI = (
    ROOT
    / "outputs"
    / "v0_5c"
    / "matti"
    / "v0-5c-synthetic-segment-2.json"
)

SCHEMA = (
    ROOT
    / "schemas"
    / "development-program.schema.json"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    canonical = load(CANONICAL)
    matti = load(MATTI)
    schema = load(SCHEMA)

    result = canonical["solver_result"]
    demands = canonical["demands"]

    assert result["status"] == "OPTIMAL"

    geometry = result["geometry"]
    allocations = result["allocations"]

    built = [
        g
        for g in geometry
        if g["form"] in {"built_5_story", "tower"}
    ]

    opened = [
        g
        for g in geometry
        if g["form"] == "open_space"
    ]

    unused = [
        g
        for g in geometry
        if g["form"] == "unused"
    ]

    # ---------------------------------------------------------
    # 1. EXACT PROGRAM AREA CONSERVATION
    # ---------------------------------------------------------
    expected = {
        d["program_id"]: float(d["area_sqft"])
        for d in demands
    }

    observed = {
        program_id: 0.0
        for program_id in expected
    }

    for a in allocations:
        observed[a["program_id"]] += float(a["area_sqft"])

    for program_id in expected:
        assert math.isclose(
            expected[program_id],
            observed[program_id],
            rel_tol=1e-9,
            abs_tol=1e-5,
        ), (
            program_id,
            expected[program_id],
            observed[program_id],
        )

    expected_built_area = sum(
        d["area_sqft"]
        for d in demands
        if d["kind"] == "built"
    )

    expected_open_area = sum(
        d["area_sqft"]
        for d in demands
        if d["kind"] == "open_space"
    )

    observed_built_area = sum(
        a["area_sqft"]
        for a in allocations
        if next(
            d["kind"]
            for d in demands
            if d["program_id"] == a["program_id"]
        ) == "built"
    )

    observed_open_area = sum(
        a["area_sqft"]
        for a in allocations
        if next(
            d["kind"]
            for d in demands
            if d["program_id"] == a["program_id"]
        ) == "open_space"
    )

    assert math.isclose(
        expected_built_area,
        observed_built_area,
        rel_tol=1e-9,
        abs_tol=1e-5,
    )

    assert math.isclose(
        expected_open_area,
        observed_open_area,
        rel_tol=1e-9,
        abs_tol=1e-5,
    )

    # ---------------------------------------------------------
    # 2. CERTIFIED SYNTHETIC GEOMETRY
    # ---------------------------------------------------------
    built_floor_plates = sum(
        int(g["stories"])
        for g in built
    )

    assert built_floor_plates == 186
    assert result["built_floor_plates"] == 186

    assert len(opened) == 4
    assert result["open_cells"] == 4

    assert len(built) == 7
    assert len(unused) == 13

    assert expected_built_area == 100_000.0
    assert expected_open_area == 2_000.0

    # ---------------------------------------------------------
    # 3. MATTI SCHEMA
    # ---------------------------------------------------------
    validator = Draft202012Validator(schema)

    errors = sorted(
        validator.iter_errors(matti),
        key=lambda e: list(e.path),
    )

    if errors:
        details = "\n".join(
            f"- {'/'.join(map(str, e.path))}: {e.message}"
            for e in errors
        )
        raise AssertionError(
            "Matti schema validation failed:\n" + details
        )

    # ---------------------------------------------------------
    # 4. EXACT FOOTPRINT EQUIVALENCE
    # ---------------------------------------------------------
    canonical_footprints = {
        (g["segment"], g["row"], g["col"])
        for g in built
    }

    matti_footprints = set()

    for building in matti["buildings"]:
        assert len(building["footprint"]) == 1

        cell = building["footprint"][0]

        matti_footprints.add(
            (
                matti["segment"],
                cell["row"],
                cell["col"],
            )
        )

    assert matti_footprints == canonical_footprints

    # ---------------------------------------------------------
    # 5. EXACT HEIGHT EQUIVALENCE
    # ---------------------------------------------------------
    canonical_heights = {
        (g["segment"], g["row"], g["col"]): int(g["stories"])
        for g in built
    }

    matti_heights = {}

    for building in matti["buildings"]:
        cell = building["footprint"][0]

        floors = building["floors"]

        assert len(floors) == 1

        levels = floors[0]["levels"]

        if len(levels) == 1:
            stories = 1
        else:
            first, last = levels
            assert first == 0
            stories = last + 1

        key = (
            matti["segment"],
            cell["row"],
            cell["col"],
        )

        matti_heights[key] = stories

    assert matti_heights == canonical_heights

    # ---------------------------------------------------------
    # 6. RENDERING CONVENTION ONLY
    # ---------------------------------------------------------
    canonical_by_cell = {
        (g["segment"], g["row"], g["col"]): g
        for g in built
    }

    for building in matti["buildings"]:
        cell = building["footprint"][0]

        key = (
            matti["segment"],
            cell["row"],
            cell["col"],
        )

        canonical_cell = canonical_by_cell[key]

        if canonical_cell["form"] == "built_5_story":
            assert building["type"] == "podium"

        elif canonical_cell["form"] == "tower":
            assert building["type"] == "tower"

        else:
            raise AssertionError(
                f"Unexpected canonical form: "
                f"{canonical_cell['form']}"
            )

    # ---------------------------------------------------------
    # REPORT
    # ---------------------------------------------------------
    print("=" * 72)
    print("VOLPE V0.5c — INTEGRATION CERTIFICATION")
    print("=" * 72)
    print("SOLVER STATUS            : OPTIMAL")
    print("PROGRAM AREA CONSERVATION: PASS")
    print("BUILT AREA               : 100,000.000 sqft — PASS")
    print("OPEN AREA                :   2,000.000 sqft — PASS")
    print("BUILT FLOOR PLATES       : 186 — PASS")
    print("BUILT FOOTPRINT CELLS    : 7 — PASS")
    print("OPEN CELLS               : 4 — PASS")
    print("UNUSED CELLS             : 13 — PASS")
    print("MATTI JSON SCHEMA        : PASS")
    print("FOOTPRINT EQUIVALENCE    : PASS")
    print("HEIGHT EQUIVALENCE       : PASS")
    print("PROGRAM SEMANTICS MAPPED : FALSE")
    print("5-STORY PODIUM MAPPING   : VISUALIZATION ONLY")
    print("RESULT                    : CERTIFIED")
    print("=" * 72)


if __name__ == "__main__":
    main()
