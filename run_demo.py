from pathlib import Path
import json
from jsonschema import Draft202012Validator

from src.optimizer import solve
from src.matti_adapter import to_matti_programs

ROOT = Path(__file__).resolve().parent
RYAN = ROOT / "data" / "mock" / "ryan_program.json"
SITE = ROOT / "data" / "geometry" / "volpe_site_grid.json"
CATALOG = ROOT / "data" / "catalog" / "demo_buildable_use_data.json"
SCHEMA = ROOT / "schemas" / "development-program.schema.json"
OUT = ROOT / "outputs"
MATTI_OUT = OUT / "matti"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_vertical_support(placements):
    occupied = {(p["segment"], p["row"], p["col"], p["level"]) for p in placements}
    for p in placements:
        if p["level"] > 0:
            below = (p["segment"], p["row"], p["col"], p["level"] - 1)
            if below not in occupied:
                raise ValueError(f"Unsupported vertical placement: {p}")
    return True


def main():
    ryan = load(RYAN)
    site = load(SITE)
    catalog = load(CATALOG)
    schema = load(SCHEMA)

    catalog_types = {a["amenity_type"] for a in catalog["amenities"]}
    requested_types = {x["program_type"] for x in ryan["program"]}
    unknown = requested_types - catalog_types
    if unknown:
        raise ValueError(f"Ryan input contains types not in catalog: {sorted(unknown)}")

    placements = solve(ryan["program"], site["valid_cells"], catalog)
    validate_vertical_support(placements)

    canonical = {
        "scenario_id": ryan["scenario_id"],
        "model": "volpe_geometry_optimizer_v0_1",
        "status": "FEASIBLE_DEMO",
        "scientific_optimality_claim": False,
        "assumptions": [
            "V0.1 is an interface/geometry test only.",
            "Integer program instances only.",
            "ground_level=true is used as a temporary demo placement rule.",
            "Flexible programs may be stacked vertically.",
            "No physical area is inferred from the approximately 22 m grid spacing.",
            "No FAR, height, cost, accessibility, or urban-performance objective is used."
        ],
        "placements": placements
    }

    OUT.mkdir(exist_ok=True)
    MATTI_OUT.mkdir(parents=True, exist_ok=True)
    for old in MATTI_OUT.glob("*.json"):
        old.unlink()

    (OUT / "canonical_solution.json").write_text(
        json.dumps(canonical, indent=2), encoding="utf-8"
    )

    matti_programs = to_matti_programs(ryan["scenario_id"], placements)
    validator = Draft202012Validator(schema)

    for program in matti_programs:
        errors = sorted(validator.iter_errors(program), key=lambda e: list(e.path))
        if errors:
            details = "\n".join(
                f"- {'/'.join(map(str, e.path))}: {e.message}" for e in errors
            )
            raise ValueError("Current Matti schema rejected generated output.\n" + details)

        path = MATTI_OUT / f"{ryan['scenario_id']}-segment-{program['segment']}.json"
        path.write_text(json.dumps(program, indent=2), encoding="utf-8")

    levels = sorted({p["level"] for p in placements})
    cells_used = {(p["segment"], p["row"], p["col"]) for p in placements}

    print("VOLPE GEOMETRY OPTIMIZER V0.1")
    print(f"catalog types      : {len(catalog_types)}")
    print(f"valid site cells   : {len(site['valid_cells'])}")
    print(f"program instances  : {len(placements)}")
    print(f"cells used         : {len(cells_used)}")
    print(f"levels used        : {levels}")
    print(f"segments generated : {[p['segment'] for p in matti_programs]}")
    print("vertical support   : PASS")
    print("schema validation  : PASS")
    print(f"canonical output   : {OUT / 'canonical_solution.json'}")
    print(f"Matti outputs      : {MATTI_OUT}")
    print("STATUS              : FEASIBLE_DEMO (no optimality claim)")


if __name__ == "__main__":
    main()
