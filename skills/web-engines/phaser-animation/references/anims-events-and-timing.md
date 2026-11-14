# Anims, events and timing (Phaser 4.2)

Depth for `phaser-animation`: config fields, event flow, chaining and timing controls.

## Animation config

| Field | Meaning |
|-------|---------|
| `key` | Unique animation name. |
| `frames` | Array of frames or `generateFrameNumbers`/`generateFrameNames` result. |
| `frameRate` | Frames per second (default 24 when `duration` is null). |
| `duration` | Total ms; overrides frameRate. |
| `repeat` | `0` once, `-1` forever, `n` extra repeats. |
| `repeatDelay` | ms between repeats. |
| `delay` | ms before first play. |
| `yoyo` | Play forward then backward. |
| `timeScale` | Playback speed multiplier. |
| `skipMissedFrames` | Drop frames on lag (default true). |
| `showBeforeDelay` / `showOnStart` / `hideOnComplete` | Visibility around playback. |

## Frame generation

```js
// Spritesheet, numeric frames
this.anims.generateFrameNumbers("dude", { start: 0, end: 7 });
this.anims.generateFrameNumbers("dude", { frames: [0, 1, 2, 1] });

// Atlas, named frames
this.anims.generateFrameNames("hero", { prefix: "run_", start: 0, end: 7, zeroPad: 2 });
```

- `generateFrameNames` supports `prefix`, `suffix`, `start`, `end`, `zeroPad`.
- A frame entry can carry a custom `duration` for holds.

## Event flow

```text
animationstart
  animationupdate (per frame)
  animationrepeat (each loop)
animationcomplete        (only if the animation actually completes)
animationstop            (stop() or interruption)
```

Keyed variants: `animationcomplete-attack`, `animationstart-attack`, etc.

- Forever-looping animations never emit `complete`.
- `animationupdate` receives `(anim, frame)`; `frame.index` is the frame in the animation.
- Remove listeners on scene shutdown or use `once`.

## Playing and chaining

| Method | Effect |
|--------|--------|
| `sprite.play(key, ignoreIfPlaying)` | Start; `true` avoids restarting. |
| `sprite.anims.play(key, ignoreIfPlaying)` | Same via state. |
| `sprite.anims.chain(keyOrArray)` | Queue after completion; no args clears. |
| `sprite.anims.stop()` | Stop. |
| `sprite.anims.pause()/resume()` | Pause/resume. |
| `sprite.anims.restart()` | Restart current. |
| `this.anims.play(key, children)` | Play across sprites. |
| `this.anims.staggerPlay(key, children, ms)` | Offset starts. |
| `this.anims.addMix(a, b, ms)` | Blend/queue when switching. |

- Local animations (`sprite.anims.create`) take priority over global ones with the same key.
- Chained animations are per game object.

## Timing

- `sprite.anims.timeScale` — multiplier.
- `sprite.anims.msPerFrame` — fixed frame duration.
- `sprite.anims.currentFrame.index` — current frame (1-based in Phaser's frame list).
- Global manager `timeScale` affects all animations; prefer per-sprite for variation.
- For frame-accurate logic, drive from `animationupdate`, not timers.

## Test checklist

1. Idle/run/attack switch without restarting or flicker.
2. One-shot fires `animationcomplete` and returns to locomotion.
3. Hit frame fires exactly once per attack.
4. Looping animation does not fire complete.
5. Chain and combo inputs work with buffered windows.
6. `timeScale` matches movement speed; no foot sliding.
7. Atlas and spritesheet animations both resolve frames.
8. Scene restart recreates animations.
9. Pixel-art renders sharp (`pixelArt: true`).
10. No per-frame `create` or listener leaks.
