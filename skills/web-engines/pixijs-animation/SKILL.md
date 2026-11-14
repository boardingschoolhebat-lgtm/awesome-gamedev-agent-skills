---
name: pixijs-animation
description: >
  Frame animation in PixiJS v8: AnimatedSprite from texture arrays or spritesheet animations,
  animationSpeed and loop, play/stop/gotoAndPlay, onComplete/onLoop/onFrameChange callbacks,
  autoUpdate vs manual ticker updates, anchor and flip handling, and pooling animated sprites.
  Use when a PixiJS game needs sprite animation. Targets PixiJS v8.22.
---

# PixiJS animation

PixiJS animates by swapping textures: `AnimatedSprite` holds a texture array and advances it on the
shared ticker. Spritesheets provide named animations and are the efficient path. Targets
**PixiJS v8.22**.

## When to use

- Use when a PixiJS sprite needs idle/walk/attack frames, spritesheet animations or frame events.
- Use when animations run too fast/slow, ignore `loop`, or fire callbacks late.

**When *not* to use:** tweens of position/scale/alpha → a tween library; loading assets →
`pixijs-rendering`; UI → `pixijs-ui`; audio → `phaser-audio` (Phaser-specific).

## Core workflow

1. **Load the spritesheet** with `Assets.load`; `sheet.animations` maps names to texture arrays.
2. **Create** `new AnimatedSprite(sheet.animations["walk"])` or the options object form.
3. **Configure** `animationSpeed`, `loop`, `anchor`, and callbacks.
4. **Play** with `.play()`; the shared ticker advances it by default.
5. **React** with `onComplete` (non-looping) or `onFrameChange` for hit/foot frames.
6. **Pool** animated sprites for bullets/effects instead of constructing per spawn.
7. **Stop and remove** sprites when done; textures are shared and cheap, sprites are not.

## Patterns

### 1. Spritesheet animation

```js
import { AnimatedSprite, Assets, Container } from "pixi.js";

const sheet = await Assets.load("assets/hero.json");
const hero = new AnimatedSprite(sheet.animations["walk"]);

hero.anchor.set(0.5, 1);
hero.animationSpeed = 1 / 8;   // 8 frames per second at 60 fps ticker
hero.loop = true;
hero.play();

app.stage.addChild(hero);
```

- `sheet.animations["walk"]` is an array of textures; the JSON defines frame names.
- `animationSpeed` is frames per ticker tick (≈ frames per 1/60 s), not frames per second; divide
  your target FPS by 60.
- `anchor` matters for flipping and ground alignment; set it once.
- The sprite shares the spritesheet's textures; do not clone them per instance.

### 2. Options object and callbacks

```js
const explosion = new AnimatedSprite({
  textures: sheet.animations["explode"],
  animationSpeed: 0.4,
  loop: false,
  autoPlay: true,
  onComplete: () => explosion.destroy(),
  onFrameChange: (frame) => {
    if (frame === 3) playSmoke();
  },
  onLoop: () => console.log("looped"),
});
```

- `autoPlay` starts immediately; otherwise call `play()`.
- `onComplete` fires only when `loop = false` and the last frame finishes.
- `onFrameChange` receives the current frame index; use it for hit windows.
- `updateAnchor: true` keeps the anchor stable when frame sizes differ.

### 3. Manual playback control

```js
hero.stop();                 // stop on current frame
hero.gotoAndStop(0);         // jump to frame 0 and stop
hero.gotoAndPlay(0);         // restart from frame 0
hero.animationSpeed = 0.5;   // slow down live
hero.loop = false;
```

- `play()` resumes from the current frame; `gotoAndPlay(0)` restarts.
- Changing `animationSpeed` takes effect immediately.
- `playing` tells you whether the ticker is advancing it.

### 4. Auto vs manual update

```js
// Default: autoUpdate = true, advances on Ticker.shared
const sprite = new AnimatedSprite(textures);

// Manual: advance with your own dt (pause menus, replays, fixed step)
const manual = new AnimatedSprite({ textures, autoUpdate: false });
manual.play();
app.ticker.add((ticker) => manual.update(ticker.deltaTime));
```

- Manual updates let you freeze animation while gameplay is paused.
- `update(deltaTime)` expects ticker delta units, not seconds.
- Do not advance twice (auto + manual).

### 5. Flipping and facing

```js
hero.scale.x = Math.abs(hero.scale.x) * (facingLeft ? -1 : 1);
```

- Flip with a negative `scale.x` around the anchor; keep the anchor centered or at the feet.
- Do not create separate flipped textures unless performance demands it.

### 6. Pooling

```js
const pool = [];

function spawnEffect(x, y) {
  const fx = pool.pop() ?? new AnimatedSprite(sheet.animations["hit"]);
  fx.position.set(x, y);
  fx.loop = false;
  fx.gotoAndPlay(0);
  fx.visible = true;
  app.stage.addChild(fx);
}
```

- Reuse sprites and toggle `visible`; remove from the stage or park them off-screen when done.
- Destroy only when the pool is trimmed.
- Textures stay in the sheet cache; destroying sprites does not free them.

## Pitfalls

- **Animation too fast/slow** → `animationSpeed` is per tick, not per second. Use targetFPS / 60.
- **No `onComplete`** → `loop` is true; set `loop = false`.
- **First frame flashes** → the sprite starts on frame 0 before `play()`; set `gotoAndStop` or
  `visible = false` until playing.
- **Anchor drifts between frames** → frames have different sizes; use `updateAnchor: true` or
  uniform frame sizes.
- **Double-speed animation** → autoUpdate plus a manual `update` call.
- **Memory growth** → new AnimatedSprite per particle. Pool and reuse.
- **Blurry pixels** → texture scale mode nearest for pixel-art (`texture.source.scaleMode =
  "nearest"`).
- **Destroyed texture** → destroying the spritesheet while sprites still use it. Keep assets
  loaded for the scene's lifetime.
- **Callbacks after destroy** → `onComplete` destroying the sprite while other code still
  references it; null-check.

## References

- Read `references/animated-sprite-and-sheets.md` for the AnimatedSprite API table, spritesheet
  JSON shape, ticker timing math, pooling and a test checklist.

## Related skills

- `pixijs-rendering` — Application, assets and display objects.
- `pixijs-ui` — menus/HUD around the game.
- `phaser-animation` — frame animation in Phaser.
- `game-feel` — timing and hit feedback.
