# Grids, parts, terrain and streaming (Roblox)

Depth for `roblox-tilemap`: the platform limits that decide the representation, the APIs used,
and the checks that catch a map that only looks right in Studio.

## API used by the skill

| Call / property | Notes |
|-----------------|-------|
| `Instance.new("Part")` | Set `Size`, `CFrame`/`Position`, `Anchored`, `Material`, `Color`, surfaces, then `Parent`. |
| `PVInstance:PivotTo(cframe)` | Moves a Model/BasePart so its pivot lands on `cframe`; primary way to place models. |
| `Model:MoveTo(position)` | Legacy placement that keeps old behavior; can displace parts. Prefer `PivotTo`. |
| `Model.PrimaryPart` / `Model.WorldPivot` | Define what "the pivot" means for a tile template. |
| `Terrain:FillBlock(cframe, size, material)` | Fills solid terrain inside the box; `Enum.Material.Air` clears it. |
| `Terrain:FillRegion(region, resolution, material)` | Region3 form; resolution must suit the voxel grid. |
| `Terrain:Clear()` | Removes all terrain in the place. |
| `Workspace.StreamingEnabled` | Enables instance streaming for large places. |
| `Player:RequestStreamAroundAsync(position)` | Pre-streams an area before a teleport (server-side call). |
| `CollectionService:AddTag(instance, tag)` | Stable gameplay tag; `GetTagged` and added/removed signals. |
| `Instance:SetAttribute(name, value)` | Per-instance grid coordinates and tile ids. |
| `Workspace:GetPartBoundsInBox(cframe, size, params)` | Box overlap query over parts (not terrain). |
| `HttpService:GetAsync(url)` | Server-only; requires HTTP requests enabled for the place. |
| `HttpService:JSONDecode(string)` | Decodes a JSON layout loaded from disk or the web. |

Terrain collision is implicit: filled voxels collide without a part. Parts collide according to
`CanCollide`, and queries according to `CanQuery`.

## Terrain versus parts

| Question | Terrain | Parts |
|----------|---------|-------|
| Exact tile edges? | No — voxel resolution (4 studs by default) | Yes, any `Size` |
| Many small tiles? | Poor fit | Poor fit above a few thousand |
| Cheap collision? | Yes | One collider per part |
| Editable per cell? | Yes, refill the voxel | Destroy/recreate the part |
| Organic shapes? | Good | Needs meshes |
| Replication cost | Low (terrain is one object) | High (one instance per tile) |
| Materials/colors per cell | Per voxel material | Per part |

Rules of thumb:

- A flat 100×100 grid of 8-stud parts is 10,000 instances: prefer merged chunk geometry or
  terrain.
- A cave or island map is terrain: `FillBlock` runs or `WriteVoxels` for detailed shapes.
- A puzzle board, a tower defense lane or a sim plot is a part grid: small counts, exact cells,
  direct interaction.

## Grid conventions

```text
col 1 -> world X = 0 .. TILE
row 1 -> world Z = 0 .. TILE
cell center = (col - 0.5) * TILE, height, (row - 0.5) * TILE
```

Write the convention in one module and import it everywhere. A Tiled importer that writes
`grid[row][col]` while the builder reads `grid[col][row]` produces a transposed map that still
looks plausible on a square test level.

## Terrain details

- `FillBlock(cframe, size, material)` fills a box aligned to the terrain voxel grid; a box that
  does not cover a voxel may leave it unchanged.
- Filling runs along a row is much cheaper than one call per cell; group by material too.
- `Enum.Material.Water` fills swimmable water; `Air` removes terrain.
- Terrain has no per-voxel script instance: gameplay metadata lives in your grid, attributes on
  separate parts, or a parallel data structure.
- `Terrain:Clear()` affects the whole place; scope edits with `FillRegion` or saved regions
  instead.
- Terrain does not appear in `GetPartBoundsInBox`; query your grid or parts for gameplay volumes.

## Tiled import details

- `layer.data` is row-major, `width * height` entries; `0` is empty.
- `firstgid` differs per tileset; subtract `firstgid - 1` only for gids belonging to that
  tileset.
- Tiled 1.5+ flip flags live in the top bits: mask with `bit32.band(gid, 0x1FFFFFFF)` before
  subtracting.
- `layer.type == "tilelayer"` for tile data; `objectgroup` for spawn points and zones.
- Import to a plain Luau table, validate dimensions, then build. Never build directly from the
  decoded JSON in a loop that also yields, or a partial map becomes visible.
- Prefer generating a `ModuleScript` from the Tiled file at build time over `GetAsync` at
  runtime: no HTTP dependency, no load failure in production.

## Streaming rules

- `StreamingEnabled` streams parts and terrain around each player's focus; streamed-out instances
  do not exist on that client.
- Keep chunk models small (under ~64 cubic studs) so they arrive together; set
  `ModelStreamingMode` deliberately (`Atomic`, `Persistent`, `Nonatomic`).
- Client-side `Raycast`, `GetPartBoundsInBox` and `GetBoundingBox` only see streamed-in content;
  never use "no result" as proof that nothing is there.
- `Player:RequestStreamAroundAsync(position)` before teleporting prevents a streaming pause; call
  it on the server and allow time before moving the character.
- Tags work with streaming: `GetInstanceAddedSignal(tag)` fires on stream-in,
  `GetInstanceRemovedSignal(tag)` on stream-out. Clean up per-instance state on removal.
- `WaitForChild` on a streamed model can block indefinitely; use tags, attributes and
  `FindFirstChild` with a timeout.

## Testing checklist

1. Fresh server start: the map builds once, no duplicate folders, no errors in Output.
2. Join with two clients: both see the same layout; nothing is client-built.
3. Walk every map edge: no invisible walls, no fall-through, no gaps between chunks.
4. Remove a tile at runtime: parts disappear and collision updates; terrain is refilled with
   `Air`.
5. Teleport across the map with streaming on: `RequestStreamAroundAsync` prevents a long pause.
6. Query near the streaming boundary: results only include loaded parts; gameplay handles the
   absence.
7. Count instances: `#workspace.Level:GetDescendants()` stays within the budget you chose.
8. Test on a low-end device or with the device emulator: frame time and memory, not only Studio
   playtest.
9. Reload the place: generated maps rebuild identically from the same seed/grid.
