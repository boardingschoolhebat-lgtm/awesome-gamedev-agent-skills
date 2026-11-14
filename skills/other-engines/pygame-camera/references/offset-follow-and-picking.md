# Offset, follow and picking (pygame-ce 2.5.8)

Depth for `pygame-camera`: coordinate spaces, damped follow, clamping, culling and parallax.

## Coordinate spaces

| Space | Origin | Used by |
|-------|--------|---------|
| World | level origin | entity positions, tile maps |
| Screen | window top-left | `screen.blit`, mouse, HUD |

```text
screen = (world - camera.pos) * zoom + screen_size/2
world  = (screen - screen_size/2) / zoom + camera.pos
```

- `camera.pos` is the world point at the center of the view.
- Mouse: `pygame.mouse.get_pos()` is screen space; convert before comparing with world positions.
- HUD: draw with screen coordinates only.
- Zoom scales distances around the view center; camera position does not change.

## Follow

```python
t = 1 - math.exp(-speed * dt)
camera.pos += (desired - camera.pos) * t
```

- `speed` ~4–8 for a soft follow, 10–15 for tight.
- Clamp `dt` (`min(dt, 1/30)`) so a stall does not teleport the camera.
- Dead zone: only follow the part of the offset beyond the radius.
- Look-ahead: `target + velocity * 0.3`, blended.

## Clamp

```text
view_w = screen_w / zoom
x_min  = view_w / 2
x_max  = level_w - view_w / 2
```

- If `x_min > x_max` (level narrower than view), use `level_w / 2`.
- Apply after follow and after any zoom change.
- Level bounds in world pixels.

## Zoom

- `zoom > 1` zooms in; view size in world units shrinks.
- Scaling sprites per frame is expensive; pre-scale or render the world to a surface and scale
  once.
- Integer zoom for pixel-art; keep the camera on integer pixels at draw time.
- Smooth zoom toward a target, not per wheel event.

## Culling

```text
view_rect = Rect(
    camera.pos.x - screen_w/(2*zoom) - margin,
    camera.pos.y - screen_h/(2*zoom) - margin,
    screen_w/zoom + 2*margin,
    screen_h/zoom + 2*margin,
)
```

- Skip sprites whose rect does not collide with `view_rect`.
- Margin ≥ half the largest sprite to avoid popping.
- Cull before `blit`, after updating positions.

## Parallax

```text
offset = (camera.pos - screen_center) * factor
```

- Draw the layer at `-offset`, tiled with modulo.
- Factor 0 pins to screen; 1 matches the world.
- Draw order: sky, far, mid, world, foreground, HUD.

## Shake

- Random offset × strength × falloff, decayed by `dt`.
- Apply at draw time; never mutate `camera.pos`.
- Accessibility toggle.

## Test checklist

1. Scrolling world; HUD fixed.
2. Mouse picking correct at zoom 0.5, 1, 2.
3. No outside-level pixels; small levels centered.
4. Follow smooth at 30/60/144 fps; dead zone stops jitter.
5. Zoom changes keep the view valid and do not blur.
6. Parallax aligns and tiles.
7. Shake decays without drift.
8. Culling does not pop sprites.
9. Resize recomputes view and clamp.
10. Pixel-art stays sharp at rest.
