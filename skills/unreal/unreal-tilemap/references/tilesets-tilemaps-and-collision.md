# Paper 2D tile sets, maps and collision (UE 5.8)

Depth for `unreal-tilemap`: the asset model, the component API, coordinate conventions and the
collision rules that make a Paper 2D level behave like its art.

## API used by the skill

| Call / type | Signature | Notes |
|-------------|-----------|-------|
| `UPaperTileMapComponent::CreateNewTileMap` | `(int32 MapWidth, int32 MapHeight, int32 TileWidth, int32 TileHeight, float PixelsPerUnrealUnit, bool bCreateLayer)` | Replaces the map; only meaningful for an owned map. |
| `UPaperTileMapComponent::SetTile` | `(int32 X, int32 Y, int32 Layer, FPaperTileInfo NewValue)` | Owned maps only; does not rebuild collision. |
| `UPaperTileMapComponent::GetTile` | `(int32 X, int32 Y, int32 Layer)` → `FPaperTileInfo` | Returns a copy; empty info is an empty cell. |
| `UPaperTileMapComponent::RebuildCollision` | `()` | Recreates the body setup; call once after edits. |
| `UPaperTileMapComponent::ResizeMap` | `(int32 NewWidthInTiles, int32 NewHeightInTiles)` | Owned maps only; keeps existing cells where possible. |
| `UPaperTileMapComponent::OwnsTileMap` | `()` → `bool` | Whether edits are allowed. |
| `FPaperTileInfo` | `{ TObjectPtr<UPaperTileSet> TileSet; int32 PackedTileIndex; }` | Cell contents; `IsValid()`/`GetTileIndex()`. |
| `UPaperTileSet` | asset | Texture, tile size, margin/padding, per-tile data. |
| `UPaperTileLayer` | object in a tile map | `LayerName`, `bLayerCollides`, width/height. |
| `UPaperTileMap` | asset | Layers, `PixelsPerUnrealUnit`, collision settings. |

Include paths: `PaperTileMapComponent.h`, `PaperTileSet.h`, `PaperTileLayer.h`,
`PaperTileMap.h`; module dependency `Paper2D`.

## Asset setup

1. Import the tileset texture with **Sprite** texture type and no compression artifacts
   (`TC_EditorIcon`/`TC_BC7` per project policy; pixel art usually wants nearest filtering).
2. Right-click the texture ▸ **Sprite Actions** ▸ **Create Tile Set** (or create a Tile Set asset
   and assign the texture), then set:
   - **Tile Size**: one cell in pixels.
   - **Margin**: border around the whole sheet.
   - **Padding**: gutter between cells.
3. Paint per-tile collision in the tile set if the project uses it; otherwise control collision
   per layer.
4. Create a **Tile Map** asset and choose the tile set in the editor palette.
5. Set **Pixels Per Unreal Unit** on the tile map (or pass it to `CreateNewTileMap`). This is the
   single scale knob between pixels and centimetres.

## Coordinate conventions

```text
local position of tile (X, Y) corner = (X * TileSize, Y * TileSize, 0) / PixelsPerUnrealUnit
tile under local position            = floor(local / (TileSize / PixelsPerUnrealUnit))
```

With `PixelsPerUnrealUnit = 1`, a 32 px tile is 32 uu and the math is just `floor(local / 32)`.
Paper 2D sprites use the same pixel-to-unit scale, so set the character sprite's pixels-per-unit
to match or the character will look wrong on the tiles.

## Layer rules

- Layer 0 is drawn first; later layers draw on top within the component.
- `bLayerCollides` only has an effect when the tile map/component has collision enabled.
- Put decorative tiles on a non-colliding layer so hiding or changing art cannot change physics.
- One-way platforms and slopes are not a layer flag; add them as separate actors or handle them
  in movement code.
- Layer names are editor-facing; code uses indices. Renaming a layer does not change its index,
  but reordering does.

## Collision

- `RebuildCollision()` recreates the component's body setup from the colliding layers.
- Collision uses the tile map's collision thickness/settings; thin tiles can tunnel fast actors —
  pair with `physics-tuning` and continuous/swept movement where needed.
- Collision channels: set the component's collision profile so the player capsule blocks on the
  tile layer and projectiles can query it.
- After changing tile art or tile set collision data, rebuild and re-test; the body setup is
  cached.
- For runtime holes, clear the cell and rebuild; do not disable the whole component for one tile.

## Painting workflow

| Tool | Use |
|------|-----|
| Brush | paint single cells on the active layer |
| Fill | flood an area on the active layer — check the layer first |
| Picker | sample an existing cell into the palette |
| Erase | clear a cell (empty `FPaperTileInfo`) |
| Layers panel | add, rename, hide, lock, set collision |

Save the asset before PIE. A tile map edited in the editor and a tile map generated at BeginPlay
are two different sources of truth; if both exist, the generated one wins and painted edits look
lost.

## Testing checklist

1. Tile set: every tile picks the intended cell (no margin/padding drift).
2. Tile map: tiles align with sprites at the project's pixels-per-unit.
3. Layers: hiding a decorative layer does not change collision; a colliding layer blocks the
   player.
4. Edges: walk the whole map border; no invisible walls or fall-through.
5. Runtime edit: clear a cell, rebuild, and confirm both visuals and collision change.
6. Origin transform: rotate and scale the actor, then re-check world-to-tile conversion.
7. Performance: `stat unit` and `stat scenerendering` while the map is visible; a static map should
   not add per-frame cost.
8. Packaged build: tiles and collision present after cooking (plugin enabled, assets cooked).
