#!/usr/bin/env python3
import json
from pathlib import Path
from src.economic_formulation import profit_accounting, rows_from_contract

ROOT = Path(__file__).resolve().parent
with (ROOT / "data" / "mock" / "ryan_economic_placeholder.json").open("r", encoding="utf-8") as f:
    contract = json.load(f)
rows = rows_from_contract(contract)

# Unit test only: q=1 in each row's explicitly declared basis.
# This is not a planning scenario and is not an optimizer decision.
q_test = {row.amenity_type: 1.0 for row in rows}
basis_test = {row.amenity_type: row.basis_unit for row in rows}
observed = profit_accounting(rows, q_test, basis_test)
expected = sum(row.profit_usd for row in rows)
assert observed == expected

first = rows[0]
bad_basis = dict(basis_test)
bad_basis[first.amenity_type] = "__INTENTIONAL_MISMATCH__"
try:
    profit_accounting(rows, q_test, bad_basis)
except ValueError:
    mismatch_gate = "PASS"
else:
    raise AssertionError("Basis mismatch was not rejected")

print("VOLPE V0.3b — ECONOMIC FORMULATION CONTRACT")
print(f"economic rows       : {len(rows)}")
print("profit identity     : PASS")
print(f"basis mismatch gate : {mismatch_gate}")
print("quantity semantics  : ENDOGENOUS / SYMBOLIC")
print("sqft spatial use    : NOT YET")
print("optimizer changed   : NO")
print("optimization run    : NO")
print("weights/scaling     : NOT DEFINED")
print("STATUS              : ECONOMIC_FORMULATION_READY")
