# Atlases, chunks and collision (Bevy 0.20)

Depth for `bevy-tilemap`: the atlas API, the index math, chunking strategy and the collision
conventions that keep the visual grid and the gameplay grid aligned.

## API used by the skill

| Item | Signature / form | Notes |
|------|------------------|-------|
| `TextureAtlasLayout::from_grid` | `(tile_size: UVec2, columns: u32, rows: u32, padding: Option<UVec2>, offset: Option<UVec2>)` | One cell per tile; padding/offset describe the sheet's gutters. |
| `assets.add` | `texture_atlas_layouts.add(layout)` | Store the returned `Handle<TextureAtlasLayout>`. |
| `Sprite::from_atlas_image` | `(texture: Handle<Image>, atlas: TextureAtlas)` | Builds a sprite whose `texture_atlas` is `Some(..)`. |
| `TextureAtlas` | `{ layout: Handle<TextureAtlasLayout>, index: usize }` | Index is 0-based. |
| `Sprite.texture_atlas` | `Option<TextureAtlas>` | Mutate the index to swap tiles at runtime. |
| `Sprite.custom_size` | `Option<Vec2>` | Force a world size when the sheet's tile size differs. |
| `ImagePlugin::default_nearest()` | plugin setting | Nearest filtering for pixel art. |
| `Commands::spawn` | `spawn((..))` → `EntityCommands` | Deferred insertion. |
| `EntityCommands::with_child` | `with_child((..))` | Spawns a child in one call. |
| `Visibility` | `Visible` / `Hidden` / `Inherited` | Hides the hierarchy, keeps entities alive. |

## Index math

```text
columns = tileset_width / tile_width
rows    = tileset_height / tile_height
index   = (row_in_sheet * columns) + col_in_sheet     -- 0-based
```

Tiled gid → atlas index: `index = gid - firstgid`. With a single tileset and default `firstgid =
1`, `index = gid - 1`. Multiply the row by the number of **columns**, not rows; swapping them is a
common off-by-one that still looks plausible on square sheets.

With margin `m` and spacing `s`, `from_grid` needs `padding`/`offset` rather than a hand-rolled
formula:

```rust
let layout = TextureAtlasLayout::from_grid(
    UVec2::splat(16),
    16,                    // columns
    16,                    // rows
    Some(UVec2::splat(1)), // padding between tiles
    Some(UVec2::splat(1)), // offset from the sheet's top-left corner
);
```

Verify the values against the tileset's real margins; a one-pixel error shows as a strip of the
neighbouring tile on every edge.

## Layer and chunk layout

```text
Level (root, z = -10..10 per layer)
├── Chunk_0_0 (Transform, Visibility, Chunk)
│   ├── Sprite tile (col, row, z = 0)
│   └── ...
└── Chunk_1_0
```

- A chunk is 16–64 tiles per side; 32 keeps entity counts per chunk manageable and culling
  granular.
- Spawn children relative to the chunk or in world space consistently. The example above uses
  world-space children plus a chunk `Transform` at the chunk origin; pick one and keep it.
- Cull with a radius that covers the window plus a margin, or compute the real viewport from the
  camera and window.
- Despawning and respawning chunks from `MapGrid` is safe because the grid, not the sprite
  entities, is authoritative.

## Collision conventions

- One conversion pair, used everywhere:

  ```text
  col  = floor(x / TILE)
  row  = floor(-y / TILE)      -- when row 0 is at the top (screen coordinates)
  x    = col * TILE
  y    = -row * TILE
  ```

- A body is a centre point plus half-extents. Test every cell the box overlaps:
  `left..=right`, `top..=bottom`, using `-0.001` on the far edges so a box that ends exactly on a
  tile boundary does not claim the next cell.
- Resolve X first, then Y, and re-check the second axis with the updated position. This gives
  clean wall sliding without a physics engine.
- Sub-step: `steps = ceil(max(|dx|, |dy|) / (TILE * 0.5))`. At high speed this is the difference
  between stopping at a wall and passing through it.
- Decide the border policy once: out-of-bounds solid (the example) or clamped. Mixing them makes
  one map edge behave differently.
- One-way platforms need the previous position: solid only while moving down and when the
  previous bottom was above the platform top.

## Third-party tilemap crates

Use one when the map is large, needs many layers, tile animation or built-in culling. Before
adding:

1. Read the crate's README for its supported Bevy version; a crate pinned to an older minor will
   not compile against 0.20.
2. Check whether it uses the same `TextureAtlasLayout`/`Sprite` pipeline or its own material and
   mesh path.
3. Keep the gameplay grid in your own `Resource` regardless; do not let the crate's entities become
   the source of truth for collision or saves.
4. Measure: one sprite per tile is fast enough for many 2D games, and a crate adds a dependency and
   its own migration cost.

## Testing checklist

1. Load a level with one tile: exactly one sprite, correct tile, correct position.
2. Load a multi-cell level: no duplicated or missing tiles, layers in the intended order.
3. Walk to every map edge: no invisible walls, no fall-through, no gap between collision and art.
4. Sprint at a wall and a thin floor: sub-stepping stops the body.
5. Edit a solid tile to empty and back: collision and visuals both change.
6. Scroll a large map: chunks hide/show without visible popping inside the window.
7. Zoom or resize the window: collision stays aligned with the art (gameplay is in world units).
8. Save and reload an edited grid: the level returns identically.
