---
name: pygame-camera
description: >
  Camera work in pygame-ce 2.5.8: a manual camera offset/zoom for scrolling worlds, smooth follow
  with a dead zone, level clamping, parallax, screen shake, world↔screen conversion for mouse
  aiming, and drawing only visible sprites. Use when a pygame game needs scrolling, zoom, shake or
  parallax. Targets pygame-ce 2.5.8.
---

# pygame cameras

pygame has no camera: you keep an offset (and optionally a zoom) and add it to every world draw.
The camera is therefore a small set of functions plus discipline about coordinate spaces.
Targets **pygame-ce 2.5.8**.

## When to use

- Use when a pygame game needs a scrolling/following camera, zoom, shake or parallax.
- Use when mouse clicks miss their targets after the world scrolls.

**When *not* to use:** the loop and sprites → `pygame-core`; tile levels → `pygame-tilemap`;
saving → `pygame-save`; engine-neutral design → `camera-systems`.

## Core workflow

1. **Keep a camera object** with `offset` (world position of the view center or top-left) and
   `zoom`.
2. **Follow** the target with exponential damping and a dead zone.
3. **Clamp** to level bounds using the zoomed view size.
4. **Convert** world→screen for drawing and screen→world for mouse input.
5. **Cull** sprites outside the view before drawing.
6. **Apply shake** as a draw-time offset, not by moving the camera.
7. **Keep the HUD in screen space**, drawn without the offset.

## Patterns

### 1. Camera with world→screen conversion

```python
import pygame
from pygame.math import Vector2

class Camera:
    def __init__(self, x=0.0, y=0.0, zoom=1.0):
        self.pos = Vector2(x, y)     # world point at the view center
        self.zoom = zoom

    def world_to_screen(self, point, screen_size):
        w, h = screen_size
        return (
            (point[0] - self.pos.x) * self.zoom + w / 2,
            (point[1] - self.pos.y) * self.zoom + h / 2,
        )

    def screen_to_world(self, point, screen_size):
        w, h = screen_size
        return Vector2(
            (point[0] - w / 2) / self.zoom + self.pos.x,
            (point[1] - h / 2) / self.zoom + self.pos.y,
        )
```

```python
def draw(screen, camera, sprites):
    for sprite in sprites:
        x, y = camera.world_to_screen(sprite.rect.center, screen.get_size())
        rect = sprite.image.get_rect(center=(round(x), round(y)))
        screen.blit(sprite.image, rect)
```

- Decide once whether `pos` is the view center or top-left; the math above assumes center.
- Round only at draw time; keep the camera float for smooth follow.
- Zooming sprites: `pygame.transform.smoothscale` per frame is expensive; pre-scale or use
  `pygame.transform.scale_by` sparingly.

### 2. Smooth follow with dead zone

```python
import math

DEAD_ZONE = 48
FOLLOW = 6.0

def follow(camera, target_pos, dt):
    delta = Vector2(target_pos) - camera.pos
    if delta.length() <= DEAD_ZONE:
        return
    desired = Vector2(target_pos) - delta.normalize() * DEAD_ZONE
    t = 1 - math.exp(-FOLLOW * dt)
    camera.pos += (desired - camera.pos) * t
```

- `1 - exp(-k*dt)` is frame-rate independent; clamp `dt` to avoid huge steps after a stall.
- Dead zone prevents jitter when the player idles.
- For pixel-art, round the camera at draw time, not in `follow`.

### 3. Clamp to level

```python
def clamp(camera, level_size, screen_size):
    w, h = screen_size
    view_w, view_h = w / camera.zoom, h / camera.zoom
    level_w, level_h = level_size

    if view_w < level_w:
        camera.pos.x = min(max(camera.pos.x, view_w / 2), level_w - view_w / 2)
    else:
        camera.pos.x = level_w / 2

    if view_h < level_h:
        camera.pos.y = min(max(camera.pos.y, view_h / 2), level_h - view_h / 2)
    else:
        camera.pos.y = level_h / 2
```

- Clamp after follow and after zoom changes.
- If the level is smaller than the view, center it.
- Use level bounds in world pixels, not tile indices.

### 4. Parallax

```python
def draw_parallax(screen, layer, camera, factor, screen_size):
    w, h = screen_size
    ox = (camera.pos.x - w / 2) * factor
    oy = (camera.pos.y - h / 2) * factor
    screen.blit(layer, (-ox % layer.get_width() - layer.get_width(), -oy % layer.get_height()))
```

- Factor 0 = screen-fixed, 1 = world-locked; use 0.2–0.6 for backgrounds.
- Tile the layer with modulo so it never runs out.
- Parallax layers are drawn before the world, without the camera offset.

### 5. Shake

```python
import random

class Shake:
    def __init__(self):
        self.time = 0.0
        self.strength = 0.0

    def add(self, strength, duration):
        self.strength = max(self.strength, strength)
        self.time = max(self.time, duration)

    def offset(self, dt):
        if self.time <= 0:
            return (0, 0)
        self.time -= dt
        falloff = max(self.time / 0.25, 0)
        return (
            random.uniform(-1, 1) * self.strength * falloff,
            random.uniform(-1, 1) * self.strength * falloff,
        )
```

Apply the offset when computing screen positions; never add it to `camera.pos`.

### 6. Culling and drawing order

```python
def visible(rect, camera, screen_size, margin=64):
    w, h = screen_size
    view = pygame.Rect(
        camera.pos.x - w / (2 * camera.zoom) - margin,
        camera.pos.y - h / (2 * camera.zoom) - margin,
        w / camera.zoom + margin * 2,
        h / camera.zoom + margin * 2,
    )
    return rect.colliderect(view)
```

- Cull before blitting; large worlds otherwise cost fill rate.
- Draw background → world → foreground → HUD.
- `pygame.sprite.LayeredUpdates` can order sprites but not cull; combine both.

## Pitfalls

- **Mouse aim offset** → screen position used as world position. Convert with
  `screen_to_world`.
- **HUD scrolls** → drawn through the camera transform. Draw it last in screen space.
- **Camera jitters** → raw lerp factor, or rounding before smoothing.
- **Shows outside the level** → no clamp, or clamp with unzoomed view size.
- **Sprites pop at edges** → culling margin too small for large sprites.
- **Shake drifts** → added to `camera.pos`. Apply as a draw offset.
- **Zoom blurs** → scaling every sprite per frame; pre-scale assets or use integer zoom.
- **Low FPS makes follow slow/fast** → frame-dependent lerp; use `1 - exp(-k*dt)` and clamp `dt`.
- **Camera state and level bounds disagree** → separate sources; keep one level-size constant.

## References

- Read `references/offset-follow-and-picking.md` for the coordinate math, clamping formulas,
  culling, parallax and a camera test checklist.

## Related skills

- `pygame-core` — the loop, sprites and input.
- `pygame-tilemap` — tile drawing and level bounds.
- `pygame-save` — persisting settings.
- `camera-systems` — engine-neutral follow/shake design.
- `love2d-camera` — the same manual camera in Lua.
