# Transform, follow and picking (LÖVE 11.5)

Depth for `love2d-camera`: the transform stack, inverse math for input, follow/clamp formulas and
parallax.

## Transform order

```lua
love.graphics.push("all")
love.graphics.translate(screenW/2, screenH/2)  -- 1. move origin to screen center
love.graphics.scale(zoom)                      -- 2. zoom around center
love.graphics.rotate(rotation)                 -- 3. rotate around center
love.graphics.translate(-cam.x, -cam.y)        -- 4. move world so cam is at center
-- draw world in world coordinates
love.graphics.pop()
```

Order matters: reversing 3 and 4 rotates around the world origin instead of the camera.

## Inverse transform (screen → world)

Without rotation:

```text
worldX = (screenX - w/2) / zoom + cam.x
worldY = (screenY - h/2) / zoom + cam.y
```

With rotation `r`:

```text
dx = (screenX - w/2) / zoom
dy = (screenY - h/2) / zoom
worldX = cam.x + dx*cos(-r) - dy*sin(-r)
worldY = cam.y + dx*sin(-r) + dy*cos(-r)
```

`love.mouse.getPosition()` returns screen coordinates in the window; on high-DPI displays LÖVE
already reports logical pixels.

## Follow math

```lua
local dist = math.sqrt(dx*dx + dy*dy)
if dist > DEAD_ZONE then
    local nx, ny = dx/dist, dy/dist
    local targetX, targetY = target.x - nx*DEAD_ZONE, target.y - ny*DEAD_ZONE
    local t = 1 - math.exp(-SPEED * dt)
    cam.x = cam.x + (targetX - cam.x) * t
    cam.y = cam.y + (targetY - cam.y) * t
end
```

- Exponential damping is frame-rate independent.
- Dead zone in world units; if you zoom, the same world distance covers fewer screen pixels.
- Look-ahead: target + velocity * seconds, clamped and blended.

## Clamp formulas

```text
viewW = screenW / zoom
viewH = screenH / zoom
cam.x in [viewW/2, levelW - viewW/2]
cam.y in [viewH/2, levelH - viewH/2]
```

If `viewW >= levelW`, center at `levelW/2`. Recompute after zoom changes and on window resize.

## Parallax

```text
offset = (cam.pos - screenCenter) * (1 - factor)
```

Draw the layer translated by that offset, outside the camera transform (or inside with the
computed offset). Factor 0 pins the layer to the screen; factor 1 moves it with the world.

- Multiple layers: sky 0.1, far 0.3, mid 0.6, foreground 1.0.
- Camera rotation complicates parallax; keep rotation off if possible.
- Parallax layers should be larger than the view to avoid gaps at edges.

## Shake

- Compute offset per frame, apply in `attach`, never mutate camera position.
- Decay with delta time; clamp magnitude; accessibility toggle.
- Use `love.math.random` for deterministic seeds if replays matter.

## Test checklist

1. World scrolls; HUD stays fixed.
2. Mouse picking lands on the cursor at zoom 0.5/1/2 and with rotation.
3. Camera never shows outside the level; small levels center.
4. Follow smooth at 30/60/144 fps; dead zone stops jitter.
5. Zoom smooth, clamps, and keeps the view valid.
6. Parallax layers align at screen edges and after resize.
7. Shake decays and does not drift.
8. Transform does not leak into HUD or the next frame.
9. Pixel-art: no shimmer at rest.
10. Window resize recomputes view and clamp.
