---
name: roblox-tilemap
description: >
  Build grid levels in Roblox from parts, Models and Terrain: choose the representation, convert
  a Luau tile grid to world positions, batch instance creation, fill terrain with FillBlock,
  place models with PivotTo, tag tile types with CollectionService, stream chunks, and import
  Tiled JSON on the server. Use when a Roblox place needs a tilemap, grid-based level, generated
  map, terrain fill, or chunk streaming. Targets Roblox's rolling platform APIs.
---

# Roblox tilemaps

Roblox has no tilemap object. A grid level is either **parts/models** you place yourself or
**Terrain voxels** you fill, plus Luau data that says what is where. This skill picks between
them and builds the pipeline on the server. Targets Roblox's **rolling platform APIs**.

## When to use

- Use when a Roblox place needs a grid-based level, a generated map, tile collision, terrain
  filling, chunk streaming, or a Tiled/Luau layout imported at runtime.
- Use when a map built from thousands of individual parts is slow to load or to replicate.

**When *not* to use:** physics of moving assemblies → `roblox-physics`; character movement →
`roblox-characters`; remote validation → `roblox-networking`; UI → `roblox-ui`; cross-engine
level design → `level-design`; data persistence → `roblox-datastores`.

## Choose the representation first

| Representation | Use when | Cost |
|----------------|----------|------|
| `Terrain` voxels | solid ground, caves, hills, big organic maps | 4-stud voxel resolution; cheap collision, no per-tile instances |
| One `Part` per tile | flat grid, few tile types, simple collision | one instance per tile; thousands replicate and render poorly |
| One `Model` per tile | tiles with decoration, pivots, multiple parts | heavier than a Part; use `PivotTo` |
| One merged part or mesh per chunk | large static map with a few materials | cheapest to render; edits require rebuilding the chunk |

Pick one primary representation per layer; mixing Terrain and parts for the same surface produces
z-fighting and doubled collision.

## Core workflow

1. **Fix the tile size in studs.** Terrain snaps to its voxel grid (4 studs by default); parts can
   use any size. Write the conversion once: `world = origin + Vector3.new(col, 0, row) * TILE`.
2. **Keep the grid as data.** A Luau module (or JSON decoded on the server) with layers of
   integer ids; `0` means empty. Treat it as the source of truth, not the instances.
3. **Build on the server only.** Parent the result to a `Folder` in `Workspace`; clients must not
   create the authoritative map, or they will desync and duplicate it.
4. **Batch creation.** Set properties before parenting, reuse a template, and yield between
   batches so the server does not stall a frame.
5. **Fill terrain in runs.** `Terrain:FillBlock(cframe, size, material)` fills a box; fill a
   horizontal run of tiles per call instead of one voxel at a time.
6. **Place models with `PivotTo`.** For part tiles set `CFrame`/`Position`; for models use
   `model:PivotTo(cframe)` so the pivot, not an arbitrary child, defines the position.
7. **Tag and attribute.** `CollectionService:AddTag(part, "Tile_Wall")` and
   `part:SetAttribute("GridX", col)` give gameplay code stable hooks that survive a rebuild.
8. **Stream large maps.** For big worlds, build chunk models around 64 studs, enable
   `Workspace.StreamingEnabled`, and use `Player:RequestStreamAroundAsync` before teleports.

## Patterns

### 1. Grid to world position

```lua
local TILE = 8                 -- studs per tile
local ORIGIN = Vector3.new(0, 0, 0)

local function tileCenter(col: number, row: number, height: number): Vector3
    return ORIGIN + Vector3.new(
        (col - 1) * TILE + TILE / 2,
        height,
        (row - 1) * TILE + TILE / 2
    )
end

local function tileCFrame(col: number, row: number, height: number): CFrame
    return CFrame.new(tileCenter(col, row, height))
end
```

Keep one convention for the whole project: 1-based grid, row growing along +Z, column along +X.
A second convention in the importer is the usual source of a mirrored map.

### 2. Build part tiles in batches

```lua
local Workspace = game:GetService("Workspace")
local CollectionService = game:GetService("CollectionService")

local function buildTile(grid: { { number } }, parent: Folder)
    for row, cells in grid do
        for col, id in cells do
            if id ~= 0 then
                local part = Instance.new("Part")
                part.Name = "Tile_" .. id
                part.Size = Vector3.new(TILE, TILE, TILE)
                part.CFrame = tileCFrame(col, row, TILE / 2)
                part.Anchored = true
                part.Material = Enum.Material.SmoothPlastic
                part.Color = Color3.fromRGB(90, 120, 90)
                part.TopSurface = Enum.SurfaceType.Smooth
                part.BottomSurface = Enum.SurfaceType.Smooth

                part:SetAttribute("GridX", col)
                part:SetAttribute("GridY", row)
                part:SetAttribute("TileId", id)
                CollectionService:AddTag(part, "Tile")
                part.Parent = parent
            end
        end
        if row % 32 == 0 then task.wait() end     -- yield between batches
    end
end
```

`Anchored = true` is mandatory for a static level; an unanchored tile falls and replicates
motion. Set every property before `Parent` to avoid a replication spike per property assignment.

### 3. Fill terrain in runs

```lua
local Terrain = workspace.Terrain

local function fillRun(row: number, colStart: number, colEnd: number, id: number)
    local width = (colEnd - colStart + 1) * TILE
    local center = Vector3.new(
        (colStart - 1) * TILE + width / 2,
        TILE / 2,
        (row - 1) * TILE + TILE / 2
    )
    Terrain:FillBlock(CFrame.new(center), Vector3.new(width, TILE, TILE), Enum.Material.Grass)
end

local function buildTerrain(grid: { { number } })
    for row, cells in grid do
        local start = nil
        for col = 1, #cells + 1 do
            local solid = cells[col] == 1
            if solid and not start then
                start = col
            elseif not solid and start then
                fillRun(row, start, col - 1, 1)
                start = nil
            end
        end
    end
end
```

Terrain is voxel-based: a 1-stud tile size cannot be represented exactly, and a fill smaller than
the voxel grid may round. Use terrain when the tile size is a multiple of the voxel size, or when
the art does not need exact cell edges.

### 4. Model tiles and `PivotTo`

```lua
local template = game:GetService("ReplicatedStorage"):WaitForChild("Tiles"):WaitForChild("Tree")

local function placeModel(col: number, row: number, parent: Folder)
    local model = template:Clone()
    model:PivotTo(tileCFrame(col, row, 0))
    model:SetAttribute("GridX", col)
    model:SetAttribute("GridY", row)
    model.Parent = parent
end
```

`Model:PivotTo` moves the model so its pivot lands on the given `CFrame`; `Model:MoveTo` keeps a
different legacy behavior and can shove parts. Set the template's `PrimaryPart` or
`WorldPivot` so the pivot means "bottom centre of the tile", and document it for artists.

### 5. Import a Tiled layout on the server

```lua
local HttpService = game:GetService("HttpService")

local function loadTiled(url: string)
    local raw = HttpService:GetAsync(url)        -- requires HTTP requests enabled
    local map = HttpService:JSONDecode(raw)
    local firstGid = map.tilesets[1].firstgid or 1
    local layers = {}
    for _, layer in map.layers do
        if layer.type == "tilelayer" then
            local grid = {}
            for row = 1, layer.height do
                grid[row] = {}
                for col = 1, layer.width do
                    local gid = layer.data[(row - 1) * layer.width + col]
                    grid[row][col] = gid == 0 and 0 or gid - firstGid + 1
                end
            end
            layers[layer.name] = grid
        end
    end
    return layers
end
```

`HttpService:GetAsync` works only on the server and only when HTTP requests are enabled for the
place; for shipping, prefer a `ModuleScript` generated at build time over a runtime fetch. Tiled
1.5+ packs flip flags into the high bits of a gid — mask them before subtracting `firstgid`.

### 6. Chunking and streaming

```lua
local CHUNK = 32
local CHUNK_STUDS = CHUNK * TILE

local function chunkKey(col: number, row: number): string
    return math.floor((col - 1) / CHUNK) .. ":" .. math.floor((row - 1) / CHUNK)
end

-- Build one Folder/Model per chunk so streaming can load and unload whole regions.
local function newChunk(col: number, row: number): Folder
    local folder = Instance.new("Folder")
    folder.Name = "Chunk_" .. chunkKey(col, row)
    folder.Parent = workspace:FindFirstChild("Level")
    return folder
end
```

With `Workspace.StreamingEnabled`, keep each chunk model under roughly 64 cubic studs, set
`ModelStreamingMode` deliberately (`Atomic` for a chunk that must arrive whole), and call
`player:RequestStreamAroundAsync(position)` before a teleport. Client-side queries such as
`GetPartBoundsInBox` only see streamed-in parts, so never treat a client query as proof that
nothing exists there.

## Pitfalls

- **Server freezes while the map builds** → thousands of `Instance.new` calls in one frame. Batch,
  yield every few hundred parts, or prebuild the map in Studio.
- **Map is duplicated or different for each player** → it was built in a `LocalScript`. Build on
  the server; clients only decorate.
- **Parts fall through the world** → `Anchored` was left `false`, or it was set after parenting
  and physics ran first. Anchor before `Parent`.
- **Terrain does not line up with tile art** → terrain snaps to the voxel grid; a tile size that
  is not a multiple of it cannot be represented. Use parts for exact cell edges.
- **`FillBlock` with a tiny size does nothing visible** → the fill is below voxel resolution or
  entirely inside existing terrain; fill in runs at least one voxel wide.
- **Model lands offset from its tile** → the pivot is not where you think. Set `PrimaryPart` or
  `WorldPivot` and use `PivotTo`, not `MoveTo`.
- **Every tile is queryable and touchable** → set `CanCollide`, `CanTouch` and `CanQuery`
  deliberately; decorative tiles do not need all three.
- **Runtime hole is not walkable after removing a tile** → destroying the part is enough for
  parts, but terrain needs `Terrain:FillBlock(cframe, size, Enum.Material.Air)`.
- **`GetAsync` fails in production** → HTTP requests are disabled for the place, or the URL is
  not reachable from Roblox. Embed the map data instead.
- **Tiled map is mirrored or offset by one** → gid subtraction, flip bits, or a row/column
  convention mismatch between importer and builder.
- **Streaming makes distant props vanish** → that is expected; a client query cannot see
  unstreamed instances, and `WaitForChild` on a streamed model can block. Use tags and
  `GetInstanceAddedSignal`.
- **Editing a chunk is expensive** → rebuilding thousands of parts per edit. For destructible
  tiles keep a smaller editable area, or use terrain for the destructible layer.

## References

- Read `references/grid-parts-terrain-and-streaming.md` for the API table, terrain and part
  trade-offs, Tiled import details, streaming rules and a test checklist.

## Related skills

- `roblox-luau` — services, instances and the client/server model.
- `roblox-physics` — collision groups, queries and moving assemblies on the built level.
- `roblox-studio-workflow` — Explorer structure, tags and in-Studio verification.
- `roblox-networking` — validating client actions that modify the map.
- `level-design` — layout, pacing and readability of the grid.
- `procedural-gen` — generating the tile grid before it is built.
