---
name: phaser-tilemap
description: >
  Build tile levels in Phaser 4.2: load Tiled JSON, CSV or 2D-array maps, add tilesets,
  create layers, enable tile collision by index, range or Tiled property, wire Arcade colliders,
  query and edit tiles at runtime, and set world/camera bounds. Use when a Phaser game loads a
  Tiled map, needs tile collisions, parallax layers, or dynamic tiles such as doors and breakables.
---

# Phaser tilemaps

Load and collide tile levels in Phaser 4.2. Targets **Phaser 4.2** for new projects; inspect the
installed major before editing an existing project.

A tilemap is data (Tiled JSON, CSV or a 2D array) plus tileset images. `createLayer` turns one
layer into a `TilemapLayer` game object; collision flags on that layer are what Arcade Physics
tests against.

## When to use

- Use when loading a Tiled map, adding tilesets, creating layers, enabling tile collisions,
  querying tiles for gameplay, or editing tiles at runtime.
- Use when a project contains `*.json` Tiled maps and `this.make.tilemap` calls.

**When *not* to use:** bodies, colliders and overlap basics → `phaser-arcade-physics`; game
config, scenes and the loader → `phaser-core`; level layout and pacing → `level-design`;
generating maps from noise → `procedural-gen`; Matter physics tile conversion is a different
path and is out of scope here.

## Core workflow

1. **Export from Tiled** as JSON (finite map, tile layer format CSV or Base64 uncompressed), and
   keep the tileset image files next to the map. Note the exact tileset name and tile size.
2. **Preload both assets.** `this.load.tilemapTiledJSON('map', 'map.json')` and
   `this.load.image('tiles', 'tiles.png')`. Embedding the image inside the JSON still needs the
   Phaser texture key.
3. **Create the map and tilesets.** `this.make.tilemap({ key: 'map' })`, then
   `map.addTilesetImage(tiledName, textureKey, tileWidth, tileHeight, margin, spacing)` — the
   first argument must match the tileset name used in Tiled.
4. **Create layers in draw order.** `map.createLayer('Background', tileset)` first, then
   `Ground`, then `Decor`. Set depth or scroll factor for parallax.
5. **Enable collision on the layer, not the map.** Use `setCollision`, `setCollisionBetween`,
   `setCollisionByProperty({ collides: true })`, or `setCollisionFromCollisionGroup()`.
6. **Collide with Arcade.** `this.physics.add.collider(player, groundLayer)`. Tiles without a
   collision flag are ignored, so an empty collider usually means step 5 was skipped.
7. **Bound the world.** Set `physics.world.setBounds` and `cameras.main.setBounds` to
   `map.widthInPixels` × `map.heightInPixels`, then follow the player.

## Patterns

### 1. Tiled JSON → layers → collision

```js
preload() {
  this.load.tilemapTiledJSON('level1', 'assets/level1.json');
  this.load.image('tiles', 'assets/tiles.png');          // texture key, not the file name
}

create() {
  const map = this.make.tilemap({ key: 'level1' });
  const tileset = map.addTilesetImage('terrain', 'tiles'); // Tiled tileset name, texture key
  if (!tileset) throw new Error('tileset name does not match the Tiled map');

  const background = map.createLayer('Background', tileset, 0, 0);
  const ground = map.createLayer('Ground', tileset, 0, 0);
  const decor = map.createLayer('Decor', tileset, 0, 0);

  background.setScrollFactor(0.5);        // simple parallax
  decor.setDepth(2);

  ground.setCollisionByProperty({ collides: true });
  this.physics.add.collider(this.player, ground);

  this.physics.world.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
  this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
  this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
}
```

`addTilesetImage` returns `null` when the name does not match; throwing early turns a silent
blank map into a clear error.

### 2. Collision by index, range or property

```js
ground.setCollision([1, 2, 3]);              // exact tile indexes
ground.setCollisionBetween(10, 20);          // inclusive range
ground.setCollisionByProperty({ collides: true });   // boolean property painted in Tiled
ground.setCollisionFromCollisionGroup();     // shapes authored in Tiled's collision editor

this.physics.add.collider(this.player, ground, (player, tile) => {
  if (tile.index === 12) this.damage(player); // per-tile reaction
});
```

Prefer properties over raw indexes: reordering the tileset then does not silently change which
tiles are solid. Arcade tile collision is a full-tile AABB — slopes and one-way tiles need
extra handling (`phaser-arcade-physics` covers body-level tricks).

### 3. Query tiles for gameplay

```js
const tx = map.worldToTileX(this.player.x);
const ty = map.worldToTileY(this.player.y);
const tile = ground.getTileAt(tx, ty);        // null when the cell is empty

const isSolid = tile !== null && tile.collides;
const worldX = map.tileToWorldX(tx);          // top-left corner of the cell
```

Query the layer that owns the tiles (`ground.getTileAt`) or the map with an explicit layer name.
`tile.collides` reflects the flags set in step 2, not the Tiled editor's collision editor unless
you used `setCollisionFromCollisionGroup`.

### 4. Runtime edits (doors, breakables, dug tiles)

```js
ground.removeTileAt(tx, ty);                  // clears the cell
ground.putTileAt(14, tx, ty);                 // places tile index 14
ground.putTileAt(0, tx, ty);                  // 0 also clears

// New indexes need collision flags re-applied if they were not part of the original set.
ground.setCollisionBetween(10, 20, true, true);
```

`putTileAt` and `removeTileAt` update the layer's collision data by default; pass the
`recalculateFaces` argument as `false` only when batching many edits and refresh afterwards. The
cell must be inside the map bounds.

### 5. Object layers for spawns and triggers

```js
const spawns = map.getObjectLayer('Spawns');
for (const obj of spawns.objects) {
  this.spawnEnemy(obj.x, obj.y, obj.name);
}
```

Object layers are data only: rectangles, points and polygons do not create bodies. Spawn a
physics body at the object's position, or build a `staticGroup` of zones for triggers.

### 6. CSV or 2D-array levels (no Tiled file)

```js
const map = this.make.tilemap({ data: rows, tileWidth: 32, tileHeight: 32 });
const layer = map.createLayer(0, 'tiles');
layer.setCollisionByExclusion([-1, 0]);       // everything except empty cells
```

Useful for procedurally generated rows: generate the 2D array, then build the map at runtime.

## Pitfalls

- **Blank map, no error** — `addTilesetImage` name or texture key is wrong, or the tileset image
  was never loaded. Log the return value and fail fast.
- **Tiles render but nothing collides** — collision flags were never set on the layer, or they
  were set on a different layer than the one in the collider.
- **`setCollisionByProperty` does nothing** — the Tiled property name/case differs (`collides`
  vs `Collides`), or the property was set on the tileset image instead of the tile.
- **Collision appears one tile off** — margin/spacing or tile size in `addTilesetImage` does not
  match the Tiled tileset, so the wrong tile image and flags line up.
- **Player walks off the map** — world and camera bounds were not set to `widthInPixels` /
  `heightInPixels`.
- **Parallax layer jitters** — scroll factors on tiled layers combined with camera follow and
  rounding; keep parallax factors simple and test at different camera speeds.
- **Layer order looks wrong** — later `createLayer` calls draw above earlier ones; use `setDepth`
  rather than reordering when the map order is fixed.
- **Dynamic edits do not collide** — the new tile index has no collision flag, or the edit
  happened outside the map bounds and returned `null`.
- **Colliders per tile** — one collider for the whole layer is enough; adding one per tile costs
  performance and leaks handlers.
- **Scaled layers shift collision** — scaling the layer scales its tile bodies; verify collisions
  after `setScale` instead of assuming the flags handle it.
- **Chunked/infinite Tiled maps** — export finite maps for this workflow; infinite maps need
  chunk-aware handling that this skill does not cover.
- **Matter tilemap mixed with Arcade** — a layer converted for Matter does not collide with
  Arcade bodies. Pick one physics system per layer.

## References

- Read `references/tiled-and-collision.md` for Tiled export settings, tileset arguments, the
  layer collision API, tile queries and edits, object layers and a debug checklist.

## Related skills

- `phaser-arcade-physics` — bodies, velocity, colliders and platformer/top-down movement.
- `phaser-core` — game config, scene lifecycle, loader and cameras.
- `level-design` — layout, pacing and readability of the tile grid.
- `procedural-gen` — generating the tile rows this skill renders.
- `camera-systems` — follow, deadzone and bounds behavior.
