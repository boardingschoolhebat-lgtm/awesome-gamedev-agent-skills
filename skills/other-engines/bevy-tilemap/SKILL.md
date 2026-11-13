---
name: bevy-tilemap
description: >
  Build tile levels in Bevy 0.20: cut a tileset with TextureAtlasLayout, spawn one Sprite per
  non-empty cell with TextureAtlas, chunk entities for culling, convert world positions to grid
  cells, collide against the grid, and edit tiles at runtime. Use when a Bevy project needs a
  tilemap, sprite-sheet tiles, a grid level, or tile collision. Targets Bevy 0.20.
---

# Bevy tilemaps

Bevy has no tilemap type: a tile level is a `TextureAtlasLayout` cut from a tileset, one `Sprite`
entity per non-empty cell, and your own integer grid for collision. This skill builds that stack.
Targets **Bevy 0.20**.

## When to use

- Use when drawing a tile level, chunking a large map, colliding with tiles, or editing tiles at
  runtime in a Bevy project.
- Use when `Cargo.toml` depends on `bevy` and the level is a grid of sprite-sheet tiles.

**When *not* to use:** ECS structure, scheduling and queries → `bevy-ecs`; level pacing →
`level-design`; saving edited levels → `bevy-save`; very large maps where a third-party tilemap
crate is justified (see the note below); 3D grids → Bevy 3D mesh work, not this skill.

## Core workflow

1. **Pin the version.** Read `Cargo.toml`/`Cargo.lock`; the atlas API changed across releases.
   New examples target Bevy 0.20.
2. **Keep tiles sharp.** Add `DefaultPlugins.set(ImagePlugin::default_nearest())`, or the nearest
   sampler on the tileset image; linear filtering bleeds neighbouring tiles at the seams.
3. **Build the layout once.** `TextureAtlasLayout::from_grid(UVec2::splat(TILE), columns, rows,
   None, None)` and `texture_atlas_layouts.add(layout)`.
4. **Keep the grid as data.** A `Resource` with rows of tile ids (`0` = empty) and a set of solid
   ids; the sprites are a view, the grid is the truth.
5. **Spawn one sprite per non-empty cell.** `Sprite::from_atlas_image(texture, TextureAtlas {
   layout, index })` plus a `Transform` at `(col * TILE, -row * TILE, z)` and a `Tile { col, row }`
   marker. Index is 0-based; Tiled gids are 1-based.
6. **Chunk large maps.** Spawn a parent entity per chunk, keep its tiles as children, and toggle
   or despawn chunks outside the camera view.
7. **Collide against the grid.** Convert a world position to a cell with `floor(pos / TILE)` and
   test the solid set; move axis by axis in sub-tile steps to avoid tunnelling.
8. **Edit through the grid.** Change the stored id and update that entity's
   `sprite.texture_atlas.index`, or despawn/spawn it; never treat the sprite as the source of
   truth.

## Patterns

### 1. Layout and level data

```rust
use bevy::prelude::*;
use std::collections::HashSet;

const TILE: f32 = 16.0;

#[derive(Resource)]
struct LevelAssets {
    texture: Handle<Image>,
    layout: Handle<TextureAtlasLayout>,
}

#[derive(Resource)]
struct MapGrid {
    tiles: Vec<Vec<u32>>,      // tiles[row][col], 0 = empty
    solid: HashSet<u32>,
}

fn load_level(
    mut commands: Commands,
    asset_server: Res<AssetServer>,
    mut layouts: ResMut<Assets<TextureAtlasLayout>>,
) {
    let texture = asset_server.load("textures/tileset.png");
    // tile size, columns, rows, padding, offset — all Option arguments are UVec2.
    let layout = TextureAtlasLayout::from_grid(UVec2::splat(TILE as u32), 16, 16, None, None);
    let layout = layouts.add(layout);

    commands.insert_resource(LevelAssets { texture, layout });
    commands.insert_resource(MapGrid {
        tiles: vec![vec![1; 40]; 20],
        solid: HashSet::from([1, 2, 7]),
    });
}
```

`from_grid` counts columns and rows in tiles, so `16, 16` describes a 16×16-tile sheet. Padding and
offset are optional `UVec2` values for tilesets with gutters; pass the real values or the atlas
indices drift by a few pixels per tile.

### 2. Spawn the tiles

```rust
#[derive(Component)]
struct Tile {
    col: u32,
    row: u32,
}

fn spawn_tiles(assets: Res<LevelAssets>, grid: Res<MapGrid>, mut commands: Commands) {
    for (row, cells) in grid.tiles.iter().enumerate() {
        for (col, &id) in cells.iter().enumerate() {
            if id == 0 {
                continue;
            }
            commands.spawn((
                Sprite::from_atlas_image(
                    assets.texture.clone(),
                    TextureAtlas {
                        layout: assets.layout.clone(),
                        index: id as usize - 1,     // gid 1 -> atlas index 0
                    },
                ),
                Transform::from_xyz(col as f32 * TILE, -(row as f32) * TILE, 0.0),
                Tile { col: col as u32, row: row as u32 },
            ));
        }
    }
}
```

Row `0` at `y = 0` and rows growing downward matches screen coordinates; flip the sign if the
project uses Y-up world space. Give each layer a distinct `z` (background `-10`, ground `0`,
decor `10`) because Bevy does not guarantee draw order for equal-z sprites.

### 3. Chunk a large map

```rust
#[derive(Component)]
struct Chunk {
    min: Vec2,
    max: Vec2,
}

fn spawn_chunk(commands: &mut Commands, assets: &LevelAssets, grid: &MapGrid,
               chunk_col: usize, chunk_row: usize) {
    const CHUNK: usize = 32;
    let mut chunk = commands.spawn((
        Transform::from_xyz(chunk_col as f32 * CHUNK as f32 * TILE,
                            -(chunk_row as f32) * CHUNK as f32 * TILE, 0.0),
        Visibility::default(),
        Chunk {
            min: Vec2::new(chunk_col as f32 * CHUNK as f32 * TILE,
                           -(chunk_row as f32) * CHUNK as f32 * TILE),
            max: Vec2::new((chunk_col + 1) as f32 * CHUNK as f32 * TILE,
                           -((chunk_row + 1) as f32) * CHUNK as f32 * TILE),
        },
    ));

    for row in chunk_row * CHUNK..((chunk_row + 1) * CHUNK).min(grid.tiles.len()) {
        for col in chunk_col * CHUNK..((chunk_col + 1) * CHUNK).min(grid.tiles[row].len()) {
            let id = grid.tiles[row][col];
            if id == 0 { continue; }
            chunk.with_child((
                Sprite::from_atlas_image(
                    assets.texture.clone(),
                    TextureAtlas { layout: assets.layout.clone(), index: id as usize - 1 },
                ),
                Transform::from_xyz(col as f32 * TILE, -(row as f32) * TILE, 0.0),
            ));
        }
    }
}

fn cull_chunks(camera: Single<&Transform, With<Camera2d>>, mut chunks: Query<(&Chunk, &mut Visibility)>) {
    let view = camera.translation.truncate();
    for (chunk, mut visibility) in &mut chunks {
        let center = (chunk.min + chunk.max) * 0.5;
        let radius = (chunk.max - chunk.min).length() * 0.5 + 800.0;
        *visibility = if center.distance(view) <= radius {
            Visibility::Visible
        } else {
            Visibility::Hidden
        };
    }
}
```

`with_child` spawns the sprite as a child of the chunk; hiding the chunk hides the children and
saves draw submissions. For a map too large for memory, despawn hidden chunks and rebuild them
from `MapGrid` when they come back — the grid stays authoritative.

### 4. Grid collision

```rust
fn solid_at(grid: &MapGrid, col: i32, row: i32) -> bool {
    if col < 0 || row < 0 {
        return true;                       // treat outside the map as solid
    }
    grid.tiles
        .get(row as usize)
        .and_then(|line| line.get(col as usize))
        .is_some_and(|id| grid.solid.contains(id))
}

fn overlaps_solid(grid: &MapGrid, center: Vec2, half: Vec2) -> bool {
    let left = ((center.x - half.x) / TILE).floor() as i32;
    let right = ((center.x + half.x - 0.001) / TILE).floor() as i32;
    let top = ((-(center.y + half.y)) / TILE).floor() as i32;
    let bottom = ((-(center.y - half.y) + 0.001) / TILE).floor() as i32;
    for row in top..=bottom {
        for col in left..=right {
            if solid_at(grid, col, row) {
                return true;
            }
        }
    }
    false
}

fn move_body(body: &mut Vec2, half: Vec2, delta: Vec2, grid: &MapGrid) {
    let steps = (delta.abs().max_element() / (TILE * 0.5)).ceil().max(1.0) as i32;
    let step = delta / steps as f32;
    for _ in 0..steps {
        let next_x = Vec2::new(body.x + step.x, body.y);
        if !overlaps_solid(grid, next_x, half) {
            body.x = next_x.x;
        }
        let next_y = Vec2::new(body.x, body.y + step.y);
        if !overlaps_solid(grid, next_y, half) {
            body.y = next_y.y;
        }
    }
}
```

World → row uses the same sign convention as spawning (`row = floor(-y / TILE)`). Keep that
conversion in one function; two copies with different signs is the usual "invisible wall" bug.

### 5. Edit a tile at runtime

```rust
fn dig_tile(
    mut commands: Commands,
    mut grid: ResMut<MapGrid>,
    mut tiles: Query<(Entity, &Tile, &mut Sprite)>,
    col: u32,
    row: u32,
    new_id: u32,
) {
    if let Some(cells) = grid.tiles.get_mut(row as usize) {
        if let Some(cell) = cells.get_mut(col as usize) {
            *cell = new_id;
        }
    }

    for (entity, tile, mut sprite) in &mut tiles {
        if tile.col != col || tile.row != row {
            continue;
        }
        if new_id == 0 {
            commands.entity(entity).despawn();
        } else if let Some(atlas) = &mut sprite.texture_atlas {
            atlas.index = new_id as usize - 1;
        }
        return;
    }
}
```

If the cell was empty there is no entity to update; spawn a new sprite from the grid. `Commands`
are deferred, so the despawn is applied at the next sync point, not immediately.

### 6. When to use a tilemap crate

One entity per tile is fine into the low tens of thousands. Beyond that, or for built-in chunk
culling, layers and tile animation, a third-party crate such as `bevy_ecs_tilemap` is the
appropriate tool. Check the crate's supported Bevy release before adding it: a crate pinned to an
older Bevy minor will not build against 0.20. This skill deliberately stays on built-in sprites so
it compiles with Bevy alone.

## Pitfalls

- **Tiles are blurry or bleed** → linear filtering samples the neighbouring atlas cell. Use
  `ImagePlugin::default_nearest()` or a nearest sampler, and make the layout match the image grid.
- **Every tile shows the same sprite** → the atlas `index` is 0-based while a Tiled gid is 1-based,
  or the layout's `columns`/`rows` do not match the sheet.
- **`TextureAtlasLayout::from_grid` arguments rejected** → `padding` and `offset` are
  `Option<UVec2>`, not `UVec2`; pass `None` or `Some(UVec2::splat(n))`.
- **Sprites overlap in the wrong order** → equal `z` is not a draw-order guarantee. Assign a
  distinct `z` per layer.
- **`SpriteBundle`/`Camera2dBundle` not found** → bundles were removed in 0.16. Spawn `Sprite`,
  `Transform`, `Camera2d` directly; required components fill in the rest.
- **Spawned tile cannot be queried in the same system** → `Commands` are deferred. Read it in a
  later system or use `commands.spawn(...).id()` and defer the work.
- **World → grid is off by one tile at negative coordinates** → `as i32` truncates toward zero;
  use `floor()` for negatives as well.
- **Player walks through thin floors at speed** → one large move per frame skips cells. Sub-step
  by at most half a tile.
- **Hiding a chunk still costs CPU** → `Visibility::Hidden` removes rendering, not the entities.
  Despawn far chunks if entity count or memory is the problem.
- **Frame rate collapses at 100k tiles** → one entity per tile. Use chunks, merge static layers,
  or move to a tilemap crate.
- **Camera zoom breaks collision** → the camera's projection scale does not change world
  coordinates; convert screen → world with the camera before dividing by `TILE`, and keep
  gameplay positions in world units.

## References

- Read `references/atlas-chunks-and-collision.md` for the atlas API table, gid/index math, chunk
  layout, collision conventions, the crate decision and a testing checklist.

## Related skills

- `bevy-ecs` — components, resources, queries, systems and `Commands` semantics.
- `bevy-save` — persisting edited grids and player position.
- `level-design` — layout, pacing and readability of the tile grid.
- `camera-systems` — follow, deadzone and bounds behaviour.
- `procedural-gen` — generating the integer grid before it is spawned.
