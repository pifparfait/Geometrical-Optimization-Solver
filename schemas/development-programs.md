# Development programs

A development program says what is built on one segment of the Volpe site: the buildings,
where each stands, and what is on each floor. The map turns it into the development graph it
draws (floors stacked one storey apart, units and amenities in a ring around each floor). You
describe *what* is built; the map adds the drawing (the hub, the edges, the order round each
ring, the positions).

Each program is one JSON file in `src/popvis/development/programs/`. Programs with the same
`id` are one option in the "Site development" panel, with a plan for each of their segments:
`towers-segment-0.json` … `towers-segment-4.json` are "Towers on a podium" on each segment. A
segment's menu lists the options that have a plan for it.

## Format

```json
{
  "id": "towers",
  "name": "Towers on a podium",
  "summary": "One sentence for the panel and the voice assistant.",
  "segment": 0,
  "buildings": [
    {
      "id": "podium", "type": "podium", "footprint": "segment",
      "floors": [
        { "levels": [0], "amenities": { "lobby": 1, "grocery": 1, "retail": 4 } },
        { "levels": [1], "amenities": { "gym": 1, "daycare": 1 }, "serves": "development" }
      ]
    },
    {
      "id": "tower1", "type": "tower", "on": "podium", "footprint": [{ "row": 2, "col": 6 }],
      "floors": [
        { "levels": [0, 2], "units": { "studio": 1, "1br": 2, "2br": 2, "3br": 1 } },
        { "levels": [3], "units": { "1br": 2 }, "amenities": { "lounge": 1 }, "serves": "building" },
        { "levels": [4], "amenities": { "roofDeck": 1 }, "serves": "building" }
      ]
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `id` | The option the plan belongs to. Use a new id for a plan of its own; reuse one to add a plan for another segment to that option. |
| `name`, `summary` | The option's name in the panel and a one-sentence description; the same in every program with that `id`. |
| `segment` | Which segment, **0-based** (the panel's "Segment 1" is `0`). |
| `buildings[].id` | A name, unique within the segment. |
| `buildings[].type` | `podium`, `tower` or `plinth`. Sets the floors' colour. |
| `buildings[].on` | Optional: the `id` of the building it stands on. Its ground floor goes on top of that one's top floor. |
| `buildings[].footprint` | `"segment"` (every cell of the segment) or a list of `{ "row", "col" }` cells. The building's floors are drawn over the centre of its cells. |
| `floors[].levels` | `[level]` or `[first, last]` (inclusive), counted from the building's own ground floor (0). |
| `floors[].units`, `floors[].amenities` | Counts by type, on *each* of those levels. |
| `floors[].serves` | Optional: the floor's amenities serve every home on the segment (`"development"`) or only this building's (`"building"`). Drawn as service links. |

## Checking a file

[`development-program.schema.json`](development-program.schema.json) is the format's JSON
Schema (draft 2020-12). Start a program with
`"$schema": "<path to>/development-program.schema.json"` and editors such as VS Code complete
and check it as you type; any JSON Schema validator can check it too, for example
`npx ajv-cli validate --spec=draft2020 -s docs/development-program.schema.json -d my-program.json`.

The schema checks the shape and the types. It can't check how the buildings fit together:
the rules below. The map checks those when it loads the file.

## Rules

The map rejects a program that breaks any of these, naming the file and the place:

- Every footprint cell is on that segment (see the grid below), and none is given twice.
- A building that stands `on` another lies within that one's footprint, and buildings don't stand on each other in a circle.
- No two buildings share a cell on the same storey.
- Every level from 0 to the building's top is given exactly once.
- Types are from the lists below; counts are whole numbers above 0.
- Programs with the same `id` have the same `name` and `summary`, and plan different segments.

## Types

Units, with their floor area (a unit's disc is sized by it):
`studio` 45 m², `1br` 60 m², `2br` 85 m², `3br` 110 m².

Amenities, with how many people each serves (an amenity's disc is sized by it):
`lobby` 500, `retail` 300, `grocery` 2000, `cafe` 150, `restaurant` 200, `gym` 400,
`daycare` 80, `clinic` 1500, `library` 1000, `coworking` 150, `makerspace` 100,
`events` 300, `lounge` 100, `laundry` 60, `roofDeck` 120, `roofGarden` 300.

A new type is an entry in `src/popvis/development/kinds.ts` (its label, colour and size).

## The site grid

The site is a 14×14 grid of cells about 22 m apart. Each cell belongs to one segment (0–4);
`.` is off the site. Shown north-up, as on the map: **rows count northward** (row 0 is the
south end) and **columns count westward** (column 0 is the east edge).

![The site grid's segments, north up](site-segments.svg)

```
col    13 12 11 10  9  8  7  6  5  4  3  2  1  0
row 13  .  4  4  4  4  3  3  3  3  3  3  3  3  3
row 12  .  4  4  4  4  3  3  3  3  3  3  3  3  3
row 11  .  4  4  4  4  3  3  .  .  .  .  .  .  .
row 10  .  4  4  4  4  3  3  .  .  .  .  .  .  .
row  9  .  4  4  4  4  3  3  .  .  .  .  .  .  .
row  8  .  2  2  2  1  1  1  .  .  .  .  .  .  .
row  7  .  2  2  2  1  1  1  .  .  .  .  .  .  .
row  6  2  2  2  2  1  1  1  .  .  .  .  .  .  .
row  5  2  2  2  2  1  1  1  1  1  .  .  .  .  .
row  4  2  2  2  2  1  1  1  1  1  1  1  1  .  .
row  3  2  2  2  2  0  0  0  0  0  0  0  .  .  .
row  2  .  .  2  2  0  0  0  0  0  0  0  .  .  .
row  1  .  .  .  .  .  0  0  0  0  0  0  .  .  .
row  0  .  .  .  .  .  .  .  .  0  0  .  .  .  .
```

## Trying a program

Open the program viewer at https://linode.mistermatti.com/volpe/, or run the repo
(`npm install`, then `npm run dev`; no keys or population data needed) and open
http://localhost:5181/viewer.html. The viewer draws a program on its segment as the
map does. Start from one of the repo's programs, paste yours, or drop a `.json` file on the
page; every edit is checked, and if it breaks a rule the panel says which and where, while
the map keeps the last valid version.

To make it an option in the main map, put the file in `src/popvis/development/programs/` and
reload. Options are listed by file name.
