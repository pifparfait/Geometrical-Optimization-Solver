from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import coo_matrix


@dataclass(frozen=True)
class ProgramDemand3D:
    program_id: str
    area_sqft: float
    kind: str  # open_space | built


@dataclass(frozen=True)
class Cell3D:
    cell_id: str
    segment: int
    row: int
    col: int


def solve_3d_staged(
    demands: Sequence[ProgramDemand3D],
    cells: Sequence[Cell3D],
    *,
    cell_area_sqft: float,
    podium_stories: int = 5,
    max_stories: int = 30,
) -> Dict:

    if not cells:
        raise ValueError("At least one cell is required")
    if cell_area_sqft <= 0:
        raise ValueError("cell_area_sqft must be positive")
    if podium_stories < 1:
        raise ValueError("podium_stories must be >= 1")
    if max_stories < podium_stories:
        raise ValueError(
            "max_stories must be >= podium_stories"
        )

    for d in demands:
        if d.area_sqft <= 0:
            raise ValueError(
                f"{d.program_id}: area must be positive"
            )
        if d.kind not in {"open_space", "built"}:
            raise ValueError(
                f"{d.program_id}: unsupported kind {d.kind}"
            )

    built_demands = [
        d for d in demands if d.kind == "built"
    ]
    open_demands = [
        d for d in demands if d.kind == "open_space"
    ]

    total_built = sum(d.area_sqft for d in built_demands)
    total_open = sum(d.area_sqft for d in open_demands)

    # =========================================================
    # STAGE 1 — GEOMETRY MILP
    #
    # b[c] = built footprint
    # o[c] = open-space footprint
    # h[c] = integer number of built floor plates
    #
    # No amenity identity appears in this MILP.
    # =========================================================

    n = len(cells)

    # Variable layout:
    # [b_0 ... b_n-1,
    #  o_0 ... o_n-1,
    #  h_0 ... h_n-1]

    def ib(i: int) -> int:
        return i

    def io(i: int) -> int:
        return n + i

    def ih(i: int) -> int:
        return 2 * n + i

    nv = 3 * n

    # Stage-1A objective:
    # minimize total active built floor plates only.
    #
    # Do not emulate lexicographic optimization using large
    # numerical weights. That approach can interact with MILP
    # relative-gap tolerances as problem scale increases.
    c_height = np.zeros(nv, dtype=float)

    for i in range(n):
        c_height[ih(i)] = 1.0

    lb = np.zeros(nv, dtype=float)
    ub = np.zeros(nv, dtype=float)

    for i in range(n):
        ub[ib(i)] = 1.0
        ub[io(i)] = 1.0
        ub[ih(i)] = float(max_stories)

    integrality = np.ones(nv, dtype=int)

    rows: List[Dict[int, float]] = []
    row_lb: List[float] = []
    row_ub: List[float] = []

    def add_row(
        coeffs: Dict[int, float],
        lower: float,
        upper: float,
    ) -> None:
        rows.append(coeffs)
        row_lb.append(lower)
        row_ub.append(upper)

    for i in range(n):
        # open OR built, never both
        add_row(
            {
                ib(i): 1.0,
                io(i): 1.0,
            },
            -np.inf,
            1.0,
        )

        # h <= Hmax * b
        add_row(
            {
                ih(i): 1.0,
                ib(i): -float(max_stories),
            },
            -np.inf,
            0.0,
        )

        # h >= podium_stories * b
        add_row(
            {
                ih(i): 1.0,
                ib(i): -float(podium_stories),
            },
            0.0,
            np.inf,
        )

    # Enough total built floor area.
    if total_built > 0:
        add_row(
            {
                ih(i): cell_area_sqft
                for i in range(n)
            },
            total_built,
            np.inf,
        )

    # Enough horizontal open-space area.
    if total_open > 0:
        add_row(
            {
                io(i): cell_area_sqft
                for i in range(n)
            },
            total_open,
            np.inf,
        )

    rr: List[int] = []
    cc: List[int] = []
    vv: List[float] = []

    for r, coeffs in enumerate(rows):
        for j, value in coeffs.items():
            rr.append(r)
            cc.append(j)
            vv.append(value)

    A = coo_matrix(
        (vv, (rr, cc)),
        shape=(len(rows), nv),
    ).tocsr()

    base_constraint = LinearConstraint(
        A,
        np.asarray(row_lb, dtype=float),
        np.asarray(row_ub, dtype=float),
    )

    # ---------------------------------------------------------
    # STAGE 1A — MINIMIZE BUILT FLOOR PLATES
    # ---------------------------------------------------------

    height_result = milp(
        c=c_height,
        integrality=integrality,
        bounds=Bounds(lb, ub),
        constraints=base_constraint,
        options={
            "disp": False,
            "mip_rel_gap": 0.0,
        },
    )

    if not height_result.success:
        return {
            "status": (
                "INFEASIBLE"
                if height_result.status == 2
                else "SOLVER_FAILURE"
            ),
            "stage": "GEOMETRY_HEIGHT_MILP",
            "solver_status": int(height_result.status),
            "message": str(height_result.message),
        }

    optimal_floor_plates = int(
        round(
            sum(
                height_result.x[ih(i)]
                for i in range(n)
            )
        )
    )

    # ---------------------------------------------------------
    # STAGE 1B — FIX HEIGHT OPTIMUM, MINIMIZE FOOTPRINT
    # ---------------------------------------------------------

    footprint_row = np.zeros(nv, dtype=float)

    for i in range(n):
        footprint_row[ih(i)] = 1.0

    fixed_height = LinearConstraint(
        footprint_row.reshape(1, -1),
        np.asarray(
            [float(optimal_floor_plates)],
            dtype=float,
        ),
        np.asarray(
            [float(optimal_floor_plates)],
            dtype=float,
        ),
    )

    c_footprint = np.zeros(nv, dtype=float)

    for i in range(n):
        c_footprint[ib(i)] = 1.0
        c_footprint[io(i)] = 1.0

    geometry_result = milp(
        c=c_footprint,
        integrality=integrality,
        bounds=Bounds(lb, ub),
        constraints=[
            base_constraint,
            fixed_height,
        ],
        options={
            "disp": False,
            "mip_rel_gap": 0.0,
        },
    )

    if not geometry_result.success:
        return {
            "status": "SOLVER_FAILURE",
            "stage": "GEOMETRY_FOOTPRINT_MILP",
            "solver_status": int(geometry_result.status),
            "message": str(geometry_result.message),
        }

    gx = geometry_result.x

    geometry = []
    built_slots: List[Tuple[str, int]] = []
    open_slots: List[str] = []

    for i, cell in enumerate(cells):
        built = gx[ib(i)] > 0.5
        opened = gx[io(i)] > 0.5
        height = int(round(gx[ih(i)]))

        if opened:
            form = "open_space"
            stories = 0
            open_slots.append(cell.cell_id)

        elif built:
            # 5 stories is physically built but architecturally
            # ambiguous under the current team rules:
            # podium = 5, tower = 5-30.
            #
            # Do not invent a podium/tower label at exactly 5.
            form = (
                "built_5_story"
                if height == podium_stories
                else "tower"
            )
            stories = height

            for level in range(height):
                built_slots.append(
                    (cell.cell_id, level)
                )

        else:
            form = "unused"
            stories = 0

        geometry.append(
            {
                "cell_id": cell.cell_id,
                "segment": cell.segment,
                "row": cell.row,
                "col": cell.col,
                "form": form,
                "stories": stories,
            }
        )

    # =========================================================
    # STAGE 2 — PROGRAM ALLOCATION LP
    #
    # Geometry is now fixed.
    # Allocate exact Ryan/program areas into valid slots.
    # =========================================================

    allocations: List[Dict] = []

    def allocate_lp(
        program_demands: Sequence[ProgramDemand3D],
        slots: Sequence,
        *,
        open_space: bool,
    ) -> Tuple[bool, List[Dict]]:

        if not program_demands:
            return True, []

        if not slots:
            return False, []

        nd = len(program_demands)
        ns = len(slots)
        nvars = nd * ns

        def idx(d: int, s: int) -> int:
            return d * ns + s

        # Neutral zero objective.
        # HiGHS solves this as a feasibility LP.
        obj = np.zeros(nvars, dtype=float)

        A_eq = []
        b_eq = []

        # Exact program conservation.
        for d_i, demand in enumerate(program_demands):
            row = np.zeros(nvars, dtype=float)

            for s_i in range(ns):
                row[idx(d_i, s_i)] = 1.0

            A_eq.append(row)
            b_eq.append(demand.area_sqft)

        A_ub = []
        b_ub = []

        # Per-slot capacity.
        for s_i in range(ns):
            row = np.zeros(nvars, dtype=float)

            for d_i in range(nd):
                row[idx(d_i, s_i)] = 1.0

            A_ub.append(row)
            b_ub.append(cell_area_sqft)

        lp = linprog(
            c=obj,
            A_ub=np.asarray(A_ub, dtype=float),
            b_ub=np.asarray(b_ub, dtype=float),
            A_eq=np.asarray(A_eq, dtype=float),
            b_eq=np.asarray(b_eq, dtype=float),
            bounds=(0.0, None),
            method="highs",
        )

        if not lp.success:
            return False, []

        out: List[Dict] = []

        for d_i, demand in enumerate(program_demands):
            for s_i, slot in enumerate(slots):
                value = float(lp.x[idx(d_i, s_i)])

                if value <= 1e-7:
                    continue

                if open_space:
                    cell_id = slot
                    level = 0
                else:
                    cell_id, level = slot

                out.append(
                    {
                        "program_id": demand.program_id,
                        "cell_id": cell_id,
                        "level": level,
                        "area_sqft": value,
                    }
                )

        return True, out

    ok_built, built_allocations = allocate_lp(
        built_demands,
        built_slots,
        open_space=False,
    )

    if not ok_built:
        return {
            "status": "SOLVER_FAILURE",
            "stage": "BUILT_ALLOCATION_LP",
        }

    ok_open, open_allocations = allocate_lp(
        open_demands,
        open_slots,
        open_space=True,
    )

    if not ok_open:
        return {
            "status": "SOLVER_FAILURE",
            "stage": "OPEN_ALLOCATION_LP",
        }

    allocations.extend(built_allocations)
    allocations.extend(open_allocations)

    return {
        "status": "OPTIMAL",
        "geometry_status": "OPTIMAL",
        "allocation_status": "FEASIBLE",
        "geometry_objective": {
            "floor_plates": int(optimal_floor_plates),
            "footprint_cells": int(
                round(geometry_result.fun)
            ),
        },
        "cell_area_sqft": float(cell_area_sqft),
        "podium_stories": int(podium_stories),
        "max_stories": int(max_stories),
        "built_floor_plates": len(built_slots),
        "open_cells": len(open_slots),
        "geometry": geometry,
        "allocations": allocations,
    }
