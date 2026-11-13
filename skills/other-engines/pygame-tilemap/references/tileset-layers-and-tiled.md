# Tilesets, cached layers, camera and Tiled (pygame-ce 2.5.8)

Depth for `pygame-tilemap`: the exact Surface APIs, the layout that keeps the frame cheap, and
the checks that catch a misaligned level.

## API used by the skill

| Call | Signature | Notes |
|------|-----------|-------|
| `pygame.image.load` | `load(path)` → `Surface` | Call `.convert()` (opaque) or `.convert_alpha()` (transparent) once. |
| `Surface.subsurface` | `subsurface(Rect)` → `Surface` | Shares pixels with the parent; `.copy()` to detach. |
| `Surface.copy` | `copy()` → `Surface` | Owns new pixels; costs memory per tile if overused. |
| `Surface.blit` | `blit(source, dest, area=None, special_flags=0)` → `Rect` | `area` copies a sub-rectangle of the source. |
| `Surface.fill` | `fill(color, rect=None, special_flags=0)` | With a `rect`, clears just that tile. |
| `pygame.Surface` | `Surface((w, h), flags)` | Use `pygame.SRCALPHA` for transparent layers. |
| `pygame.Rect` | `Rect(x, y, w, h)` | Integer edges: `left/top/right/bottom`. |
| `pygame.FRect` | `get_frect(**kwargs)` | pygame-ce float rect; useful for smooth positions. |
| `Rect.colliderect` | `colliderect(other)` → `bool` | Overlap test; touching edges do not count. |
| `Rect.clip` | `clip(other)` → `Rect` | Visible part of a layer, for culling. |
| `pygame.math.Vector2` | `Vector2(x, y)` | Camera and true float position. |

`blit` returns the affected `Rect`; ignore it unless you use `pygame.display.update(rects)`.

## Slicing math

No margin, no spacing:

```text
col = (gid - 1) % columns
row = (gid - 1) // columns
x   = col * tile_w
y   = row * tile_h
```

With margin `m` and spacing `s`:

```text
columns = (image_w - 2m + s) // (tile_w + s)
x       = m + col * (tile_w + s)
```

Rows use the same formula with `tile_h` and `image_h`. Slice with `pygame.Rect(x, y, tile_w,
tile_h)`; a rect one pixel too large makes neighbours bleed into the tile.

## Layer strategy

| Map size | Strategy | Cost |
|----------|----------|------|
| Up to ~2000×2000 px | one `Surface` per layer | one blit per layer per frame |
| Larger | chunk surfaces (32×32 tiles) | blit only visible chunks |
| Constantly edited | grid + dirty-region re-render | redraw changed cells only |

```python
CHUNK = 32
CHUNK_PX = CHUNK * TILE

def visible_chunks(camera: pygame.math.Vector2, screen: pygame.Surface,
                   map_w: int, map_h: int):
    c0 = max(0, int(camera.x) // CHUNK_PX)
    r0 = max(0, int(camera.y) // CHUNK_PX)
    c1 = min((map_w - 1) // CHUNK, (int(camera.x) + screen.get_width()) // CHUNK_PX)
    r1 = min((map_h - 1) // CHUNK, (int(camera.y) + screen.get_height()) // CHUNK_PX)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            yield col, row
```

Build chunks lazily and keep the grid authoritative so an edit survives a chunk rebuild.

## Camera rules

- Store the camera as floats for smooth follow, but round when blitting:
  `screen.blit(layer, (-round(camera.x), -round(camera.y)))`.
- Clamp the camera to `map_px - screen_size` so the edge does not show the clear colour; clamp to
  zero first for maps smaller than the window.
- Convert screen → world with `world = screen + camera`; world → screen with
  `screen = world - camera`.
- If the game renders to a fixed-size logical surface and scales it to the window, do all tile
  math in logical pixels and scale once at present time.

## Collision details

- Iterate every cell the rect overlaps; `(right - 1)` and `(bottom - 1)` avoid counting the
  cell just outside a rect whose edge lands exactly on a tile boundary.
- Decide the border policy once: solid out-of-bounds, or clamp the player to the map. Mixing the
  two makes one edge behave differently.
- One-way platforms need the previous position: solid only while falling and when the player's
  previous bottom was at or above the tile top.
- Slopes do not fit the grid; give slope tiles their own height function and resolve vertically
  against it.
- Keep platformer physics out of the tile loop: compute `dx`/`dy` first, then resolve against
  the grid (see `pygame-core` for the movement loop).

## pytmx notes

`pytmx` is an external package with its own release cycle.

- `pytmx.load_pygame(path)` returns a `TiledMap`.
- `tmx.width`/`tmx.height` are in tiles; `tmx.tilewidth`/`tmx.tileheight` are in pixels.
- Iterating a `TiledTileLayer` yields `(x, y, gid)`; `gid == 0` means empty.
- `tmx.get_tile_image_by_gid(gid)` returns a `Surface` or `None`; cache the results.
- Object layers (`tmx.objects`, `tmx.objectgroups`) are the place for spawn points and zones —
  convert them to plain data at load time.
- Layer order in `tmx.layers` is the draw order; keep only visible layers when baking.
- Use `tmx.get_tile_properties_by_gid(gid)` to read custom properties such as `solid`, `damage`
  or `oneway` instead of hard-coding ids.

## Debug checklist

1. Draw the collision grid over the art with a translucent overlay; walk every edge and corner.
2. Print `(col, row, gid, solid)` under the player; most "invisible wall" reports end here.
3. Render the map at 1:1 scale first, then add the camera. Misalignment introduced by the camera
   is much easier to spot this way.
4. Check a packaged build (PyInstaller and friends): asset paths are relative to the executable,
   not the source folder.
5. Profile with `pygame.time.Clock` and a frame-time print before and after caching; a correct
   layer adds one or two blits, not thousands.
6. Resize the window or toggle fullscreen once: tiles must stay sharp and collision must not
   shift.
