# VOLPE Geometrical Optimization Solver — V0

A deliberately small, functional end-to-end scaffold:

`mock Ryan demand -> canonical geometry placement -> Matti development-program JSON -> schema validation`

V0 is **not** the scientific optimization model. It is an interface and geometry smoke test.

## 1. Create the virtual environment

From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Run

```bash
python run_demo.py
```

Expected final status:

```text
schema validation  : PASS
STATUS              : FEASIBLE_DEMO (no optimality claim)
```

## Inputs

- `data/catalog/demo_buildable_use_data.json` — the current 37-type catalog.
- `data/geometry/volpe_site_grid.json` — the 14×14 VOLPE site grid transcribed from Matti's supplied documentation.
- `data/mock/ryan_program.json` — temporary Ryan-interface fixture.
- `schemas/development-program.schema.json` — Matti's current schema.
- `schemas/development-programs.md` — Matti's current documentation.

## Outputs

- `outputs/canonical_solution.json` — solver-owned canonical solution.
- `outputs/matti/*.json` — one Matti-compatible development-program file per used segment.

## Deliberate V0 simplifications

- integer program instances only;
- one instance per valid grid cell;
- level 0 only;
- deterministic horizontal allocation;
- no inferred cell area;
- no FAR, height, cost, accessibility, or urban-performance objective;
- no claim of optimality.

The mock uses `cafe`, `restaurant`, `clinic`, and `library` because these names are present both
in the 37-type catalog and Matti's current 16-type schema. When Matti extends the schema, the
mock can be changed to any of the 37 program types without changing the canonical architecture.

When Ryan sends the real interface, replace only `data/mock/ryan_program.json` and, if necessary,
the small input adapter. Do not redesign the canonical solution around Ryan's serialization.
