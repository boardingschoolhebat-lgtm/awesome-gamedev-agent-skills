# Defold tile sources and tile collisions

Reference material for `SKILL.md`. Targets **Defold 1.14.0**.

## Tile source anatomy

A `.tilesource` is a grid over one image:

| Property | Meaning |
|----------|---------|
| Image | The tilesheet; every tile has the same width and height |
| Tile width / height | Grid cell size in pixels — this is the size scripts must assume |
| Margin / spacing | Empty border around the sheet and between tiles |
| Collision | Optional image used to generate convex collision shapes per tile |
| Collision groups | Named groups (`ground`, `danger`, …) listed under the tilesource root |

Collision shapes are traced from the opaque pixels of the **Collision** image, not the visual
image, so a tile can look like a thin platform and collide as a full box (or the reverse).
Adding a collision image updates the editor preview with outlines on each tile.

Assign a tile to a group in the tilesource editor (paint mode). Tiles left in no group do not
collide. The default group is `default` for new tilesources.

## Making a tilemap collidable

1. Put the `.tilemap` on a game object.
2. Add a **Collision Object** component to the same game object.
3. Set the collision object's **Collision Shape** to the `.tilemap` file instead of adding
   primitive shapes.
4. Set **Mask** on the collision object to the groups that should collide with the tiles.
   The **Group** property is not used for tilemap shapes — tile groups come from the
   tilesource.
5. Keep `[physics] use_fixed_timestep = 1` in `game.project` and run gameplay physics in
   `fixed_update`, as with any physics object.

One collision object can reference one tilemap. A tilemap with several layers still produces
one collision object; layer visibility does not change collision.

## Physics messages

| Message | Sent when | Fields to read |
|---------|-----------|----------------|
| `collision_response` | Two collision objects stop overlapping | `other_id`, `other_position`, `own_group`, `other_group` |
| `contact_point_response` | Every frame two objects touch | `position`, `normal`, `distance`, plus group fields |
| `trigger_response` | A `trigger` collision object overlaps another | `enter`, `other_id`, `other_group` |

For tile collisions the tile's group arrives in the message; the official
[tilemap collision example](https://defold.com/examples/tilemap/collisions) checks
`message.own_group == hash("danger")` from the object that hits the tiles, so test both
group fields when the setup is not obvious.

## Coordinate system

Tile indices are 1-based; `(1, 1)` is the first cell above and to the right of the tilemap
component's origin. Cells left of and below the origin are `0, -1, -2, …`:

```text
+-------+-------+-------+-------+
|  0,3  |  1,3  |  2,3  |  3,3  |
+-------+-------+-------+-------+
|  0,2  |  1,2  |  2,2  |  3,2  |
+-------+-------+-------+-------+
|  0,1  |  1,1  |  2,1  |  3,1  |
+-------O-------+-------+-------+
|  0,0  |  1,0  |  2,0  |  3,0  |
+-------+-------+-------+-------+
```

So for a world position `p` and tile size `s`, with the tilemap game object at `o`:

```text
x = floor((p.x - o.x) / s.x) + 1
y = floor((p.y - o.y) / s.y) + 1
```

This assumes the tilemap object has no rotation and uniform scale. If it does, transform `p`
into the object's local space first (or keep level tilemaps axis-aligned).

## Runtime edits

```lua
tilemap.set_tile(url, layer, x, y, index, [transform_bitmask])
tilemap.set_tile("#tilemap", "ground", 8, 2, 0)   -- clear
```

- `index` is the tile's position in the tilesource; `0` clears the cell.
- `transform_bitmask` is `tilemap.H_FLIP`, `tilemap.V_FLIP`, `tilemap.ROTATE_90`,
  `ROTATE_180` or `ROTATE_270`, summed. Flip applies before rotation.
- The coordinates must be inside the bounds the map was created with. `set_tile` cannot
  extend the map; author the full extent once.
- Run physics debug after runtime edits to confirm the collision shape for the edited cell
  matches the new tile.

Reading tiles:

```lua
local index = tilemap.get_tile("#tilemap", "ground", x, y)          -- 0 = empty
local info  = tilemap.get_tile_info("#tilemap", "ground", x, y)     -- { index, h_flip, v_flip, rotate_90 }
local left, bottom, columns, rows = tilemap.get_bounds("#tilemap")  -- all layers collapsed
local tiles = tilemap.get_tiles("#tilemap", "ground")               -- tiles[row][column]
```

## Layer visibility and materials

```lua
tilemap.set_visible("#tilemap", "foreground", false)
```

Visibility affects rendering only; collisions stay active. To tint or fade a layer, assign a
custom material and animate its `tint` constant — editing the shared builtin material changes
every tilemap that uses it.

## Debug checklist

1. Physics debug on: do shapes match the art at the edges and on slopes?
2. Walk into every collision group; confirm each produces the expected message.
3. Confirm decorative tiles produce no collision (`default` group left empty).
4. Clear and place a tile at runtime; confirm art and collision both change.
5. Hide a layer; confirm only rendering changes.
6. Bundle a desktop build and repeat 1–5 — headless runs simulate physics but draw nothing.
