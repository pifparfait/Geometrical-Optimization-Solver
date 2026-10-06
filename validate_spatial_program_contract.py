from pathlib import Path

from src.spatial_program_contract import (
    load_spatial_program,
    summarize_spatial_program,
)


INPUT = Path("data/external/ryan/building_use_example.json")


def fmt(value: float) -> str:
    return f"{value:,.3f}"


def main() -> None:
    payload = load_spatial_program(INPUT)
    summary = summarize_spatial_program(payload)

    print("============================================================")
    print("VOLPE V0.4a — SPATIAL PROGRAM CONTRACT")
    print("RYAN -> PARFAIT")
    print("============================================================")
    print()
    print(f"input                 : {INPUT}")
    print(f"programs              : {summary['program_count']}")
    print()
    print("DECISION OWNERSHIP")
    print(f"what                  : {summary['what']}")
    print(f"how much              : {summary['how_much']}")
    print(f"typology              : {summary['typology']}")
    print(f"where                 : {summary['where']}")
    print(f"level                 : {summary['level']}")
    print()
    print("PROGRAM TYPOLOGIES")

    for location in (
        "open_space",
        "podium",
        "tower",
        "podium_and_tower",
    ):
        count = summary["location_counts"].get(location, 0)
        print(f"{location:<22}: {count}")

    print()
    print("FIXED PROGRAM AREA")
    print(
        f"open space            : "
        f"{fmt(summary['open_space_area_sqft'])} sqft"
    )
    print(
        f"podium                : "
        f"{fmt(summary['podium_area_sqft'])} sqft"
    )
    print(
        f"tower                 : "
        f"{fmt(summary['tower_area_sqft'])} sqft"
    )
    print(
        f"total program         : "
        f"{fmt(summary['total_program_area_sqft'])} sqft"
    )

    print()
    print("SCOPE")
    print("economic optimization : OUT OF SCOPE / RYAN")
    print("program selection     : OUT OF SCOPE / RYAN")
    print("spatial capacity      : NOT YET APPLIED")
    print("spatial optimization  : NOT EXECUTED")
    print()
    print("STATUS                : SPATIAL_PROGRAM_READY")
    print("============================================================")


if __name__ == "__main__":
    main()
