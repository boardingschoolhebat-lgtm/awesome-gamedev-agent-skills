# Phaser 4 tilemaps: Tiled setup, layers and collision

Reference material for `SKILL.md`. Targets **Phaser 4.2**.

## Tiled export settings

| Setting | Value | Why |
|---------|-------|-----|
| Format | JSON | `tilemapTiledJSON` parses it directly |
| Tile layer format | CSV or Base64 (uncompressed) | Avoid compression unless you add the matching loader flag |
| Orientation | Orthogonal | Isometric/staggered need different camera and body assumptions |
| Infinite | Off | Infinite/chunked maps are not covered by this workflow |
| Tile size | Match the game's pixel scale | Body sizes and world math derive from it |
| Embed tilesets | Either | The image still needs a Phaser texture key |

Keep the tileset name stable. `map.addTilesetImage(name, textureKey)` matches the **name**, not
the file name.

## Tileset arguments

```js
map.addTilesetImage(
  tilesetName,     // name from Tiled
  textureKey,      // key used in this.load.image
  tileWidth,       // defaults to the map's tileWidth
  tileHeight,
  tileMargin,      // transparent border around the sheet
  tileSpacing,     // gap between tiles
  gid              // first global id, when merging tilesets
);
```

Wrong margin/spacing produces shifted tile art and shifted collision faces; wrong `gid` produces
the wrong tile for a given index.

## Layer API

```js
const layer = map.createLayer(layerID, tileset, x, y);   // tileset may be an array
```

| Call | Effect |
|------|--------|
| `layer.setCollision(indexes, collides, recalculateFaces)` | Collision on specific indexes |
| `layer.setCollisionBetween(start, stop, collides, recalculateFaces)` | Inclusive index range |
| `layer.setCollisionByProperty({ collides: true })` | Tiles with matching Tiled properties |
| `layer.setCollisionByExclusion(indexes)` | Everything except the listed indexes |
| `layer.setCollisionFromCollisionGroup()` | Shapes from Tiled's collision editor |
| `layer.getTileAt(tileX, tileY)` | `Tile` or `null` |
| `layer.putTileAt(tile, tileX, tileY, recalculateFaces)` | Place or replace a tile |
| `layer.removeTileAt(tileX, tileY, replaceWithNull, recalculateFaces)` | Clear a cell |
| `layer.setDepth(n)` / `setScrollFactor(n)` | Draw order and parallax |
| `layer.setScale(n)` | Scales rendering and tile bodies — re-test collision |

The map mirrors many of these calls with a trailing layer name:
`map.setCollision([...], true, true, 'Ground')`, `map.getTileAt(x, y, false, 'Ground')`.

## Coordinates

- `map.worldToTileX(worldX)` / `worldToTileY(worldY)` — world pixels to tile coordinates.
- `map.tileToWorldX(tileX)` / `tileToWorldY(tileY)` — top-left corner of a cell in world pixels.
- `map.widthInPixels` / `map.heightInPixels` — full map size for bounds.
- `tile.pixelX` / `tile.pixelY` — the tile's world position for effects.

Tile coordinates are integers; world coordinates are pixels. Multiply by tile size when doing
your own math, and remember the camera scroll is already applied by these helpers.

## Object layers

```js
const layer = map.getObjectLayer('Spawns');
for (const obj of layer.objects) {
  // obj.x, obj.y are world pixels; obj.width/height for rectangles; obj.polygon for shapes
}
```

Object layers are data. Create bodies yourself:

```js
const zones = this.physics.add.staticGroup();
for (const obj of map.getObjectLayer('Triggers').objects) {
  const zone = this.add.zone(obj.x + obj.width / 2, obj.y + obj.height / 2, obj.width, obj.height);
  this.physics.add.existing(zone, true);
  zones.add(zone);
}
```

Tiled stores object `x`/`y` at the top-left for rectangles; Phaser zones expect a center, so add
half the width/height.

## Physics integration

```js
this.physics.add.collider(player, groundLayer);
this.physics.add.collider(player, groundLayer, (player, tile) => {
  // tile.index, tile.x, tile.y, tile.properties
});
```

- Tile collision is AABB per tile, 32×32 default from the tileset.
- Collision flags must be set on the layer before the first physics step.
- Arcade does not do slope or one-way tile collision; use body-level techniques or Matter.
- Tilemap layers converted for Matter (`this.matter.world.convertTilemapLayer(layer)`) do not
  interact with Arcade bodies.

## Debug checklist

1. `arcade: { debug: true }` — tile bodies line up with the art at map edges and corners.
2. Walk the full perimeter: world bounds and camera bounds match `widthInPixels`/`heightInPixels`.
3. Every solid tile type blocks; decorative tiles do not.
4. A per-tile collider callback receives the expected `tile.index`.
5. Runtime `putTileAt`/`removeTileAt` change both art and collision.
6. Parallax layers move at the intended factor and do not jitter against the camera.
7. Object-layer spawns land at the authored coordinates, not offset by half a tile.
8. Tile count and layer count are within budget; no per-tile colliders were added.
