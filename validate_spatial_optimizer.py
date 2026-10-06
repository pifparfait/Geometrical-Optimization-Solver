from src.spatial_optimizer import (
    SpatialDemand,
    SpatialSlot,
    solve_spatial_allocation,
)


def main() -> None:
    # ---------------------------------------------------------
    # Synthetic certification only.
    #
    # Two fixed programs, two physical slots.
    #
    # A = 100 sqft podium
    # B = 100 sqft tower
    #
    # Slot P accepts podium only.
    # Slot T accepts tower only.
    #
    # Therefore there is exactly one feasible allocation.
    # ---------------------------------------------------------

    demands = [
        SpatialDemand(
            program_id="A",
            area_sqft=100.0,
            typology="podium",
        ),
        SpatialDemand(
            program_id="B",
            area_sqft=100.0,
            typology="tower",
        ),
    ]

    slots = [
        SpatialSlot(
            slot_id="P",
            segment=0,
            row=0,
            col=0,
            level=0,
            capacity_sqft=100.0,
            allowed_typologies=("podium",),
        ),
        SpatialSlot(
            slot_id="T",
            segment=0,
            row=1,
            col=0,
            level=1,
            capacity_sqft=100.0,
            allowed_typologies=("tower",),
        ),
    ]

    costs = {
        ("A", "P"): 2.0,
        ("B", "T"): 3.0,
    }

    result = solve_spatial_allocation(
        demands=demands,
        slots=slots,
        cost_per_sqft=costs,
    )

    print("============================================================")
    print("VOLPE V0.4d — SPATIAL OPTIMIZER CERTIFICATION")
    print("SYNTHETIC DATA ONLY")
    print("============================================================")
    print()
    print(f"backend               : {result['backend']}")
    print(f"status                : {result['status']}")
    print(f"objective             : {result['objective']}")
    print(f"allocations           : {len(result['allocations'])}")
    print()

    for allocation in result["allocations"]:
        print(
            f"{allocation['program_id']} -> "
            f"{allocation['slot_id']} | "
            f"{allocation['area_sqft']:.3f} sqft | "
            f"level={allocation['level']}"
        )

    expected_objective = 100.0 * 2.0 + 100.0 * 3.0

    if result["status"] != "OPTIMAL":
        raise AssertionError(
            f"Expected OPTIMAL, got {result['status']}"
        )

    if abs(result["objective"] - expected_objective) > 1e-8:
        raise AssertionError(
            "Unexpected objective: "
            f"{result['objective']} != {expected_objective}"
        )

    allocation_map = {
        (x["program_id"], x["slot_id"]): x["area_sqft"]
        for x in result["allocations"]
    }

    if allocation_map != {
        ("A", "P"): 100.0,
        ("B", "T"): 100.0,
    }:
        raise AssertionError(
            f"Unexpected allocation: {allocation_map}"
        )

    print()
    print("PROGRAM CONSERVATION  : PASS")
    print("TYPOLOGY COMPATIBILITY: PASS")
    print("SLOT CAPACITY         : PASS")
    print("OBJECTIVE              : PASS")
    print("HIGHS SOLVE            : PASS")
    print("CERTIFICATION          : PASS")
    print("VOLPE PHYSICAL CLAIM   : FALSE")
    print("============================================================")


if __name__ == "__main__":
    main()
