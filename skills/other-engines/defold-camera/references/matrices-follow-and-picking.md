# Matrices, follow and picking (Defold 1.14.0)

Depth for `defold-camera`: the camera API, how matrices reach the render script, and the math
behind follow, zoom, shake and coordinate conversion.

## Camera API

| API | Form | Notes |
|-----|------|-------|
| `camera.get_camera` | `(url) -> camera` | Camera id for a camera component. |
| `camera.get_view` | `(camera) -> matrix4` | View matrix. |
| `camera.get_projection` | `(camera) -> matrix4` | Projection matrix. |
| `camera.get_fov` / `set_fov` | `(camera[, fov])` | Perspective field of view, degrees. |
| `camera.get_near_z` / `set_near_z` | `(camera[, z])` | Near clipping plane. |
| `camera.get_far_z` / `set_far_z` | `(camera[, z])` | Far clipping plane. |
| `camera.get_orthographic_zoom` / `set_orthographic_zoom` | `(camera[, zoom])` | Multiplier, > 1 zooms in. |
| `camera.get_orthographic_mode` / `set_orthographic_mode` | `(camera[, mode])` | `ORTHO_MODE_FIXED`, `AUTO_FIT`, `AUTO_COVER`. |
| `camera.get_orthographic_auto_zoom` | `(camera)` | Computed auto zoom. |
| `camera.screen_to_world` | `(camera, vector3) -> vector3` | Perspective z = view depth. |
| `camera.screen_xy_to_world` | `(camera, x, y) -> vector3` | Near-plane conversion. |
| `camera.world_to_screen` | `(camera, vector3) -> vector3` | HUD markers. |
| `camera.set_aspect_ratio` / `set_auto_aspect_ratio` | `(camera[, ratio])` | Manual or automatic aspect. |

The component also exposes `orthographic_zoom` as a property, so `go.set("#camera",
"orthographic_zoom", 2)` works at runtime.

## Matrix flow

```text
camera component
   │  set_view_projection { view, projection }
   ▼
render script
   render.set_view(view)
   render.set_projection(projection)
   ▼
draw calls use the matrices
```

- Moving/rotating the camera game object changes the view matrix; the component posts an update.
- The projection follows FOV/zoom, near/far and aspect ratio.
- The render script must store and apply both; a camera that moves but never renders is almost
  always a render script that ignored the message.
- The camera's z position matters for 2D: it determines what the orthographic camera sees along z.

## Orthographic modes

| Mode | Behavior |
|------|----------|
| `FIXED` | Zoom is exactly `orthographic_zoom`; the visible area depends on the window. |
| `AUTO_FIT` | Computes zoom so the `game.project` display area fits inside the window (letterbox). |
| `AUTO_COVER` | Computes zoom so the display area covers the window (crop). |

In `AUTO_FIT`/`AUTO_COVER` the user zoom multiplies the computed value; it is not ignored.

## Follow math

Frame-rate independent damping:

```lua
local t = 1 - math.exp(-speed * dt)
self.pos = self.pos + (desired - self.pos) * t
```

Dead zone:

```lua
local delta = target - self.pos
if vmath.length(delta) > DEAD_ZONE then
    local inner = target - vmath.normalize(delta) * DEAD_ZONE
    -- damp toward inner
end
```

- Dead zone in world units, converted from a screen-space tolerance if the camera zooms.
- Look-ahead: `target + velocity * LOOK_AHEAD`, blended over time.
- Clamp to level bounds after smoothing.
- For pixel-art games, round the camera position to the pixel grid at the end, or sprites shimmer.

## Shake

```text
offset = random_unit_vector * magnitude * (remaining / duration)
position = smooth_follow_position + offset
```

- Apply after follow and after clamping; never feed the shaken position back into `self.pos`.
- Use a decaying envelope (linear or squared) and a max magnitude.
- Cap shake frequency; per-frame random at high amplitude reads as noise, not impact.
- Gate behind the accessibility reduce-motion option.

## Coordinate conversion

- `screen_to_world(camera, vmath.vector3(screen_x, screen_y, depth))`:
  - Orthographic: x/y map to world; z is not a perspective depth.
  - Perspective: z is the distance from the camera plane in world units.
- `screen_xy_to_world(camera, x, y)` returns the near-plane point; use it when no depth is known.
- `world_to_screen(camera, world)` for markers; check z/behind-camera cases before drawing.
- GUI nodes use a separate coordinate space (`gui`), not the camera projection; convert
  deliberately or draw markers in the render script.

## Test checklist

1. Follow: no jitter at rest, no lag spikes when frame time varies.
2. Dead zone: small movements do not move the camera; large ones catch up smoothly.
3. Look-ahead: direction changes blend, no snap.
4. Bounds: camera never shows outside the level; corners clamp correctly at every zoom.
5. Zoom: smooth transition, no clipping of the near plane, HUD stays fixed.
6. Shake: decays to zero, never accumulates, respects the accessibility toggle.
7. Picking: mouse/touch aim lands on the cursor at 16:9, 4:3 and ultrawide, windowed and
   fullscreen.
8. Multiple cameras: only the intended camera renders; switching does not leave stale matrices.
9. Pixel-art: camera rounding keeps sprites stable.
