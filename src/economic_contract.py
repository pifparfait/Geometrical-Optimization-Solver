import json
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
        raise ValueError("Ryan economic schema validation failed:\n- " + "\n- ".join(formatted))

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
