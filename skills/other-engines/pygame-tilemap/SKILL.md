---
name: pygame-tilemap
description: >
  Build tile levels in pygame-ce 2.5.8: slice a tileset into tile Surfaces, render each layer
  once to a cached Surface, scroll it with a camera offset, collide against the grid with Rect,
  edit tiles at runtime, and load Tiled maps through pytmx. Use when a pygame project has a
  tileset or Tiled map, or the request mentions a pygame tilemap, blitting tiles, tile
  collision, or a scrolling tile level. Targets pygame-ce 2.5.8.
---

# pygame tilemaps

pygame has no tilemap type: a tile level is a tileset image sliced into small `Surface`s, baked
into one cached layer `Surface`, drawn with a camera offset, plus your own integer grid for
collision. This skill builds that stack. Targets **pygame-ce 2.5.8**.

## When to use

- Use when drawing a tile level, scrolling a camera over it, colliding with tiles, or editing
  tiles at runtime in a pygame project.
- Use when the project ships a tileset image or a Tiled map and imports `pygame`.

**When *not* to use:** the main loop, `Sprite`/`Group` basics and input → `pygame-core`; level
pacing → `level-design`; cross-engine persistence → `save-systems`; physics tuning of a
non-tile world → `physics-tuning`.

## Core workflow

1. **Fix the tile size and tileset layout.** The tileset must sit on an exact grid; note any
   margin and spacing so the slicing math matches the art.
2. **Slice once, at load.** Cut each tile with `Surface.subsurface(rect).copy()` and store it by
   tile id in a dict. `.copy()` detaches the tile from the tileset surface, so the tileset can be
   released and no tile changes when another does.
3. **Keep the map as integers.** A list of rows per layer, `0` = empty; a separate collision grid
   marks solid ids.
4. **Bake each layer to one Surface.** Blit every tile into a `pygame.Surface` the size of the
   map, once; then the frame loop blits one surface per layer instead of thousands of tiles.
5. **Scroll with a camera offset.** Draw at `(x - camera.x, y - camera.y)`, rounded to integers;
   cull by rectangle before blitting when the map is bigger than the window.
6. **Collide against the grid.** Convert the player's `Rect` to tile indices and test solid ids;
   move one axis at a time in sub-tile steps.
7. **Verify in a window.** Check for seams, blurry tiles after scaling, and collision at every
   map edge; see the debug checklist in `references/tileset-layers-and-tiled.md`.

## Patterns

### 1. Slice a tileset into tiles

```python
import pygame

TILE = 16

def slice_tiles(tileset: pygame.Surface, tile_w: int, tile_h: int) -> dict[int, pygame.Surface]:
    cols = tileset.get_width() // tile_w
    rows = tileset.get_height() // tile_h
    tiles: dict[int, pygame.Surface] = {}
    for row in range(rows):
        for col in range(cols):
            rect = pygame.Rect(col * tile_w, row * tile_h, tile_w, tile_h)
            # .copy() owns the pixels; a bare subsurface keeps the tileset alive and shared.
            tiles[row * cols + col + 1] = tileset.subsurface(rect).copy()
    return tiles

tileset = pygame.image.load("assets/tileset.png").convert_alpha()
tiles = slice_tiles(tileset, TILE, TILE)
```

Tile id `1` is the top-left tile, matching Tiled's default `firstgid` of `1` for a single
tileset. If the tileset has margin/spacing, offset `rect` by them and step by
`tile_w + spacing`.

### 2. Bake a layer into one cached Surface

```python
def render_layer(grid: list[list[int]], tiles: dict[int, pygame.Surface],
                 tile_w: int, tile_h: int) -> pygame.Surface:
    rows, cols = len(grid), len(grid[0])
    layer = pygame.Surface((cols * tile_w, rows * tile_h), pygame.SRCALPHA)
    for row, cells in enumerate(grid):
        for col, gid in enumerate(cells):
            tile = tiles.get(gid)
            if tile is not None:
                layer.blit(tile, (col * tile_w, row * tile_h))
    return layer

ground_layer = render_layer(ground, tiles, TILE, TILE)
decor_layer = render_layer(decor, tiles, TILE, TILE)
```

`pygame.SRCALPHA` keeps transparency; without it the cached layer is opaque black where the map
has no tiles.

### 3. Draw with a camera offset and culling

```python
camera = pygame.math.Vector2(0, 0)

def draw_world(screen: pygame.Surface, layers: list[pygame.Surface]) -> None:
    offset = (-round(camera.x), -round(camera.y))
    for layer in layers:
        screen.blit(layer, offset)

# With a map much larger than the window, blit only the visible rectangle:
def draw_visible(screen: pygame.Surface, layer: pygame.Surface, camera: pygame.math.Vector2) -> None:
    view = pygame.Rect(round(camera.x), round(camera.y), *screen.get_size())
    view = view.clip(layer.get_rect())
    if view.width and view.height:
        screen.blit(layer, (view.x - camera.x, view.y - camera.y), area=view)
```

`blit(..., area=...)` copies only that part of the source; it does not scale. Round the camera
offset to whole pixels, otherwise tiles shimmer and `Rect` collision disagrees with what is on
screen.

### 4. Grid collision

```python
SOLID = {1, 2, 7}

def solid_at(grid: list[list[int]], col: int, row: int) -> bool:
    if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[row]):
        return True                      # the map border blocks movement
    return grid[row][col] in SOLID

def rect_hits_solid(grid: list[list[int]], rect: pygame.Rect) -> bool:
    c0, r0 = rect.left // TILE, rect.top // TILE
    c1, r1 = (rect.right - 1) // TILE, (rect.bottom - 1) // TILE
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            if solid_at(grid, col, row):
                return True
    return False

def move(body: pygame.math.Vector2, size: tuple[int, int],
         dx: float, dy: float, grid: list[list[int]]) -> None:
    steps = max(1, int(max(abs(dx), abs(dy)) // (TILE / 2)) + 1)
    sx, sy = dx / steps, dy / steps
    for _ in range(steps):
        probe = pygame.Rect(round(body.x + sx), round(body.y), *size)
        if not rect_hits_solid(grid, probe):
            body.x += sx
        probe = pygame.Rect(round(body.x), round(body.y + sy), *size)
        if not rect_hits_solid(grid, probe):
            body.y += sy
```

Keep the true position in floats (`Vector2` or `FRect`) and round only when building the probe
`Rect`; rounding the stored position every frame makes slow movement stick.

### 5. Edit tiles at runtime

```python
def set_tile(grid: list[list[int]], layer: pygame.Surface, tiles: dict[int, pygame.Surface],
             col: int, row: int, gid: int) -> None:
    grid[row][col] = gid
    dest = (col * TILE, row * TILE)
    tile = tiles.get(gid)
    if tile is None:
        # No "erase blit": cover the old tile with the layer background or re-render.
        layer.fill((0, 0, 0, 0), pygame.Rect(*dest, TILE, TILE))
    else:
        layer.blit(tile, dest)
```

For a handful of edits this is enough. For many edits per frame (falling sand, dug terrain),
keep the grid authoritative and re-render the dirty **region** with `layer.fill(..., area)` plus
a loop over that region instead of rebuilding the whole map.

### 6. Loading a Tiled map with pytmx

`pytmx` is a third-party loader, not part of pygame; install it separately and treat its API as
its own dependency.

```python
import pytmx

tmx = pytmx.load_pygame("assets/level.tmx")
tiles_by_gid = {}
for layer in tmx.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer):
        for x, y, gid in layer:
            tile = tmx.get_tile_image_by_gid(gid)
            if tile is not None:
                tiles_by_gid.setdefault(gid, tile)

# Then fill your own grid so collision does not depend on pytmx at runtime.
grid = [[0] * tmx.width for _ in range(tmx.height)]
for layer in tmx.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer) and layer.name == "collision":
        for x, y, gid in layer:
            grid[y][x] = gid
```

Read tile size, layer order and object layers from `tmx` once, then convert to plain grids and
Surfaces; do not query pytmx inside the frame loop.

## Pitfalls

- **Frame rate collapses on a big map** → one `blit` per tile per frame. Bake layers once, or
  render only dirty regions.
- **Tiles appear blurred or scaled wrong** → the window was resized or `SCALED` was used without
  matching the logical resolution. Keep the map at the window's logical size, or scale the whole
  layer uniformly.
- **A tile changes when another is edited** → the tiles share pixels through `subsurface`.
  `.copy()` each tile (or keep the tileset alive and never modify it).
- **Transparent tiles show black** → the cached layer was created without `pygame.SRCALPHA`.
- **Collision is offset from the art** → the camera offset is fractional, the tile size differs
  from the slicing size, or the rect origin is the sprite centre rather than its top-left.
- **Player sticks on walls or tunnels through floors** → you moved both axes at once, or moved
  farther than half a tile per check. Move axis by axis in sub-tile steps.
- **Map edge acts like a wall** → `solid_at` treats out-of-bounds as solid. That is usually
  wanted; if not, clamp the player to the map rect instead.
- **Tile ids off by one** → Tiled `firstgid` is not `1` when the map has several tilesets.
  Subtract the tileset's `firstgid - 1` before indexing.
- **Huge memory use** → a full-map RGBA layer at 4 bytes/pixel is large. Split big maps into
  chunk surfaces (for example 32×32 tiles) and blit only visible chunks.
- **`pytmx` import fails in a packaged build** → it is a separate dependency; vendor it or add it
  to the build's requirements, and keep a plain-grid fallback so the game still runs.

## References

- Read `references/tileset-layers-and-tiled.md` for the Surface/Rect API table, slicing math with
  margin/spacing, camera and culling details, pytmx field notes and a debug checklist.

## Related skills

- `pygame-core` — the loop, `Sprite`/`Group`, input and delta time this level plugs into.
- `level-design` — layout, pacing and readability of the tile grid.
- `camera-systems` — follow, deadzone and bounds behaviour.
- `procedural-gen` — generating the integer grid before it is rendered.
- `save-systems` — persisting level edits and player position.
