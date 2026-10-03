from pathlib import Path
import json
import shutil
from jsonschema import Draft202012Validator

from src.optimizer import (
    baseline_solve,
    optimize_solve,
    dispersion_objective,
)
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


def validate_unique_ground_cells(placements):
    ground = [(p["segment"], p["row"], p["col"]) for p in placements if p["level"] == 0]
    if len(ground) != len(set(ground)):
        raise ValueError("Two level-0 program instances occupy the same footprint cell.")
    return True


def write_canonical(path, scenario_id, variant, placements, objective, metadata):
    payload = {
        "scenario_id": scenario_id,
        "model": "volpe_geometry_optimizer_v0_2",
        "variant": variant,
        "status": "BASELINE_DEMO" if variant == "baseline" else "OPTIMIZED_DEMO",
        "scientific_optimality_claim": False,
        "global_optimality_claim": False,
        "objective": {
            "name": "pairwise_squared_grid_dispersion",
            "sense": "minimize",
            "value": objective,
            "units": "grid_index_squared",
            "scope": "unique occupied footprint cells",
        },
        "assumptions": [
            "V0.2 is a technical geometry optimization demo.",
            "Integer program instances only.",
            "ground_level=true remains a temporary demo placement rule.",
            "Flexible programs may be stacked vertically.",
            "No physical area is inferred from the approximately 22 m grid spacing.",
            "The compactness objective is technical only and is not an urban-performance claim.",
            "No FAR, height, cost, accessibility, population, or economic objective is used.",
            "Optimized solution is a deterministic 1-swap local optimum; global optimality is not claimed.",
        ],
        "optimization_metadata": metadata,
        "placements": placements,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def validate_and_write_matti(schema, scenario_id, variant, placements):
    target = MATTI_OUT / variant
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    programs = to_matti_programs(scenario_id, placements, variant=variant)
    validator = Draft202012Validator(schema)

    for program in programs:
        errors = sorted(validator.iter_errors(program), key=lambda e: list(e.path))
        if errors:
            details = "\n".join(
                f"- {'/'.join(map(str, e.path))}: {e.message}" for e in errors
            )
            raise ValueError(
                f"Current Matti schema rejected {variant} output.\n{details}"
            )

        path = target / f"{scenario_id}-{variant}-segment-{program['segment']}.json"
        path.write_text(json.dumps(program, indent=2), encoding="utf-8")

    return programs, target


def fmt_cells(cells):
    return [
        f"s{c['segment']}:({c['row']},{c['col']})"
        for c in sorted(cells, key=lambda x: (x["row"], x["col"], x["segment"]))
    ]


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

    baseline, baseline_cells = baseline_solve(
        ryan["program"], site["valid_cells"], catalog
    )
    optimized, optimized_cells, meta = optimize_solve(
        ryan["program"], site["valid_cells"], catalog
    )

    for placements in (baseline, optimized):
        validate_vertical_support(placements)
        validate_unique_ground_cells(placements)

    baseline_score = dispersion_objective(baseline_cells)
    optimized_score = dispersion_objective(optimized_cells)

    if optimized_score > baseline_score:
        raise ValueError("Optimization regression: optimized score is worse than baseline.")

    improvement = (
        0.0 if baseline_score == 0
        else 100.0 * (baseline_score - optimized_score) / baseline_score
    )

    OUT.mkdir(exist_ok=True)
    MATTI_OUT.mkdir(parents=True, exist_ok=True)

    # Remove old V0/V0.1 flat Matti JSONs to avoid confusing them with V0.2 variants.
    for old in MATTI_OUT.glob("*.json"):
        old.unlink()

    write_canonical(
        OUT / "baseline_solution.json",
        ryan["scenario_id"],
        "baseline",
        baseline,
        baseline_score,
        {"source": "V0.1 round-robin baseline"},
    )
    write_canonical(
        OUT / "optimized_solution.json",
        ryan["scenario_id"],
        "optimized",
        optimized,
        optimized_score,
        meta,
    )

    # Keep canonical_solution.json as the current solver-owned solution.
    write_canonical(
        OUT / "canonical_solution.json",
        ryan["scenario_id"],
        "optimized",
        optimized,
        optimized_score,
        meta,
    )

    baseline_programs, baseline_dir = validate_and_write_matti(
        schema, ryan["scenario_id"], "baseline", baseline
    )
    optimized_programs, optimized_dir = validate_and_write_matti(
        schema, ryan["scenario_id"], "optimized", optimized
    )

    levels = sorted({p["level"] for p in optimized})

    print("VOLPE GEOMETRY OPTIMIZER V0.2")
    print(f"catalog types       : {len(catalog_types)}")
    print(f"valid site cells    : {len(site['valid_cells'])}")
    print(f"program instances   : {len(optimized)}")
    print(f"cells required      : {len(optimized_cells)}")
    print(f"levels used         : {levels}")
    print()
    print("BASELINE")
    print(f"objective            : {baseline_score}")
    print(f"cells                : {fmt_cells(baseline_cells)}")
    print()
    print("OPTIMIZED")
    print(f"objective            : {optimized_score}")
    print(f"cells                : {fmt_cells(optimized_cells)}")
    print(f"local-search moves   : {meta['iterations']}")
    print(f"improvement          : {improvement:.2f}%")
    print()
    print("vertical support     : PASS")
    print("schema validation    : PASS")
    print("global optimum claim : FALSE")
    print(f"baseline Matti       : {baseline_dir}")
    print(f"optimized Matti      : {optimized_dir}")
    print(f"canonical output     : {OUT / 'canonical_solution.json'}")
    print("STATUS               : OPTIMIZED_DEMO")


if __name__ == "__main__":
    main()
