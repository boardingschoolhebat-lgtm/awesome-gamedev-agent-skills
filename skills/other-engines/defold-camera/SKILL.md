---
name: defold-camera
description: >
  Camera work in Defold: the camera component (perspective and orthographic), view/projection
  matrices into the render script, following with smoothing and dead zones, look-ahead, screen
  shake, zoom, screen_to_world for mouse aim and world_to_screen for markers, and multi-camera
  setups. Use when a Defold game needs a follow camera, zoom, shake or mouse picking. Targets
  Defold 1.14.0.
---

# Defold cameras

Defold's camera component supplies a view matrix and a projection matrix to the render script;
gameplay code moves the camera game object, changes zoom, and converts between screen and world.
This skill covers follow behavior and the conversion APIs. Targets **Defold 1.14.0**.

## When to use

- Use when a Defold game needs a follow camera, smooth/dead-zone tracking, zoom, or screen shake.
- Use when mouse/touch aim misses its world target, or a marker's screen position is wrong.

**When *not* to use:** movement and input → `defold-core` + `input-systems`; tile levels →
`defold-tilemap`; save state → `defold-save`; general camera feel across engines →
`camera-systems`.

## Core workflow

1. **Add a camera component** to a game object, choose perspective or orthographic, set FOV or
   orthographic zoom, near/far.
2. **Let the render script use its matrices.** The camera component posts view/projection to the
   render script; assign them in `on_message` (`set_view_projection`).
3. **Move the camera game object**, not the matrices, for follow and shake.
4. **Follow with smoothing**: exponential damping toward a target plus a dead zone; add look-ahead
   from velocity.
5. **Convert coordinates** with `camera.screen_to_world` (aim) and `camera.world_to_screen`
   (markers).
6. **Shake as an offset** applied after follow, decayed over time, disabled by the accessibility
   option.

## Patterns

### 1. Render script receives the matrices

```lua
-- render/camera.render_script (attached in game.project)
function init(self)
    self.view = nil
    self.projection = nil
end

function update(self, dt)
    if not self.view then return end
    render.set_view(self.view)
    render.set_projection(self.projection)
end

function on_message(self, message_id, message, sender)
    if message_id == hash("set_view_projection") then
        self.view = message.view
        self.projection = message.projection
    end
end
```

The camera component sends `set_view_projection` with `view` and `projection`; assigning them is
what makes the camera affect rendering. Changing the camera's z position updates the view matrix
automatically.

### 2. Follow with smoothing and a dead zone

```lua
local FOLLOW_SPEED = 6          -- higher = snappier
local DEAD_ZONE = 48            -- pixels of slack before the camera moves

function init(self)
    self.cam = camera.get_camera("#camera")   -- camera component on this game object
    self.pos = go.get_position()
end

function update(self, dt)
    local target = go.get_position("/player")
    local delta = target - self.pos
    local distance = vmath.length(delta)

    if distance > DEAD_ZONE then
        -- move only the part beyond the dead zone, damped exponentially
        local desired = target - vmath.normalize(delta) * DEAD_ZONE
        local t = 1 - math.exp(-FOLLOW_SPEED * dt)
        self.pos = self.pos + (desired - self.pos) * t
    end

    local shake = self:shake_offset()
    go.set_position(self.pos + shake)
end
```

- Exponential damping (`1 - exp(-k*dt)`) is frame-rate independent; a raw `t = 0.1` is not.
- The dead zone prevents micro-jitter when the player idles.
- Clamp the camera to level bounds after smoothing, not before, or it fights the follow.

### 3. Look-ahead

```lua
local LOOK_AHEAD = 0.35   -- seconds of velocity

local function look_ahead_target(player_pos, velocity, dt)
    return player_pos + velocity * LOOK_AHEAD
end
```

Use the player's velocity (or input direction if velocity is noisy), clamp the offset, and blend
it in over ~0.3 s so direction changes do not snap the camera.

### 4. Zoom

```lua
-- Orthographic: multiplier, > 1 zooms in.
go.set("#camera", "orthographic_zoom", 2)

-- Perspective: field of view in degrees.
camera.set_fov("#camera", 60)
```

- In `ORTHO_MODE_FIXED`, `orthographic_zoom` is the effective zoom; in `AUTO_FIT`/`AUTO_COVER` it
  multiplies the computed zoom.
- Animate zoom toward a target (sprint, aim, boss) with the same damping; do not set it per frame
  from raw input.
- `camera.set_near_z`/`set_far_z` for depth range; keep near as large as the scene allows to
  preserve depth precision.

### 5. Screen to world (mouse aim) and world to screen (markers)

```lua
function on_input(self, action_id, action)
    if action_id == hash("aim") and action.pressed then
        -- Orthographic: screen x/y is enough; z is ignored/at near plane.
        local world = camera.screen_to_world("#camera", vmath.vector3(action.screen_x, action.screen_y, 0))
        go.set_position(world, "/aim_marker")
    end
end
```

- `camera.screen_to_world(camera, screen)` returns a world position; for a perspective camera the
  vector's z is the view depth in world units from the camera plane.
- `camera.screen_xy_to_world` converts screen XY at the near plane when you do not have a depth.
- `camera.world_to_screen(camera, world)` is the inverse for HUD markers and damage numbers.
- Screen coordinates are in the game's display space; account for `game.project` display scaling
  and window size.

### 6. Screen shake

```lua
local SHAKE_TIME = 0.25
local SHAKE_STRENGTH = 12

function init(self)
    self.shake_t = 0
    self.shake_mag = 0
end

function shake(self, magnitude)
    self.shake_mag = math.max(self.shake_mag, magnitude)
    self.shake_t = SHAKE_TIME
end

function shake_offset(self)
    if self.shake_t <= 0 then return vmath.vector3() end
    local falloff = self.shake_t / SHAKE_TIME
    return vmath.vector3(
        (math.random() * 2 - 1) * self.shake_mag * falloff,
        (math.random() * 2 - 1) * self.shake_mag * falloff,
        0)
end
```

Decay `self.shake_t` in `update`, apply the offset last, and gate it behind an accessibility
setting (see `accessibility`). Avoid per-frame `math.random` allocs in hot loops if profiling
shows pressure.

## Pitfalls

- **Camera does nothing** → the render script never assigned `message.view`/`message.projection`,
  or the camera component is not on the game object being moved.
- **Camera lag depends on frame rate** → raw lerp factor. Use `1 - exp(-k*dt)`.
- **Mouse aim offset from the cursor** → `screen_to_world` called with the wrong camera url, or
  display scaling not accounted for.
- **Shake moves the gameplay camera permanently** → offset applied to `self.pos` instead of added
  after it.
- **Zoom jitters** → zoom set directly from input each frame; damp toward a target instead.
- **Follow fights level bounds** → clamp after smoothing and keep the target inside bounds.
- **Multiple cameras both render** → only one camera should be active per render pass; use camera
  focus/messages deliberately, and test with two viewports.
- **Perspective picking ignores depth** → pass a z view depth for `screen_to_world`, or use
  `screen_xy_to_world` for near-plane picking.

## References

- Read `references/matrices-follow-and-picking.md` for the camera API table, orthographic modes,
  matrix flow, follow/shake math and a camera test checklist.

## Related skills

- `defold-core` — game objects, messages and the update loop.
- `defold-tilemap` — level bounds for camera clamping.
- `defold-save` — persisting camera/settings options.
- `camera-systems` — engine-neutral follow, dead zone and shake design.
- `accessibility` — motion/shake reduction options.
