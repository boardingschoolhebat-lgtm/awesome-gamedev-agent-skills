---
name: unreal-tilemap
description: >
  Build Paper 2D tile levels in Unreal Engine 5.8: tile sets and tile map assets, layers,
  UPaperTileMapComponent CreateNewTileMap/SetTile/GetTile, collision rebuilds, pixel-per-unit
  scaling, and runtime tile edits. Use when an Unreal 2D project needs a tilemap, tileset,
  Paper2D tile layer, or tile collision. Targets UE 5.8 with the Paper2D plugin.
---

# Unreal Paper 2D tilemaps

Paper 2D has a real tilemap: a `UPaperTileMap` asset of layers, painted from a `UPaperTileSet`,
rendered and collided through `UPaperTileMapComponent`. Targets **Unreal Engine 5.8** with the
**Paper2D** plugin enabled.

## When to use

- Use when an Unreal 2D project needs painted tile levels, tileset slicing, tile collision, or
  runtime tile changes.
- Use when a tile map component does not render, `SetTile` does nothing, or tile collision is
  missing after edits.

**When *not* to use:** character movement on the level → `unreal-2d-movement`; level pacing →
`level-design`; 3D landscapes → Landscape/World Partition; UMG → `unreal-ui`; Blueprint-only
gameplay → `unreal-blueprints`.

## How Paper 2D tilemaps fit together

| Object | Job |
|--------|-----|
| `UPaperTileSet` | A texture plus tile size, margin, padding, and per-tile metadata (collision, terrain). |
| `UPaperTileMap` | A grid asset with one or more `UPaperTileLayer`s and a pixels-per-unreal-unit scale. |
| `UPaperTileLayer` | One layer of cells, a name, and `bLayerCollides`. |
| `FPaperTileInfo` | A cell's contents: `TileSet` + `PackedTileIndex`. |
| `UPaperTileMapComponent` | Renders a tile map and owns or references one; the scripting surface. |

A tile map component either **owns** its map (created with `CreateNewTileMap`) or **references**
a shared tile map asset. `SetTile`, `ResizeMap` and similar edits only work on owned maps —
`OwnsTileMap()` tells you which case you are in.

## Core workflow

1. **Enable Paper2D.** Edit ▸ Plugins ▸ Paper2D; restart the editor. Without it, the asset types
   and the component do not exist.
2. **Create the tile set.** Import the tileset texture, then create a Tile Set from it and set
   tile size, margin and padding to match the art exactly. Optional collision data belongs to
   the tile set, not the level.
3. **Create the tile map.** Either paint a Tile Map asset in the Tile Map editor (the normal
   content workflow) or let a component own a generated map via `CreateNewTileMap`.
4. **Pick the scale.** `PixelsPerUnrealUnit` converts pixels to centimetres: with `1.0`, a 32 px
   tile is 32 uu. Match it to the sprites and the camera so the tiles are not tiny or enormous.
5. **Layer deliberately.** Ground on layer 0, decoration on layer 1 with `bLayerCollides =
   false`; collision is per layer and also depends on the map/component having collision
   enabled.
6. **Script through the component.** `GetTile(X, Y, Layer)` returns `FPaperTileInfo`;
   `SetTile(X, Y, Layer, Info)` writes a cell. Call `RebuildCollision()` once after a batch of
   edits, not per tile.
7. **Verify in a packaged build.** Check tile alignment against sprites, collision on every edge,
   and that the Paper2D plugin is cooked into the build.

## Patterns

### 1. An actor that owns a generated tile map

```cpp
// TileLevelActor.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "TileLevelActor.generated.h"

class UPaperTileMapComponent;
class UPaperTileSet;

UCLASS()
class MYGAME_API ATileLevelActor : public AActor
{
    GENERATED_BODY()

public:
    ATileLevelActor();

    UFUNCTION(BlueprintCallable, Category = "Tilemap")
    void BuildFromGrid(const TArray<int32>& Cells, int32 Width, int32 Height);

protected:
    UPROPERTY(VisibleAnywhere, Category = "Tilemap")
    TObjectPtr<UPaperTileMapComponent> TileMap;

    UPROPERTY(EditAnywhere, Category = "Tilemap")
    TObjectPtr<UPaperTileSet> TileSet;

    UPROPERTY(EditAnywhere, Category = "Tilemap")
    int32 TileSize = 32;                       // pixels
};
```

```cpp
// TileLevelActor.cpp
#include "TileLevelActor.h"
#include "PaperTileMapComponent.h"
#include "PaperTileSet.h"
#include "PaperTileLayer.h"

ATileLevelActor::ATileLevelActor()
{
    PrimaryActorTick.bCanEverTick = false;
    TileMap = CreateDefaultSubobject<UPaperTileMapComponent>(TEXT("TileMap"));
    RootComponent = TileMap;
}

void ATileLevelActor::BuildFromGrid(const TArray<int32>& Cells, int32 Width, int32 Height)
{
    if (!TileSet || Width <= 0 || Height <= 0)
    {
        return;
    }

    // Replaces any previous owned map; 1.0 pixel per unreal unit keeps 32 px tiles at 32 uu.
    TileMap->CreateNewTileMap(Width, Height, TileSize, TileSize, 1.0f, true);

    for (int32 Y = 0; Y < Height; ++Y)
    {
        for (int32 X = 0; X < Width; ++X)
        {
            const int32 Value = Cells.IsValidIndex(Y * Width + X) ? Cells[Y * Width + X] : 0;
            if (Value == 0)
            {
                continue;
            }

            FPaperTileInfo Info;
            Info.TileSet = TileSet;
            Info.PackedTileIndex = Value - 1;   // grid ids are 1-based, tile indices 0-based
            TileMap->SetTile(X, Y, 0, Info);
        }
    }

    // SetTile does not update collision; rebuild once after all edits.
    TileMap->RebuildCollision();
}
```

`CreateNewTileMap(MapWidth, MapHeight, TileWidth, TileHeight, PixelsPerUnrealUnit,
bCreateLayer)` replaces the component's map and, when `bCreateLayer` is true, creates an empty
layer you can write into. `PackedTileIndex` indexes the tile set's tiles, not pixels; compute it
from the tile set's columns when importing an external map.

### 2. Read and edit a cell

```cpp
FPaperTileInfo ATileLevelActor::GetCell(int32 X, int32 Y, int32 Layer) const
{
    return TileMap ? TileMap->GetTile(X, Y, Layer) : FPaperTileInfo();
}

void ATileLevelActor::ClearCell(int32 X, int32 Y, int32 Layer)
{
    if (!TileMap)
    {
        return;
    }
    // An empty info (no TileSet) clears the cell.
    TileMap->SetTile(X, Y, Layer, FPaperTileInfo());
    TileMap->RebuildCollision();          // batch edits, then rebuild once
}
```

`GetTile` returns a copy; `IsValid()` on the info tells you whether the cell is empty. Layer
indices start at 0 and must exist — writing to layer 5 of a one-layer map silently fails or
asserts depending on the build.

### 3. World position to tile

```cpp
FIntPoint ATileLevelActor::WorldToTile(const FVector& World) const
{
    const FVector Local = TileMap->GetComponentTransform().InverseTransformPosition(World);
    // Paper2D tile maps place tile (0,0) with its corner at the component origin,
    // tiles growing along +X and +Y in local space.
    return FIntPoint(
        FMath::FloorToInt(Local.X / TileSize),
        FMath::FloorToInt(Local.Y / TileSize)
    );
}
```

Convert to **local** space first: a rotated or scaled actor otherwise reports cells that do not
match the art. If the project uses a different origin convention (centre of tile 0,0), apply the
same offset in one helper and use it everywhere.

### 4. Painting in the Tile Map editor

- Open the Tile Map asset, pick the tile set in the palette, choose the layer, and paint.
- Use the layer list to hide/lock layers; keep collision tiles on a dedicated layer.
- Brush, fill and picker tools operate per layer; a fill on the wrong layer is a common cause of
  "the level looks right but nothing collides".
- Save the asset before running PIE; unsaved tile map edits are not visible to the game.

### 5. Importing a Tiled or JSON layout

Paper 2D has **no built-in runtime Tiled loader**. Convert the external layout to your own grid
and call `SetTile`:

```text
Tiled gid -> tile set local index:  index = gid - firstgid
cell -> FPaperTileInfo:             Info.TileSet = TileSet; Info.PackedTileIndex = index;
```

Load the JSON in the editor (import as a `UDataAsset` or a `UDeveloperSettings` table) or convert
it at build time into a data table; do not fetch it over HTTP at runtime. Tiled 1.5+ packs flip
flags into the gid's high bits — mask them before subtracting `firstgid`, and apply flips through
`FPaperTileInfo` flags if the tile set supports them.

### 6. Runtime edits and performance

- Batch `SetTile` calls and call `RebuildCollision()` once; every rebuild recreates the body
  setup and is expensive.
- For a destructible area, edit only the affected tiles and rebuild that layer; for large changes,
  hide the component and swap in a regenerated map.
- Tile maps are rendered in batches per layer, so a full map is cheap to draw; the cost is the
  collision rebuild and the number of components, not the number of visible tiles.
- Keep tile maps static (`Mobility = Static`) unless they really change at runtime; a movable
  tile map loses static lighting and costs more to render.

## Pitfalls

- **Paper2D types are missing** → the plugin is disabled. Enable it and restart; the project's
  `.uproject` must list it for the build.
- **`SetTile` does nothing** → the component references a shared tile map asset instead of owning
  one. `OwnsTileMap()` is false; use `CreateNewTileMap` or edit the asset in the Tile Map editor.
- **Tiles render but nothing collides** → `SetTile` does not rebuild collision, the layer's
  `bLayerCollides` is false, or the component's collision is disabled. Call
  `RebuildCollision()` and check the layer and component settings.
- **Collision update tanks the frame** → `RebuildCollision()` inside the edit loop. Batch edits,
  rebuild once.
- **Tiles are the wrong size** → `PixelsPerUnrealUnit` does not match the sprite scale, or the
  tile set's tile size/margin/padding is wrong. Fix the asset, not the actor scale.
- **Wrong tile appears** → the packed index is 0-based while the grid/import ids are 1-based, or
  the tile set's columns changed. Recompute from the tile set.
- **Tiles are offset from sprites** → a rotated/scaled component in the world-to-tile math, or a
  different origin convention between the painter and the collision code.
- **Edits disappear after PIE** → the tile map asset was not saved, or the level builds a map at
  BeginPlay and overwrites painted edits. Decide who owns the map.
- **Lighting looks flat or wrong** → movable tile map or unlit material. Paper 2D tile maps are
  usually unlit sprites; light them deliberately or not at all.
- **Package fails or tiles are missing in the build** → Paper2D plugin not enabled for the target,
  or the tile set/tile map assets are not referenced by anything cooked. Add them to
  `Additional Asset Directories to Cook` or reference them from a cooked asset.

## References

- Read `references/tilesets-tilemaps-and-collision.md` for the Paper2D API table, tile set and
  layer setup, coordinate math, collision rules and a test checklist.

## Related skills

- `unreal-2d-movement` — Paper2D characters that walk on the tile map.
- `level-design` — layout, pacing and readability of the grid.
- `unreal-blueprints` — Blueprint-only tile map actors and edit tools.
- `physics-tuning` — collision response and stability on tile geometry.
- `godot-tilemap` / `unity-tilemap-2d` / `bevy-tilemap` — the same concept in other engines.
