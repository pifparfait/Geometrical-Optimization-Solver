from pathlib import Path

ROOT = Path.cwd()

required = [
    ROOT / ".gitignore",
    ROOT / "README.md",
    ROOT / "run_demo.py",
    ROOT / "src" / "optimizer.py",
    ROOT / "src" / "matti_adapter.py",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit(
        "Run this from the Geometrical-Optimization-Solver project root. Missing: "
        + ", ".join(missing)
    )

# Generated solver outputs are reproducible artifacts and should not be versioned.
gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
gitignore = [
    line for line in gitignore
    if not line.startswith("outputs/")
]
gitignore.append("outputs/")
(ROOT / ".gitignore").write_text("\n".join(gitignore).rstrip() + "\n", encoding="utf-8")

readme = """# Geometrical Optimization Solver

Small, reproducible geometry-optimization scaffold for the VOLPE development-program pipeline.

## Current milestone: V0.2

V0.2 is the first optimization demo built on the V0.1 end-to-end geometry baseline.

Pipeline:

```text
mock program demand
        |
37-type program catalog
        |
VOLPE valid site grid
        |
baseline 3D placement
        |
technical compactness optimization
        |
canonical solution
        |
Matti adapter
        |
development-program JSON
```

### What V0.2 optimizes

The technical objective is pairwise squared grid dispersion across occupied footprint cells:

```text
sum over i<j of ((row_i-row_j)^2 + (col_i-col_j)^2)
```

The search starts from the V0.1 baseline and performs deterministic single-cell swaps while
they strictly improve the objective. It stops at a 1-swap local optimum.

This objective is a technical geometry test only. It is **not** an urban-performance metric,
and V0.2 makes **no global optimality claim**.

### Current demo constraints

- placements use only valid VOLPE grid cells;
- `ground_level=true` is used as a temporary demo placement rule;
- flexible programs may be stacked vertically;
- vertical support is checked;
- Matti's current development-program schema is validated before output;
- no physical area is inferred from the approximately 22 m grid spacing;
- no FAR, height, cost, accessibility, population, or economic objective is used.

## Run

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the demo:

```bash
python run_demo.py
```

The current fixture should report a baseline objective of `560` and an optimized objective
of `20`, while preserving vertical support and schema validity.

## Inputs

- `data/catalog/demo_buildable_use_data.json` — current 37-type program catalog.
- `data/geometry/volpe_site_grid.json` — VOLPE 14x14 site-grid contract.
- `data/mock/ryan_program.json` — temporary upstream-interface fixture.
- `schemas/development-program.schema.json` — current Matti output schema.
- `schemas/development-programs.md` — current Matti development-program documentation.

## Outputs

Generated outputs are intentionally ignored by Git because they are reproducible.

```text
outputs/
├── baseline_solution.json
├── optimized_solution.json
├── canonical_solution.json
└── matti/
    ├── baseline/
    └── optimized/
```

`canonical_solution.json` is solver-owned. Matti JSON files are adapter outputs, not the
internal optimization representation.

## Version history

- `v0.1` — end-to-end horizontal + vertical geometry baseline, validated in the VOLPE viewer.
- `v0.2` — first deterministic compactness optimization demo, baseline-vs-optimized outputs,
  schema validation, vertical-support validation, and VOLPE viewer validation.

## Next scientific step

V0.2 proves that the geometry engine can optimize a controlled objective. The next formulation
should define which real spatial/urban signals belong in the objective and constraints before
adding solver complexity or claiming urban-performance meaning.
"""

(ROOT / "README.md").write_text(readme, encoding="utf-8")

print("UPDATED: .gitignore")
print("UPDATED: README.md")
print("V0.2 DOCUMENTATION FINALIZATION: PASS")
