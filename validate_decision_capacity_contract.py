#!/usr/bin/env python3
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
