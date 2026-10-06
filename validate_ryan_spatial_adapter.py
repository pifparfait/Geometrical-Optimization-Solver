import math

from src.ryan_spatial_adapter import load_ryan_spatial_demands


PROGRAM_PATH = "data/external/ryan/building_use_example.json"


def main() -> None:
    demands, report = load_ryan_spatial_demands(PROGRAM_PATH)

    print("============================================================")
    print("VOLPE V0.4e — RYAN -> SPATIAL SOLVER ADAPTER")
    print("PROGRAM TRANSFORMATION ONLY | NO OPTIMIZATION")
    print("============================================================")
    print()
    print(f"source programs        : {report['source_program_count']}")
    print(f"solver demands         : {report['solver_demand_count']}")
    print()
    print(
        f"source total           : "
        f"{report['source_total_area_sqft']:,.3f} sqft"
    )
    print(
        f"solver total           : "
        f"{report['solver_total_area_sqft']:,.3f} sqft"
    )
    print()

    areas = report["solver_area_by_typology_sqft"]

    print(f"open space             : {areas['open_space']:,.3f} sqft")
    print(f"podium                 : {areas['podium']:,.3f} sqft")
    print(f"tower                  : {areas['tower']:,.3f} sqft")

    print()
    print("MIXED TYPOLOGY EXPANSION")

    mixed = [
        d for d in demands
        if d.program_id.startswith("general_office::")
    ]

    for demand in mixed:
        print(
            f"{demand.program_id:<28}: "
            f"{demand.area_sqft:,.3f} sqft"
        )

    if report["source_program_count"] != 10:
        raise AssertionError("Expected 10 Ryan source programs")

    if report["solver_demand_count"] != 11:
        raise AssertionError("Expected 11 solver demands")

    if len(mixed) != 2:
        raise AssertionError(
            "general_office must expand into exactly two demands"
        )

    mixed_map = {
        d.program_id: d.area_sqft
        for d in mixed
    }

    if not math.isclose(
        mixed_map["general_office::podium"],
        16000.0,
        abs_tol=1e-6,
    ):
        raise AssertionError("Unexpected office podium area")

    if not math.isclose(
        mixed_map["general_office::tower"],
        29296.303427156818,
        abs_tol=1e-6,
    ):
        raise AssertionError("Unexpected office tower area")

    if not math.isclose(
        report["source_total_area_sqft"],
        report["solver_total_area_sqft"],
        rel_tol=1e-9,
        abs_tol=1e-6,
    ):
        raise AssertionError("Total program area was not conserved")

    if not math.isclose(
        areas["open_space"],
        2500.0,
        abs_tol=1e-6,
    ):
        raise AssertionError("Unexpected open-space total")

    if not math.isclose(
        areas["podium"],
        20000.0,
        abs_tol=1e-6,
    ):
        raise AssertionError("Unexpected podium total")

    if not math.isclose(
        areas["tower"],
        584077.2969513389,
        abs_tol=1e-6,
    ):
        raise AssertionError("Unexpected tower total")

    print()
    print("AREA CONSERVATION      : PASS")
    print("TYPOLOGY CONSERVATION  : PASS")
    print("MIXED SPLIT            : PASS")
    print("RYAN QUANTITIES CHANGED: FALSE")
    print("CAPACITY INFERRED      : FALSE")
    print("OPTIMIZER EXECUTED     : FALSE")
    print("ADAPTER                : PASS")
    print("============================================================")


if __name__ == "__main__":
    main()
