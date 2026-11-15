# Events, instances and GML

Depth for `gamemaker-core`: event order, collisions, constructors, saves and tests.

## Event order (one step)

```text
Begin Step
  Step
    (instances in undefined order; do not rely on cross-instance order)
  End Step
Draw Begin
  Draw
  Draw End
Draw GUI Begin
  Draw GUI
  Draw GUI End
```

- Alarms tick before Step.
- Room transitions requested with `room_goto` happen after the current step.
- Cross-instance order is not guaranteed; use a controller object or a global queue when order
  matters.

## Collision matrix

| Need | Function |
|------|----------|
| Can I move there? | `place_meeting(x, y, obj)` |
| What did I hit? | `instance_place(x, y, obj)` |
| All hits in an area | `instance_place_list` / `collision_rectangle_list` |
| Point inside | `position_meeting(px, py, obj)` |
| Distance query | `instance_nearest(x, y, obj)` |

- `place_meeting` uses the calling instance's mask at the given position.
- For precise melee, use `collision_rectangle` with a rectangle in front of the player.
- Collision events fire after movement; do not move inside them without a check.

## Structs vs objects

| Need | Use |
|------|-----|
| Data with methods, no events | struct/constructor |
| Needs Step/Draw/Collision | object + instance |
| Save/serialize simple data | struct + `json_stringify` |
| Many short-lived data records | struct/array, not instances |

## Save format

```json
{
  "v": 2,
  "room": "rm_level2",
  "player": { "x": 128, "y": 96, "hp": 80 },
  "flags": { "met_guide": true }
}
```

```gml
function save_game(_slot) {
    var _f = file_text_open_write("save_" + string(_slot) + ".json");
    file_text_write_string(_f, json_stringify({
        v: 2, room: room_get_name(room),
        player: { x: obj_player.x, y: obj_player.y, hp: obj_player.hp }
    }));
    file_text_close(_f);
}
```

- Validate `v` on load; fill missing fields with defaults.
- Never trust a save file's room name without checking the room exists.

## Test checklist

1. Sprite draws; Draw event calls `draw_self()`.
2. Diagonal speed equals cardinal speed.
3. Player slides along walls instead of sticking.
4. Collision mask matches the visual.
5. Alarm timers fire once and reset.
6. Room transition preserves intended globals.
7. Stale instance ids guarded with `instance_exists`.
8. Draw GUI HUD stays fixed while the camera moves.
9. Save/load round-trips position, room and health.
10. Old save version migrates without losing progress.
