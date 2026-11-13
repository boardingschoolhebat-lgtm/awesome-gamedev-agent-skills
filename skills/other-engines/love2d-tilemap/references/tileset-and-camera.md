# Tilesets, batches, camera and tile collision (LÖVE 11.5)

Depth for `love2d-tilemap`: the exact APIs, the data layout that keeps the frame cheap, and the
checks that catch a misaligned level.

## API used by the skill

| Call | Signature | Notes |
|------|-----------|-------|
| `love.graphics.newImage` | `newImage(path[, flags])` | The tileset. Set the default filter **before** this call. |
| `love.graphics.newQuad` | `newQuad(x, y, w, h, texture)` | 11.0+ texture variant; older code passes `sw, sh` numbers. |
| `love.graphics.newSpriteBatch` | `newSpriteBatch(image, maxsprites[, usage])` | `usage`: `"static"`, `"dynamic"` (default) or `"stream"`. |
| `SpriteBatch:add` | `add(quad, x, y[, r, sx, sy, ox, oy])` → index | Index is 1-based and needed by `set`. |
| `SpriteBatch:set` | `set(index, quad, x, y[, r, sx, sy, ox, oy])` | Requires a batch that is not `"static"`. |
| `SpriteBatch:clear` | `clear()` | Empties the buffer; indices restart at 1. |
| `SpriteBatch:setDrawRange` | `setDrawRange(start, count)` | 11.0+; trims what is drawn, does not reposition. |
| `SpriteBatch:setColor` | `setColor(r, g, b[, a])` | Applies to the next `add`/`set`. |
| `love.graphics.draw` | `draw(batch)` | One call per batch. |
| `love.graphics.translate` | `translate(dx, dy)` | Inside `push`/`pop` for the camera. |
| `love.graphics.setDefaultFilter` | `setDefaultFilter(min, mag[, anisotropy])` | `"nearest"` for pixel art. |

`newQuad` accepts either a texture or explicit source dimensions; the texture form is shorter and
keeps the quad correct if the image changes size.

## Quad math

For a tileset with no margin and no spacing:

```text
col  = (id - 1) % columns
row  = (id - 1) / columns          -- integer division
x    = col * tile_w
y    = row * tile_h
```

With margin `m` and spacing `s` between tiles:

```text
columns = floor((image_w - 2m + s) / (tile_w + s))
x       = m + col * (tile_w + s)
```

The `+ s` in the column count accounts for the trailing spacing the formula would otherwise
count as a tile. Use the same formula for rows and `tile_h`.

## Layer and chunk layout

```text
level
├── ground   grid[r][c] = gid   -> batch (static)
├── decor    grid[r][c] = gid   -> batch (static)
├── collision grid[r][c] = 0/1  -> never drawn
└── chunks   chunk[tile_y // 32][tile_x // 32] -> batch
```

Chunk culling:

```lua
local CHUNK_TILES = 32
local CHUNK_PX = CHUNK_TILES * TILE

local function visible(cx, cy, camera, screen_w, screen_h)
    local left, top = cx * CHUNK_PX, cy * CHUNK_PX
    return left < camera.x + screen_w
       and left + CHUNK_PX > camera.x
       and top < camera.y + screen_h
       and top + CHUNK_PX > camera.y
end
```

Build chunks lazily: an empty chunk needs no batch, and a chunk that scrolls back in can be
rebuilt from the grid. Keep the grid authoritative so edits survive a chunk rebuild.

## Camera

```lua
local function clamp_camera(camera, map_w, map_h, screen_w, screen_h)
    camera.x = math.max(0, math.min(camera.x, map_w - screen_w))
    camera.y = math.max(0, math.min(camera.y, map_h - screen_h))
end
```

Rules that avoid the common artifacts:

- Translate by `-math.floor(camera.x)`; fractional camera offsets make nearest-filtered tiles
  shimmer.
- Draw `love.graphics.rectangle("fill", 0, 0, map_w, map_h)` behind the layers when the map is
  smaller than the window, so the edge does not show the clear colour.
- Convert screen → world with `world = screen + camera`, and world → screen with
  `screen = world - camera`. Do not mix the two in collision code.
- If the camera is scaled or zoomed, convert positions **before** dividing by `TILE`; the tile
  grid itself stays unscaled.

## Tiled gids

- `firstgid` is per tileset; with several tilesets a gid belongs to the tileset whose
  `firstgid` is the largest one not above the gid. Subtract that `firstgid - 1` to get the local
  tile id used by `quads`.
- Tiled 1.5+ stores flip/rotation in the high bits of the gid (horizontal, vertical, diagonal,
  and hexagonal rotation). Mask them off before indexing; apply the flip with
  `Quad:flip`/rotation or a draw-time transform.
- `layers[i].data` is a flat array of `width * height` gids, row-major. Empty cells are `0`.
- CSV, base64 and zlib-compressed layer data all decode to the same array; only the decode step
  differs.
- Tile animations are a list of `(tileid, duration)` frames in the tileset; LÖVE has no built-in
  tile animation, so swap the quad on a timer.

## Collision grid checks

- Test the **box corners and edges**, not just the centre: iterate every cell the box overlaps
  (`floor((x + w - 1) / TILE)`), as in the skill.
- Out of bounds: decide once whether the level border is solid. Making it solid prevents walking
  off the map without an extra clamp.
- One-way platforms need a direction test: only solid when the body moves down and its previous
  bottom was above the tile top.
- Slopes are not tile-aligned; handle them with a separate height function per tile id rather
  than pretending the grid is a heightfield.
- Keep collision ids in a set (`SOLID[id] = true`) so the inner loop is a table lookup.

## Debug checklist

1. Draw the collision grid as translucent rectangles over the art (`love.graphics.rectangle`
   with alpha) and walk every edge.
2. Print the tile under the player: `col, row, id, solid`. A mismatch here explains most
   "invisible wall" reports.
3. Check a packaged `.love` build, not only `love .`: the save/asset paths and the working
   directory differ.
4. Verify the tile size after a window resize or a canvas scale; the grid must use the same
   logical pixels as the quads.
5. Profile with `love.graphics.getStats()` (`drawcalls`, `batches`) before and after chunking; a
   correct layer should add one or two draw calls, not hundreds.
