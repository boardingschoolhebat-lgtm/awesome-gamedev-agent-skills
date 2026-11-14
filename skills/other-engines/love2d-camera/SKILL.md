---
name: love2d-camera
description: >
  Camera work in LÖVE 11.5: a transform-based 2D camera (translate/scale/rotate), follow with
  smoothing and dead zone, level clamping, zoom, parallax layers, screen shake, and converting
  mouse/screen coordinates to world coordinates. Use when a LÖVE game needs a scrolling camera,
  zoom, shake or parallax. Targets LÖVE 11.5.
---

# LÖVE 2D cameras

LÖVE has no camera object; the camera is a transform you apply in `love.draw` and invert for
input. This skill covers the transform math, follow behavior, clamping, parallax and picking.
Targets **LÖVE 11.5**.

## When to use

- Use when a LÖVE game needs a scrolling/following camera, zoom, shake or parallax background.
- Use when mouse clicks land in the wrong place, or the camera drifts at level edges.

**When *not* to use:** the main loop and input → `love2d-core`; tile levels → `love2d-tilemap`;
saving → `love2d-save`; engine-neutral camera design → `camera-systems`.

## Core workflow

1. **Keep camera state** as `x, y, zoom, rotation` in a table.
2. **Apply the transform** in `love.draw`: translate to screen center, scale, rotate, translate by
   `-camera.x, -camera.y`.
3. **Follow** a target with damping and a dead zone in `love.update(dt)`.
4. **Clamp** the camera so the view stays inside level bounds (accounting for zoom).
5. **Draw parallax layers** with their own factors before the world.
6. **Invert the transform** for mouse picking: `world = (screen - center) / zoom + camera`.
7. **Reset** with `love.graphics.push("all")`/`pop()` so the transform does not leak.

## Patterns

### 1. Camera module

```lua
local Camera = {}
Camera.__index = Camera

function Camera.new(x, y)
    return setmetatable({ x = x or 0, y = y or 0, zoom = 1, rotation = 0, shake = 0 }, Camera)
end

function Camera:attach()
    local w, h = love.graphics.getDimensions()
    love.graphics.push("all")
    love.graphics.translate(w / 2, h / 2)
    love.graphics.scale(self.zoom)
    love.graphics.rotate(self.rotation)
    love.graphics.translate(-self.x, -self.y)
end

function Camera:detach()
    love.graphics.pop()
end

function Camera:toWorld(sx, sy)
    local w, h = love.graphics.getDimensions()
    local dx, dy = (sx - w / 2) / self.zoom, (sy - h / 2) / self.zoom
    local c, s = math.cos(-self.rotation), math.sin(-self.rotation)
    return self.x + dx * c - dy * s, self.y + dx * s + dy * c
end

return Camera
```

```lua
function love.draw()
    camera:attach()
    drawWorld()
    camera:detach()
    drawHUD()          -- HUD is drawn in screen space
end
```

- `push("all")` saves transform, scissor and color; `pop()` restores. A bare `push()` saves only
  the transform.
- Draw the HUD **after** `detach()`; otherwise it scrolls with the world.
- Rotation makes the inverse transform non-trivial; the formula above rotates the offset back.

### 2. Follow with smoothing and dead zone

```lua
local DEAD_ZONE = 48
local FOLLOW = 6

function Camera:follow(target, dt)
    local dx, dy = target.x - self.x, target.y - self.y
    local dist = math.sqrt(dx * dx + dy * dy)
    if dist <= DEAD_ZONE then return end

    local nx, ny = dx / dist, dy / dist
    local tx = target.x - nx * DEAD_ZONE
    local ty = target.y - ny * DEAD_ZONE

    local t = 1 - math.exp(-FOLLOW * dt)
    self.x = self.x + (tx - self.x) * t
    self.y = self.y + (ty - self.y) * t
end
```

- Frame-rate independent damping (`1 - exp(-k*dt)`).
- A dead zone stops micro-jitter when the player idles.
- For pixel-art, round the camera position only when drawing, not when smoothing, or the follow
  stutters.

### 3. Level clamping

```lua
function Camera:clamp(levelW, levelH)
    local w, h = love.graphics.getDimensions()
    local viewW, viewH = w / self.zoom, h / self.zoom
    if viewW < levelW then
        self.x = math.min(math.max(self.x, viewW / 2), levelW - viewW / 2)
    else
        self.x = levelW / 2
    end
    if viewH < levelH then
        self.y = math.min(math.max(self.y, viewH / 2), levelH - viewH / 2)
    else
        self.y = levelH / 2
    end
end
```

- Clamp after follow; clamping before fights the smoothing.
- If the level is smaller than the view, center it instead of clamping to a negative range.
- At zoom > 1 the view is smaller in world units; recompute on zoom change.

### 4. Zoom and parallax

```lua
function Camera:setZoom(z)
    self.zoom = math.max(0.25, math.min(z, 4))
end

function drawParallax(layer, factor)
    love.graphics.push("all")
    love.graphics.translate(
        -(camera.x - love.graphics.getWidth() / 2) * factor,
        -(camera.y - love.graphics.getHeight() / 2) * factor
    )
    love.graphics.draw(layer)
    love.graphics.pop()
end
```

- Parallax factor 0 = fixed to screen, 1 = moves with the world; use 0.2–0.6 for backgrounds.
- Parallax with a camera rotation needs the rotated offset; keep rotation off for parallax-heavy
  games.
- Zoom should be damped toward a target; do not set it from raw mouse wheel steps.

### 5. Shake

```lua
local shakeTime, shakeStrength = 0, 0

function Camera:addShake(strength, duration)
    shakeStrength = math.max(shakeStrength, strength)
    shakeTime = math.max(shakeTime, duration)
end

function Camera:updateShake(dt)
    if shakeTime <= 0 then return 0, 0 end
    shakeTime = shakeTime - dt
    local falloff = math.max(shakeTime / 0.25, 0)
    return love.math.random() * 2 - 1, love.math.random() * 2 - 1,
           shakeStrength * falloff
end
```

Apply the shake as a temporary offset in `attach()` (`translate(-x + sx, -y + sy)`), never by
adding to `camera.x`. Gate it behind an accessibility setting.

## Pitfalls

- **HUD scrolls** → drawn inside the camera transform. Draw it after `detach()`.
- **Mouse clicks offset** → using screen coordinates directly; invert the camera transform.
- **Transform leaks** → missing `pop()`, or drawing after `attach()` without restoring.
- **Camera jitters at edges** → clamping before smoothing, or clamping with the unzoomed view.
- **Camera shows outside the level** → no clamp, or level smaller than the view.
- **Follow stutters at low FPS** → `t = 0.1` instead of `1 - exp(-k*dt)`.
- **Shake accumulates** → added to `camera.x`; use a draw-time offset.
- **Parallax drifts on resize** → factors computed from window size rather than the camera.
- **Rotation breaks picking** → inverse transform ignores rotation.
- **Pixel-art shimmer** → fractional camera position; round at draw time or use integer zoom.

## References

- Read `references/transform-follow-and-picking.md` for the transform order, inverse math,
  clamping formulas, parallax and a camera test checklist.

## Related skills

- `love2d-core` — the loop and drawing that call the camera.
- `love2d-tilemap` — tile drawing and level bounds.
- `love2d-save` — persisting settings.
- `camera-systems` — engine-neutral follow/shake design.
- `pygame-camera` — the same manual camera in Python.
