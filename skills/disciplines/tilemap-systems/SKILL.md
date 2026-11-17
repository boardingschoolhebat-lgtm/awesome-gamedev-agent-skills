---
name: tilemap-systems
description: >
  Design engine-neutral tilemap systems: coordinate contracts, layers, chunk streaming,
  autotile rules, collision/navigation mapping, culling, and versioned serialization. Use when
  a tile-based level needs a shared model before choosing an engine API, when tile offsets,
  seams or collision disagree, or when chunk memory and draw cost grow with map size. Defer
  engine tilemap API calls to the engine skill.
---

# Tilemap systems

A tilemap is authoring data (grid, layers, tile ids, rules) plus an engine adapter (rendering,
collision, navigation, streaming). Keep the data authoritative; the adapter is a thin
translation.

## When to use

- Use before choosing an engine API, or when one tile model must survive an engine change.
- Use when tile positions, seams, chunk borders or collision disagree with the visuals.
- Use when deciding layer structure, chunk size, autotile rules, collision flags, or a save
  format for edited levels.

**When *not* to use:** concrete engine tilemap API calls → the detected engine's tilemap skill.
Level layout and pacing → `level-design`. Tileset art and atlas packing → `create-game-assets`.
Map generation → `procedural-gen`. Collision response → `physics-tuning`. Save persistence →
`save-systems`.

## The model

### 1. Fix the coordinate contract

| Space | Unit | Used for |
|---|---|---|
| Grid | integer `(col, row)` | authoring, collision lookup, saves |
| World | pixels/units | rendering, physics, camera |
| Screen | pixels | input, UI, picking |

Write the conversion once:

```text
world = origin + (col * tile_w, row * tile_h)
cell  = floor((world - origin) / (tile_w, tile_h))
```

Record origin, y-direction, tile anchor, and the isometric/staggered projection in the data.
Author in grid space; convert only at rendering, physics and input boundaries. Keep sub-tile
offsets (props, slopes) in an explicit field, not in the tile id.

### 2. Layers and collision are data

| Layer kind | Contents | Collides? |
|---|---|---|
| Terrain | base walkable tiles | no |
| Walls | blocking tiles | yes |
| Detail | grass, cracks, props | no |
| Overlay | tree tops, roofs | sometimes |
| Hazard/trigger | spikes, water, doors | trigger only |
| Navigation | cost/blocked flags | no |

Each layer owns tile ids plus optional per-cell flags. Render order is separate; never infer
collision from the topmost visual. Map tile types to flags:

| Flag | Engine mapping |
|---|---|
| `solid` | collision layer/shape |
| `one_way` | one-way platform |
| `hazard` | trigger volume |
| `ladder` | area/volume |
| `nav_cost`, `nav_blocked` | navigation layer |

Keep visual variants of one tile type on the same flags.

### 3. Chunk and cull

A chunk is a fixed-size cell block, usually 16×16 or 32×32. Store global cells; derive
`chunk = (floor(col / size), floor(row / size))`. Use local coordinates only for storage.

- Autotiling and collision at a border need the neighbouring chunk's edge cells.
- Track a dirty flag per chunk; rebuild only that chunk.
- Load/unload around the camera with a hysteresis margin.
- Persist edits as chunk deltas, not full copies.
- Draw intersecting chunks/layers, not individual tiles; batch per chunk where possible.

### 4. Autotile rules are data

- Compute an 8-neighbour (or 4-neighbour) mask from layer occupancy.
- Map `(terrain, mask)` to candidate tile ids in a versioned rule table.
- Pick variants deterministically from a cell hash and seed.
- Re-evaluate the changed cell and its neighbours, not the whole map.
- Version the rule table with the tileset so atlas reordering cannot silently change the map.

### 5. Serialize identity

Store stable tile ids plus a tileset/palette id, never atlas pixels. Include a format version and
migration path, layer names/kinds, chunk keys and only changed chunks, and the ruleset version.
Put optional per-cell fields (rotation, variant, hazard damage) in explicit fields.

## Workflow

1. Write the coordinate contract.
2. Choose the layer and flag schema.
3. Choose the chunk size and record it in the save header.
4. Define stable tile ids and flags.
5. Build the autotile rule table.
6. Implement the engine adapter as a thin translation.
7. Test every chunk border, map edge, both axes, and a save reload.

## Pitfalls

- Mixing cell and world units in one function.
- Off-by-one chunk borders (inclusive vs exclusive).
- Deriving collision from visuals.
- Rebuilding autotiles or chunks for the whole map on every edit.
- Streaming without hysteresis; one node per tile on large maps.

## Composition

- Engine tilemap skill: concrete rendering, collision and tile-edit APIs.
- `level-design`: layout, pacing and encounters.
- `create-game-assets`: tileset art and atlas layout.
- `procedural-gen`: generation that writes into this grid.
