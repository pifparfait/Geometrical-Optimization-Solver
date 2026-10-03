from pathlib import Path

from src.economic_contract import load_json, validate_ryan_economic_contract

ROOT = Path(__file__).resolve().parent

payload = load_json(ROOT / "data" / "mock" / "ryan_economic_placeholder.json")
schema = load_json(ROOT / "schemas" / "ryan_economic_input.schema.json")
catalog = load_json(ROOT / "data" / "catalog" / "demo_buildable_use_data.json")

result = validate_ryan_economic_contract(payload, schema, catalog)

print("VOLPE V0.3a — RYAN ECONOMIC CONTRACT")
print(f"contract version : {result['contract_version']}")
print(f"currency         : {result['currency']}")
print(f"economic rows    : {result['rows']}")
print(f"catalog matches  : {result['catalog_matches']}")
print("schema           : PASS")
print("catalog mapping  : PASS")
print("spatial use      : NOT YET — no sqft-to-VOLPE capacity conversion assumed")
print("optimization     : NOT EXECUTED")
print("STATUS           : ECONOMIC_CONTRACT_READY")
