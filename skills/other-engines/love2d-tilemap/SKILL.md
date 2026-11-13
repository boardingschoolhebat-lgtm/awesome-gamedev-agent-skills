---
name: love2d-tilemap
description: >
  Build tile levels in LÖVE 11.5 from a tileset: quads per tile, a SpriteBatch per layer,
  camera translation and chunk culling, grid-based tile collision, runtime tile edits, and
  importing Tiled or LDtk exports with a helper. Use when a LÖVE project has a tileset or a tile
  map, or the request mentions a LÖVE tilemap, sprite batch, quads, tile layers, tile collision,
  or a scrolling tile level. Targets LÖVE 11.5.
---

# LÖVE tilemaps

LÖVE has no tilemap object: a tile level is an image of tiles cut into **quads**, packed into
one **SpriteBatch** per layer, plus your own integer grid. This skill builds that stack.
Targets **LÖVE 11.5**.

## When to use

- Use when drawing a tile level, scrolling a camera over it, colliding with tiles, or editing
  tiles at runtime in a LÖVE project.
- Use when the project ships a tileset image or a Tiled/LDtk export and `main.lua` calls `love.*`.

**When *not* to use:** level pacing and layout → `level-design`; Box2D bodies and joints →
`love.physics`/`physics-tuning`; flipbook animation → `love2d-core` plus `game-feel`; saving
progress → `love2d-save`; cross-engine save design → `save-systems`.

## Core workflow

1. **Fix the tile size and tileset layout.** A tileset is one image on an exact grid. Note its
   margin and spacing (Tiled calls them that); they must match when you build quads.
2. **Build quads once, at load.** `love.graphics.newQuad(x, y, w, h, texture)` cuts one tile;
   store them in a 1-based array indexed by tile id (`quads[id]`).
3. **Keep the map as integers, not draw calls.** One 2D array per layer, row-major, `0` = empty.
   Keep the *collision* grid separate from decorative layers.
4. **Bake each layer into a SpriteBatch.** One batch per layer (or per chunk), `"static"` usage
   for painted levels, `"dynamic"` when tiles change; draw the batch once per frame.
5. **Move the camera, not the level.** `love.graphics.push()` → `translate(-cam.x, -cam.y)` →
   draw → `pop()`. Round the translation to whole pixels so tiles stay crisp.
6. **Collide against the grid.** Convert the player's box to tile indices and test solid ids;
   move axis by axis in sub-tile steps to avoid tunnelling.
7. **Verify in a build.** Check seams, blurry tiles, and collision at the level edges; see the
   debug checklist in `references/tileset-and-camera.md`.

## Patterns

### 1. Cut a tileset into quads (margin/spacing aware)

```lua
local TILE = 16

local function build_quads(image, tile_w, tile_h, margin, spacing)
    local cols = math.floor((image:getWidth()  - margin * 2 + spacing) / (tile_w + spacing))
    local rows = math.floor((image:getHeight() - margin * 2 + spacing) / (tile_h + spacing))
    local quads = {}
    for row = 0, rows - 1 do
        for col = 0, cols - 1 do
            local x = margin + col * (tile_w + spacing)
            local y = margin + row * (tile_h + spacing)
            -- The 5th argument is the texture whose size the quad is relative to (11.0+).
            quads[row * cols + col + 1] = love.graphics.newQuad(x, y, tile_w, tile_h, image)
        end
    end
    return quads
end

local tileset = love.graphics.newImage("assets/tileset.png")
local quads = build_quads(tileset, TILE, TILE, 0, 0)
```

Tile id `1` is the top-left tile. Tiled's first `gid` is `firstgid` (usually `1`), so
`quads[gid]` works directly for a single-tileset map.

### 2. Bake one layer into a SpriteBatch

```lua
local function build_layer(image, quads, grid, tile_w, tile_h)
    local used = 0
    for row = 1, #grid do
        for col = 1, #grid[row] do
            local id = grid[row][col]
            if id > 0 and quads[id] then used = used + 1 end
        end
    end

    -- "static" tells LÖVE the batch will not change; use "dynamic" if set() is needed.
    local batch = love.graphics.newSpriteBatch(image, used, "static")
    for row = 1, #grid do
        for col = 1, #grid[row] do
            local id = grid[row][col]
            if id > 0 and quads[id] then
                batch:add(quads[id], (col - 1) * tile_w, (row - 1) * tile_h)
            end
        end
    end
    return batch
end
```

Never draw each tile with `love.graphics.draw(quads[id], ...)` in the frame loop: hundreds of
draw calls per layer is the usual cause of a LÖVE tilemap dropping frames.

### 3. Draw with a camera and chunk culling

```lua
local camera = { x = 0, y = 0 }

local function draw_layer(batch)
    love.graphics.draw(batch)
end

function love.draw()
    love.graphics.push()
    love.graphics.translate(-math.floor(camera.x), -math.floor(camera.y))
    draw_layer(ground_batch)
    draw_layer(decor_batch)
    love.graphics.pop()
end
```

For large maps, build one batch per **chunk** (for example 32×32 tiles) and skip chunks whose
world rectangle does not intersect the camera viewport. That keeps both memory and draw calls
bounded; `setDrawRange(start, count)` only trims a single batch and does not cull by position.

### 4. Tile collision from the grid

```lua
local SOLID = { [1] = true, [2] = true, [7] = true }   -- tile ids that block

local function solid_at(grid, col, row)
    local line = grid[row]
    return line ~= nil and SOLID[line[col] or 0] == true
end

local function overlaps_solid(grid, x, y, w, h)
    local c0 = math.floor(x / TILE) + 1
    local r0 = math.floor(y / TILE) + 1
    local c1 = math.floor((x + w - 1) / TILE) + 1
    local r1 = math.floor((y + h - 1) / TILE) + 1
    for row = r0, r1 do
        for col = c0, c1 do
            if solid_at(grid, col, row) then return true end
        end
    end
    return false
end

local function move(body, dx, dy, grid)
    -- Sub-tile steps: never move more than half a tile per check, at any speed.
    local steps = math.max(1, math.ceil(math.max(math.abs(dx), math.abs(dy)) / (TILE / 2)))
    local sx, sy = dx / steps, dy / steps
    for _ = 1, steps do
        if not overlaps_solid(grid, body.x + sx, body.y, body.w, body.h) then body.x = body.x + sx end
        if not overlaps_solid(grid, body.x, body.y + sy, body.w, body.h) then body.y = body.y + sy end
    end
end
```

The grid is 1-based, so world `x = 0..TILE-1` is column `1`. Keep the collision layer's ids in
sync with art changes; a decorative tile must not be solid by accident.

### 5. Edit tiles at runtime (doors, dug blocks, breakables)

```lua
-- Build this layer with "dynamic" usage and remember each cell's sprite index.
local handles = {}   -- handles[row][col] = index returned by batch:add
for row = 1, #grid do
    handles[row] = {}
    for col = 1, #grid[row] do
        local id = grid[row][col]
        if id > 0 and quads[id] then
            handles[row][col] = layer:add(quads[id], (col - 1) * TILE, (row - 1) * TILE)
        end
    end
end

local function set_tile(row, col, id)
    grid[row][col] = id
    local index = handles[row][col]
    if index then
        layer:set(index, quads[id], (col - 1) * TILE, (row - 1) * TILE)
    else
        handles[row][col] = layer:add(quads[id], (col - 1) * TILE, (row - 1) * TILE)
    end
end
```

`set` needs a batch created with `"dynamic"` (or `"stream"`); a `"static"` batch may already
have been uploaded. Clearing a cell cannot remove a sprite index — draw the empty tile or rebuild
the layer.

### 6. Importing a Tiled export

LÖVE ships no JSON or TMX parser, and no tilemap loader. Two supported routes:

- **JSON export + a JSON library.** Decode the map, then use `tilewidth`, `tileheight`,
  `layers[i].data` and `layers[i].width` to fill your grids. `data` holds global tile ids, so
  subtract `firstgid - 1` per tileset; the top bits of a gid are flip flags in Tiled 1.5+.
- **A third-party loader** such as `STI` (Simple Tiled Implementation) for `.tmx`/`.lua` maps.
  Treat it as an external dependency with its own API and version, not as part of LÖVE.

Whatever the route, end with plain grids and quads: the rest of this skill does not care where
the numbers came from.

## Pitfalls

- **Tiles are blurry or bleed at the seams** → the default linear filter samples neighbouring
  tiles. Call `love.graphics.setDefaultFilter("nearest", "nearest")` before loading the tileset,
  and keep the camera translation integral.
- **Quads land on the wrong tile** → margin/spacing or tile size does not match the image, or the
  id is 0-based. Quads and ids here are 1-based; Tiled gids are not.
- **Only the first tile of the tileset draws** → every quad was built with the same x/y. Build
  the full grid, or cut quads on demand and cache them.
- **Batch is blank or throws on `add`** → the batch was created with too small a sprite count.
  Count the drawn tiles first, or `setBufferSize` before adding.
- **Edited tile never changes** → the batch is `"static"`, or you changed the grid without
  calling `batch:set`.
- **Everything moves at a crawl** → one draw call per tile, or a new batch per frame. Bake once,
  draw once; only rebuild on a real edit.
- **Player tunnels through thin floors at high speed** → one large move per frame skips the tile.
  Sub-step the movement or sweep the covered cells.
- **Collision is offset from the art** → world-to-tile math uses the wrong origin or a scaled
  camera. Keep the level at 1:1 scale and convert with the same tile size used to build quads.
- **Huge map exhausts memory** → a full-map batch plus a full-map Surface is heavy. Chunk the
  layers and drop chunks far from the camera.
- **Camera shows gaps at the level edge** → the drawable area is smaller than the window. Clamp
  the camera to the map rectangle or draw a background colour behind the layers.

## References

- Read `references/tileset-and-camera.md` for the quad/SpriteBatch API table, chunk layout,
  camera math, Tiled gid details, collision grid checks and a debug checklist.

## Related skills

- `love2d-core` — the callback loop, input and screen states this level plugs into.
- `love2d-save` — persisting level edits and player position.
- `level-design` — layout, pacing and readability of the tile grid.
- `camera-systems` — follow, deadzone and bounds behaviour.
- `procedural-gen` — generating the integer grid before it is baked into a batch.
