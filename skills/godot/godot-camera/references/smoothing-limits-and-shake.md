# Smoothing, limits and shake (Godot 4.7)

Depth for `godot-camera`: Camera2D properties, how smoothing and limits interact, and safe
look-ahead/shake.

## Camera2D API

| Property / method | Notes |
|-------------------|-------|
| `position_smoothing_enabled` | Smoothly move toward the target position. |
| `position_smoothing_speed` | Higher = snappier; ~5–10 is common. |
| `rotation_smoothing_enabled` / `rotation_smoothing_speed` | Only if the camera rotates; `ignore_rotation` must be false. |
| `drag_horizontal_enabled` / `drag_vertical_enabled` | Enable dead-zone margins. |
| `drag_left/right/top/bottom_margin` | 0–1 fraction of the half-screen. |
| `drag_horizontal_offset` / `drag_vertical_offset` | Shift the dead-zone center (−1..1). |
| `limit_left/top/right/bottom` | World-pixel bounds for the view. |
| `limit_smoothed` | Ease into limits instead of a hard stop. |
| `limit_enabled` | Master switch for limits. |
| `offset` | Temporary view offset (look-ahead, shake); can exceed limits. |
| `zoom` | > 1 zooms in. |
| `anchor_mode` | Drag anchor (center or top-left). |
| `make_current()` | Make this the active camera. |
| `reset_smoothing()` | Snap the view to the target position. |
| `get_screen_center_position()` | Real view center after smoothing/limits. |
| `get_target_position()` | Position the camera is heading toward. |
| `align()` | Snap to the target immediately. |

## Smoothing semantics

- Smoothing moves the **view** toward the camera node's position; the node itself does not move.
- `global_position` therefore is not necessarily the screen center — use
  `get_screen_center_position()`.
- If you set the camera's position every physics tick, smoothing still applies to the view; do not
  add your own lerp on top or you get double smoothing and lag.
- Teleports: set position, then `reset_smoothing()`.
- `position_smoothing_speed` is a response speed, not a fixed pixels/second; tune by feel.

## Limits math

```text
visible_world_width  = viewport_width  / zoom.x
visible_world_height = viewport_height / zoom.y
left_limit  <= center_x - visible_world_width/2
right_limit >= center_x + visible_world_width/2
```

- If `level_width < visible_world_width`, no center satisfies both limits; clamp zoom or accept
  letterboxing.
- Limits are in world pixels; convert from tiles (`tile_x * tile_size`).
- `offset` can push the view past limits; do not use it for permanent framing.
- Enable `limit_smoothed` so the camera decelerates into the edge.

## Dead zone

```text
margin 0.2  -> player may move 20% of half-screen before camera follows
margin 1.0  -> camera only moves at the screen edge
```

- Enable both axes for a full dead zone; one axis is fine for side-scrollers.
- Use offsets to bias the zone (e.g. show more ahead of the player).
- Drag margins combine with smoothing without conflict.

## Look-ahead and shake

```gdscript
var _look := Vector2.ZERO
var _shake := Vector2.ZERO

func _process(delta: float) -> void:
    _look = _look.lerp(desired_look, 6.0 * delta)
    _shake = _shake.lerp(Vector2.ZERO, 12.0 * delta)
    offset = _look + _shake
```

- One writer per frame; sum the components.
- Shake: random direction × strength × falloff, decayed by delta.
- Look-ahead: velocity (or input direction) × seconds, clamped.
- Gate shake behind an accessibility setting.

## Multi-camera

- One current camera per viewport.
- `enabled = false` stops processing without freeing.
- `custom_viewport` + `SubViewport` for minimaps/split screen.
- On switch: `make_current()`, then `reset_smoothing()`.

## Test checklist

1. Follow: no jitter at rest; no lag spikes at 30/60/144 fps.
2. Dead zone: small moves do not scroll; large moves catch up.
3. Limits: no outside-level pixels at every zoom and aspect ratio.
4. `limit_smoothed`: no hard stop at edges.
5. Teleport/respawn: `reset_smoothing()` prevents a glide.
6. Shake: decays to zero, does not move the node, respects the toggle.
7. Look-ahead: direction changes blend, no snap.
8. Zoom: smooth, limits still valid, pixel-art stays crisp.
9. Camera switch: instant, correct view, no stale smoothing.
10. UI/markers use `get_screen_center_position()`, not `global_position`.
