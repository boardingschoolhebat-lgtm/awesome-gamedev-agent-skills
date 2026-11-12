---
name: defold-tilemap
description: >
  Build and script tile levels in Defold 1.14.0: tile sources with collision groups, multi-layer
  .tilemap components, tilemap.get_tile/set_tile, world-to-tile math, runtime doors and
  destructible tiles, per-layer visibility, and tile collision objects. Use when a project has
  .tilemap or .tilesource files, or the request mentions a Defold tilemap, painting tiles, tile
  collisions, tile layers, tilemap.set_tile, or checking which tile is under a position.
---

# Defold tilemaps

Build grid levels in Defold 1.14.0 with a `.tilemap` component painted from a `.tilesource`.
Targets **Defold 1.14.0**.

A tilemap stores tile indices per layer; the tilesource supplies the images, the tile size
and — when a collision image is set — the collision shapes and groups for each tile.

## When to use

- Use when painting or scripting tile levels, adding tile collisions, hiding layers, or
  reading the tile under a world position.
- Use when a project contains `.tilemap` or `.tilesource` files, or when level geometry must
  change at runtime (doors, breakables, dug tiles).

**When *not* to use:** the level's layout and pacing → `level-design`; collision objects, groups
and physics messages → `defold-collision` (+ `physics-tuning`); GUI → `defold-ui`; procedural
map generation → `procedural-gen`; camera bounds → `camera-systems`.

## Core workflow

1. **Author the tilesource.** One image on a strict grid (same tile size, optional margin and
   spacing). Set the **Collision** image if tiles should collide; Defold traces the opaque
   pixels into a convex shape per tile, so collision can differ from the visuals.
2. **Add collision groups to the tilesource.** Right-click the tilesource root → *Add ▸
   Collision Group* (`ground`, `danger`, …) and paint each tile into a group. Tiles without a
   group are decorative only.
3. **Paint the tilemap.** Add layers for background, ground and decoration; keep collision
   tiles on their own layer so hiding art never changes physics.
4. **Attach a collision object.** Add a collision object to the same game object and set its
   **Collision Shape** to the `.tilemap`. The groups come from the tilesource — do not fill in
   the collision object's Group.
5. **Script with tile coordinates.** Convert world positions to 1-based indices, read with
   `tilemap.get_tile`, and write with `tilemap.set_tile`. Clear a cell with index `0`.
6. **Verify with physics debug.** Toggle *Debug ▸ Toggle Physics Debug* and run a desktop
   build: tile shapes should line up with the art, and edited cells should update.

## Patterns

### 1. World position → tile index

```lua
local TILE_W = 32   -- must match the tile source's tile width
local TILE_H = 32

-- Tile (1, 1) sits just above and to the right of the component's origin.
local function world_to_tile(pos)
	local origin = go.get_position()                 -- the game object holding the tilemap
	local x = math.floor((pos.x - origin.x) / TILE_W) + 1
	local y = math.floor((pos.y - origin.y) / TILE_H) + 1
	return x, y
end

function is_grounded(self)
	local x, y = world_to_tile(go.get_position())
	return tilemap.get_tile("#tilemap", "ground", x, y) ~= 0
end
```

Indices grow up and to the right; `0` and negative values are valid cells left of and below
the origin, which `math.floor` handling above already produces.

### 2. Bounds check and full-layer scan

```lua
function count_solid(self)
	local left, bottom, columns, rows = tilemap.get_bounds("#tilemap")
	local solid = 0
	for y = bottom, bottom + rows - 1 do
		for x = left, left + columns - 1 do
			if tilemap.get_tile("#tilemap", "ground", x, y) ~= 0 then
				solid = solid + 1
			end
		end
	end
	return solid
end
```

`get_bounds` collapses all layers into one rectangle, so use it for iteration limits rather
than assuming the painted area starts at `1, 1`.

### 3. Change a tile at runtime (doors, breakables)

```lua
local function set_cell(x, y, index, transform)
	tilemap.set_tile("#tilemap", "ground", x, y, index, transform or 0)
end

set_cell(12, 4, 0)                                     -- open a door: clear the cell
set_cell(12, 5, 77, tilemap.H_FLIP + tilemap.ROTATE_90) -- place a flipped, rotated tile
```

The cell must already exist inside the tilemap's bounds — `set_tile` cannot grow the map.
Flips apply before rotation, and the bitmask is a sum of `H_FLIP`, `V_FLIP` and one
`ROTATE_*` constant.

### 4. React to tile collision groups

```lua
function on_message(self, message_id, message, sender)
	if message_id == hash("collision_response") then
		-- Groups live on the tile source; a lava tile reports "danger".
		if message.own_group == hash("danger") or message.other_group == hash("danger") then
			go.delete(message.other_id)
		end
	end
end
```

Because the tile's shape belongs to the tilemap's collision object, check both group fields;
the official tilemap-collision example reads `own_group` from the object hitting the tiles.

### 5. Toggle layers and tint

```lua
tilemap.set_visible("#tilemap", "foreground", false)   -- hide decor, keep collisions
```

`tilemap.set_visible` affects rendering only. To dim a whole layer, animate the material's
`tint` constant on a material copy instead of the shared default material.

## Pitfalls

- **Tiles are visible but nothing collides** — a tilemap alone has no physics. Add a collision
  object whose Collision Shape is the tilemap, and set its Mask to the groups that should hit.
- **Collision object Group seems ignored** — for tilemap shapes the groups come from the
  tilesource. Setting the component's Group does not add tile collision.
- **Every tile collides, including decoration** — tiles were left in the tilesource's default
  group. Paint decorative tiles into no group, and give hazards their own group.
- **Off-by-one lookups** — indices are 1-based from the origin, and tiles below/left of it are
  `0, -1, -2`. `math.floor(world / tile_size) + 1` handles both sides.
- **`set_tile` silently does nothing** — the coordinates are outside the bounds the map was
  created with, or the layer name is misspelled. Layer names are hashed, so a typo is not an
  error at load.
- **`get_tile` returns a number that is not a tile resource** — it returns the index into the
  tilesource (and `0` for empty), not a `resource.tile_source`.
- **Hiding a layer also removes collision** — it does not; if collision disappeared, the tiles
  and the visuals were on different layers or the collision object was disabled.
- **Swapping `tile_source` at runtime keeps old collision** — the collision mapping follows the
  tilesource the tilemap was built with in some versions. Keep one tilesource per tilemap, and
  if levels differ, use separate tilemap prototypes or rebuild the level.
- **Rotated or scaled tilemap game objects break world math** — the conversion above assumes
  no rotation and uniform scale. Apply the inverse transform first, or keep level tilemaps
  axis-aligned.
- **Physics debug shows shapes offset from art** — the tilesource's margin/spacing or tile size
  does not match the image. Fix the tilesource, not the collision object.

## References

- Read `references/tilesource-and-collision.md` for tilesource setup, collision groups and
  masks, physics message fields, the coordinate diagram and a debug checklist.

## Related skills

- `level-design` — layout, pacing and readability of the tile grid.
- `defold-core` — game objects, scripts, messages, factories and Bob builds.
- `physics-tuning` — collision shapes, masks and fixed-timestep behavior.
- `defold-ui` — HUD and menus alongside the level.
- `procedural-gen` — generating tile data before painting it into a tilemap.
- `camera-systems` — bounds and follow logic for tile-based levels.
