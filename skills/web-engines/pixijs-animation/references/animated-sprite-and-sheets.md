# AnimatedSprite and sheets (PixiJS v8.22)

Depth for `pixijs-animation`: the AnimatedSprite API, spritesheet format, timing math and pooling.

## AnimatedSprite API

| Member | Notes |
|--------|-------|
| `new AnimatedSprite(textures, autoUpdate?)` | Texture array; autoUpdate defaults true. |
| `new AnimatedSprite(options)` | `{ textures, animationSpeed, loop, autoPlay, updateAnchor, onComplete, onFrameChange, onLoop }`. |
| `play()` | Start/resume from current frame. |
| `stop()` | Stop on the current frame. |
| `gotoAndPlay(frame)` | Jump and play. |
| `gotoAndStop(frame)` | Jump and stop. |
| `animationSpeed` | Frames per ticker tick (1 ≈ 60 fps). |
| `loop` | Repeat after the last frame. |
| `playing` | Whether it is advancing. |
| `currentFrame` / `totalFrames` | Frame index/count. |
| `onComplete` | Non-looping completion. |
| `onFrameChange` | Per-frame callback. |
| `onLoop` | Each loop. |
| `update(deltaTime)` | Manual advance when `autoUpdate` is false. |

## Spritesheet format

```json
{
  "frames": {
    "walk_0": { "frame": { "x": 0, "y": 0, "w": 32, "h": 48 } },
    "walk_1": { "frame": { "x": 32, "y": 0, "w": 32, "h": 48 } }
  },
  "animations": {
    "walk": ["walk_0", "walk_1"]
  },
  "meta": { "image": "hero.png", "size": { "w": 64, "h": 48 }, "scale": "1" }
}
```

- `Assets.load("hero.json")` resolves the sheet and registers `sheet.animations`.
- Animation entries are frame-name arrays; order defines playback.
- Frame rectangles must not overlap incorrectly; use a packer (TexturePacker/Aseprite export).

## Timing math

```text
animationSpeed = targetFPS / 60
```

- Ticker runs at display refresh; Pixi normalizes delta, so `1/6` ≈ 10 fps on a 60 Hz display.
- For exact timing, drive `update(dtSeconds * 60)` manually or use `Ticker.shared.deltaMS`.
- `animationSpeed` 0 pauses; negative values are not supported for reverse playback.

## Auto vs manual

- `autoUpdate: true` (default): `Ticker.shared` advances the sprite.
- `autoUpdate: false`: call `sprite.update(deltaTime)` yourself, e.g. only when unpaused.
- Never both, or the animation runs at double speed.

## Events

```js
sprite.onComplete = () => { /* non-looping only */ };
sprite.onFrameChange = (frame) => { /* hit windows, footsteps */ };
sprite.onLoop = () => { /* each loop */ };
```

- `onComplete` will not fire while `loop` is true.
- Callbacks fire from the update; keep them light.
- Clear callbacks before destroying if they close over other objects.

## Pooling recipe

```text
pool: AnimatedSprite[]
spawn: pop() or new; set textures/position/loop; gotoAndPlay(0); add to stage
recycle: remove from stage (or visible=false); push back
```

- Animation textures are shared; the per-sprite cost is the display object.
- Trim the pool if memory matters; `destroy()` frees GPU-side sprite resources, not the sheet.

## Test checklist

1. Animation speed matches the intended FPS.
2. Looping animations loop; one-shots fire `onComplete`.
3. Frame callbacks fire once per frame, not per tick.
4. Pause menu freezes animation (manual update or ticker stop).
5. Flipping keeps the anchor and feet aligned.
6. Pixel-art uses nearest scaling and stays sharp.
7. Pooled effects reset to frame 0 and hide when done.
8. No double updates from auto + manual.
9. Spritesheet stays loaded while sprites exist.
10. Destroyed sprites do not receive callbacks.
