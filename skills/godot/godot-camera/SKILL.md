---
name: godot-camera
description: >
  Camera2D work in Godot 4.7: follow setups, position smoothing, drag margins and offsets,
  smoothing limits, zoom, shake via offset, screen/world conversion, and multi-camera switching.
  Use when a Godot 2D game needs a follow camera, dead zone, room limits, zoom or shake. Targets
  Godot 4.7.
---

# Godot 2D cameras

`Camera2D` scrolls the canvas to follow its node. Godot provides smoothing, drag margins, limits
and offset; the skill is choosing which to use and not fighting them with manual lerps. Targets
**Godot 4.7**.

## When to use

- Use when a 2D game needs a follow camera, dead zone, level bounds, zoom, or screen shake.
- Use when the camera jitters, shows outside the level, or ignores smoothing.

**When *not* to use:** player movement → `godot-2d-movement`; 3D cameras → `godot-3d-essentials`;
engine-neutral camera design → `camera-systems`; UI → `godot-ui-control`.

## Core workflow

1. **Add a `Camera2D`** and make it current (`make_current()` or the enabled camera).
2. **Follow**: parent the camera to the player, or move it in `_physics_process` at the target's
   position.
3. **Enable smoothing** (`position_smoothing_enabled`, speed ~5–10) instead of lerping yourself.
4. **Add drag margins** (`drag_horizontal_enabled`, margins 0–1) for a dead zone.
5. **Set limits** to the level bounds and enable `limit_smoothed` so the camera eases into them.
6. **Use `offset` for look-ahead and shake**, summed from separate variables.
7. **Test** at several aspect ratios; limits and zoom interact.

## Patterns

### 1. Follow the player

```gdscript
extends Camera2D

@export var target: Node2D
@export var smoothing_speed := 8.0

func _ready() -> void:
    position_smoothing_enabled = true
    position_smoothing_speed = smoothing_speed
    if target:
        global_position = target.global_position
        reset_smoothing()

func _physics_process(_delta: float) -> void:
    if is_instance_valid(target):
        global_position = target.global_position
```

- With smoothing enabled, the view eases toward `global_position`; do not also `lerp` it.
- `reset_smoothing()` after a teleport so the camera snaps instead of flying across the map.
- Parenting the camera to the player is the simplest follow; limits still apply.
- `get_screen_center_position()` is the real view center when smoothing/limits shift it.

### 2. Dead zone with drag margins

```gdscript
func _ready() -> void:
    drag_horizontal_enabled = true
    drag_vertical_enabled = true
    drag_left_margin = 0.2
    drag_right_margin = 0.2
    drag_top_margin = 0.15
    drag_bottom_margin = 0.15
    drag_horizontal_offset = 0.0
    drag_vertical_offset = -0.1   # bias the dead zone upward
```

Margins are fractions of the screen from the center (0–1); 0.2 means the player can move ~20 % of
the half-screen before the camera follows. Drag margins work together with smoothing.

### 3. Limits

```gdscript
func set_level_bounds(rect: Rect2) -> void:
    limit_left = int(rect.position.x)
    limit_top = int(rect.position.y)
    limit_right = int(rect.end.x)
    limit_bottom = int(rect.end.y)
    limit_smoothed = true
```

- Limits are in canvas/world pixels, not tiles; multiply tile coordinates by tile size.
- `limit_smoothed = true` avoids a hard stop when smoothing reaches the edge.
- If the viewport is larger than the level, the camera cannot satisfy all limits; letterbox or
  clamp the zoom instead.
- `offset` can push the view past the limits by design; use it only for temporary effects.

### 4. Zoom

```gdscript
@export var zoom_level := Vector2.ONE

func _unhandled_input(event: InputEvent) -> void:
    if event.is_action_pressed("zoom_in"):
        zoom = (zoom * 1.1).clamp(Vector2(0.5, 0.5), Vector2(3, 3))
```

- `zoom` > 1 zooms in; the visible world area shrinks.
- Smooth zoom toward a target in `_process` rather than snapping per input.
- Re-check limits after zoom changes; the viewport in world units changes.
- Pixel-art: use integer zoom steps and `texture_filter` nearest to avoid shimmer.

### 5. Look-ahead and shake via offset

```gdscript
var _look := Vector2.ZERO
var _shake := Vector2.ZERO

func _physics_process(delta: float) -> void:
    var vel := Vector2.ZERO
    if is_instance_valid(target) and "velocity" in target:
        vel = target.velocity
    _look = _look.lerp(vel.normalized() * 60.0, 4.0 * delta)

    if _shake_time > 0.0:
        _shake_time -= delta
        var falloff := clampf(_shake_time / _shake_duration, 0.0, 1.0)
        _shake = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * _shake_strength * falloff
    else:
        _shake = Vector2.ZERO

    offset = _look + _shake
```

- Keep look-ahead and shake in separate variables and sum them; writing `offset` from two systems
  overwrites one.
- Decay shake with delta time; gate it behind an accessibility option.
- `offset` does not affect `global_position`, so limits are not corrupted.

### 6. Multiple cameras

```gdscript
func focus_room(room_cam: Camera2D) -> void:
    room_cam.make_current()
```

- Only one `Camera2D` is current per viewport; `make_current()` switches.
- `enabled = false` disables a camera without freeing it.
- `custom_viewport` renders a camera into a SubViewport (minimap, split screen).
- On switch, call `reset_smoothing()` to avoid a glide from the previous position.

## Pitfalls

- **Camera jitters** → manual lerp plus built-in smoothing, or moving the camera in `_process`
  while the player moves in `_physics_process`. Use one loop and one smoothing layer.
- **Camera shows outside the level** → limits unset/default, or the viewport is larger than the
  level. Set limits and clamp zoom.
- **Hard stop at the edge** → `limit_smoothed` off. Enable it.
- **Smoothing ignored after teleport** → the camera glides across the map. Call
  `reset_smoothing()`.
- **Dead zone does nothing** → drag margins set but `drag_horizontal_enabled`/
  `drag_vertical_enabled` false.
- **Shake disappears while moving** → look-ahead and shake both assign `offset`. Sum them.
- **Shake moves the camera permanently** → adding to `global_position`. Use `offset`.
- **Zoom breaks limits** → visible world area changed; recheck bounds.
- **`global_position` is not the view center** → use `get_screen_center_position()` for UI or
  spawning at the view center.
- **Two cameras fight** → both current/enabled. Make one current per viewport.

## References

- Read `references/smoothing-limits-and-shake.md` for the Camera2D property table, smoothing
  semantics, limit math, shake patterns and a camera test checklist.

## Related skills

- `godot-2d-movement` — the player the camera follows.
- `godot-tilemap` — tile size and level bounds for limits.
- `camera-systems` — engine-neutral follow/dead-zone/shake design.
- `accessibility` — motion and shake reduction options.
- `defold-camera` — the same problems in Defold.
