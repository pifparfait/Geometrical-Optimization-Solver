from pathlib import Path
import json

ROOT = Path.cwd()

required = [
    ROOT / "README.md",
    ROOT / "requirements.txt",
    ROOT / "src",
    ROOT / "data" / "catalog" / "demo_buildable_use_data.json",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit(
        "Run this from the Geometrical-Optimization-Solver project root. Missing: "
        + ", ".join(missing)
    )

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "ryan-economic-input.schema.json",
    "title": "Ryan Economic Input Contract",
    "description": "Placeholder economic interface for VOLPE V0.3a. Footprint and profit refer to the same explicit basis/unit.",
    "type": "object",
    "required": ["contract_version", "currency", "amenities"],
    "properties": {
        "contract_version": {"const": "0.3a"},
        "currency": {"const": "USD"},
        "amenities": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["amenity_type", "footprint_sqft", "profit_usd", "basis_unit"],
                "additionalProperties": False,
                "properties": {
                    "amenity_type": {"type": "string", "minLength": 1},
                    "footprint_sqft": {"type": "number", "exclusiveMinimum": 0},
                    "profit_usd": {"type": "number"},
                    "basis_unit": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Decision basis shared by footprint and profit, e.g. per_amenity_instance."
                    }
                }
            }
        }
    },
    "additionalProperties": False
}

schema_path = ROOT / "schemas" / "ryan_economic_input.schema.json"
schema_path.parent.mkdir(parents=True, exist_ok=True)
schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

fixture = {
    "contract_version": "0.3a",
    "currency": "USD",
    "amenities": [
        {"amenity_type": "cafe", "footprint_sqft": 1.0, "profit_usd": 1.0, "basis_unit": "DEMO_PLACEHOLDER_PER_INSTANCE"},
        {"amenity_type": "restaurant", "footprint_sqft": 1.0, "profit_usd": 1.0, "basis_unit": "DEMO_PLACEHOLDER_PER_INSTANCE"},
        {"amenity_type": "clinic", "footprint_sqft": 1.0, "profit_usd": 1.0, "basis_unit": "DEMO_PLACEHOLDER_PER_INSTANCE"},
        {"amenity_type": "library", "footprint_sqft": 1.0, "profit_usd": 1.0, "basis_unit": "DEMO_PLACEHOLDER_PER_INSTANCE"}
    ]
}

fixture_path = ROOT / "data" / "mock" / "ryan_economic_placeholder.json"
fixture_path.parent.mkdir(parents=True, exist_ok=True)
fixture_path.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")

warning_path = ROOT / "data" / "mock" / "RYAN_ECONOMIC_PLACEHOLDER_README.txt"
warning_path.write_text(
    "V0.3a CONTRACT TEST ONLY.\n"
    "The numeric values in ryan_economic_placeholder.json are neutral dummy values (1.0) "
    "used only to test parsing and validation. They are NOT economic or physical assumptions "
    "and MUST NOT be used for optimization conclusions.\n",
    encoding="utf-8"
)

module = '''import json
from pathlib import Path

from jsonschema import Draft202012Validator


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def catalog_types(catalog):
    return {item["amenity_type"] for item in catalog["amenities"]}


def validate_ryan_economic_contract(payload, schema, catalog):
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        formatted = []
        for error in errors:
            location = ".".join(str(x) for x in error.path) or "<root>"
            formatted.append(f"{location}: {error.message}")
        raise ValueError("Ryan economic schema validation failed:\\n- " + "\\n- ".join(formatted))

    known = catalog_types(catalog)
    seen = set()

    for row in payload["amenities"]:
        amenity = row["amenity_type"]
        if amenity not in known:
            raise ValueError(f"Ryan economic contract contains unknown amenity_type: {amenity}")
        if amenity in seen:
            raise ValueError(f"Ryan economic contract contains duplicate amenity_type: {amenity}")
        seen.add(amenity)

    return {
        "rows": len(payload["amenities"]),
        "catalog_matches": len(seen),
        "currency": payload["currency"],
        "contract_version": payload["contract_version"],
    }
'''
module_path = ROOT / "src" / "economic_contract.py"
module_path.write_text(module, encoding="utf-8")

validator_script = '''from pathlib import Path

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
'''
validator_path = ROOT / "validate_economic_contract.py"
validator_path.write_text(validator_script, encoding="utf-8")

print("CREATED:", schema_path.relative_to(ROOT))
print("CREATED:", fixture_path.relative_to(ROOT))
print("CREATED:", warning_path.relative_to(ROOT))
print("CREATED:", module_path.relative_to(ROOT))
print("CREATED:", validator_path.relative_to(ROOT))
print()
print("V0.3a ECONOMIC CONTRACT SCAFFOLD: PASS")
print("No optimizer logic was changed.")
