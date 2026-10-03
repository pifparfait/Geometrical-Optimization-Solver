#!/usr/bin/env python3
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parent

REQUIRED = [
    ROOT / "src" / "economic_contract.py",
    ROOT / "src" / "economic_formulation.py",
    ROOT / "schemas" / "ryan_economic_input.schema.json",
    ROOT / "data" / "mock" / "ryan_economic_placeholder.json",
]
for path in REQUIRED:
    if not path.exists():
        raise SystemExit(f"ERROR: required V0.3a/V0.3b artifact missing: {path.relative_to(ROOT)}")

files = {
    ROOT / "docs" / "decision_capacity_contract_v0_3c.md": r'''# VOLPE V0.3c — Decision & Capacity Contract

## Status
This document defines the symbolic decision layer connecting the economic
formulation to the future joint VOLPE optimizer. It does **not** define a
physical square-foot-to-cell conversion and does **not** execute optimization.

## 1. Decision variable
For program type `a`, grid row `r`, column `c`, and level `l`:

    x[a,r,c,l] in {0,1}

`x=1` means program type `a` is assigned to that VOLPE spatial position and
level, subject to future feasibility rules. In V0.3c this is symbolic only.

## 2. Endogenous economic quantity
For each program type `a`, q[a] >= 0 denotes the economic quantity used by the
profit formulation. The relation is deliberately unresolved:

    q[a] = Psi_a(x)

The form of Psi depends on the economic basis and physical-capacity semantics.
V0.3c does not choose among per-facility, per-square-foot, per-unit, or other
bases.

## 3. Economic objective identity
Once q[a] is validly defined on the same basis as the economic input:

    P(q) = sum_a p[a] * q[a]

This identity does not by itself authorize optimization.

## 4. Spatial capacity gate
Ryan input contains `footprint_sqft`, but V0.3c has no sourced rule for:

    footprint_sqft -> VOLPE spatial capacity

Therefore V0.3c forbids:
- treating one amenity instance as one VOLPE cell;
- inferring cell area from approximate grid-point spacing;
- deriving floors, FAR, height, or capacity from absent data;
- consuming `footprint_sqft` as a solver constraint.

`footprint_sqft` is available data but is not yet spatially actionable.

## 5. Readiness states
- decision variables: DEFINED SYMBOLICALLY
- economic quantity: ENDOGENOUS / SYMBOLIC
- profit formulation: READY
- footprint sqft: AVAILABLE
- VOLPE capacity: UNRESOLVED
- sqft-to-cell mapping: BLOCKED
- joint optimization: BLOCKED BY CAPACITY CONTRACT
- optimizer changed: NO

## 6. What unlocks joint optimization
A later version may unlock spatial capacity only after an explicit, provenanced
rule defines how physical program demand consumes VOLPE capacity. The rule must
specify units and basis and must not be inferred from the placeholder fixture.

Objective normalization, livability/social utility, Pareto/weighted
multi-objective choices, and final solver technology are outside V0.3c.
''',

    ROOT / "src" / "decision_capacity_contract.py": r'''"""VOLPE V0.3c symbolic decision/capacity contract.

No solver variables are created here. This module records what is defined,
what remains unresolved, and the gate preventing unsourced sqft-to-cell
conversion from entering the optimizer.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class DecisionIndex:
    amenity_type: str
    row: int
    col: int
    level: int


@dataclass(frozen=True)
class CapacityReadiness:
    decision_variables: str = "DEFINED_SYMBOLICALLY"
    economic_quantity: str = "ENDOGENOUS_SYMBOLIC"
    profit_formulation: str = "READY"
    footprint_sqft: str = "AVAILABLE"
    volpe_capacity: str = "UNRESOLVED"
    sqft_to_cell_mapping: str = "BLOCKED"
    joint_optimization: str = "BLOCKED_BY_CAPACITY_CONTRACT"
    optimizer_changed: bool = False


READINESS = CapacityReadiness()


def symbolic_quantity_relation() -> str:
    return "q_a = Psi_a(x)"


def require_spatial_capacity_rule(capacity_rule) -> None:
    if capacity_rule is None:
        raise ValueError(
            "Spatial capacity unresolved: no sourced sqft-to-VOLPE capacity "
            "rule is available. footprint_sqft must not be converted to cells."
        )


def assert_no_spatial_consumption(rows: Iterable[Dict]) -> Tuple[int, float]:
    rows = list(rows)
    total_sqft_field_value = sum(float(r["footprint_sqft"]) for r in rows)
    return len(rows), total_sqft_field_value
''',

    ROOT / "validate_decision_capacity_contract.py": r'''#!/usr/bin/env python3
import json
from pathlib import Path

from src.decision_capacity_contract import (
    READINESS,
    DecisionIndex,
    assert_no_spatial_consumption,
    require_spatial_capacity_rule,
    symbolic_quantity_relation,
)

ROOT = Path(__file__).resolve().parent
ECON = ROOT / "data" / "mock" / "ryan_economic_placeholder.json"
OPTIMIZER = ROOT / "src" / "optimizer.py"

with ECON.open("r", encoding="utf-8") as f:
    payload = json.load(f)
rows = payload["amenities"]

idx = DecisionIndex("cafe", 0, 0, 0)
assert idx.amenity_type == "cafe"
assert idx.row == 0 and idx.col == 0 and idx.level == 0

assert symbolic_quantity_relation() == "q_a = Psi_a(x)"

row_count, descriptive_sqft_sum = assert_no_spatial_consumption(rows)
assert row_count == len(rows)
assert descriptive_sqft_sum > 0

blocked = False
try:
    require_spatial_capacity_rule(None)
except ValueError:
    blocked = True
assert blocked, "Missing spatial capacity rule did not block execution"

assert READINESS.decision_variables == "DEFINED_SYMBOLICALLY"
assert READINESS.economic_quantity == "ENDOGENOUS_SYMBOLIC"
assert READINESS.profit_formulation == "READY"
assert READINESS.footprint_sqft == "AVAILABLE"
assert READINESS.volpe_capacity == "UNRESOLVED"
assert READINESS.sqft_to_cell_mapping == "BLOCKED"
assert READINESS.joint_optimization == "BLOCKED_BY_CAPACITY_CONTRACT"
assert READINESS.optimizer_changed is False
assert OPTIMIZER.exists()

print("VOLPE V0.3c — DECISION & CAPACITY CONTRACT")
print(f"economic rows         : {row_count}")
print("decision variables    : DEFINED SYMBOLICALLY")
print("economic quantity     : ENDOGENOUS / SYMBOLIC")
print("profit formulation    : READY")
print("footprint sqft        : AVAILABLE")
print("VOLPE capacity        : UNRESOLVED")
print("sqft -> cell mapping  : BLOCKED")
print("capacity fail-closed  : PASS")
print("joint optimization    : BLOCKED BY CAPACITY CONTRACT")
print("optimizer changed     : NO")
print("optimization run      : NO")
print("STATUS                : DECISION_MODEL_READY / SPATIAL_CAPACITY_PENDING")
''',
}

created = []
for path, content in files.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SystemExit(f"ERROR: refusing to overwrite existing file: {path.relative_to(ROOT)}")
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    created.append(path)

for p in created:
    print(f"CREATED: {p.relative_to(ROOT)}")
print()
print("V0.3c DECISION & CAPACITY CONTRACT SCAFFOLD: PASS")
print("No optimizer logic was changed.")
print("No sqft-to-VOLPE capacity conversion was introduced.")
print("No optimization was executed.")
