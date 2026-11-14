---
name: phaser-animation
description: >
  Sprite animation in Phaser 4.2: creating global and local animations, spritesheet and atlas
  frames, play/chain/stagger, repeat/yoyo/delays, animation events, timeScale and msPerFrame,
  and switching animation state without restarting or flickering. Use when a Phaser game needs
  sprite animation, attack frames, or animation-driven gameplay events. Targets Phaser 4.2.
---

# Phaser animations

Phaser animation is frame-based: the `AnimationManager` owns named animations, each sprite's
`AnimationState` plays one, and events fire on start/update/complete. Targets **Phaser 4.2**.

## When to use

- Use when a Phaser sprite needs idle/walk/attack frames, atlas animations or chained states.
- Use when animations restart every frame, never fire `animationcomplete`, or ignore hit frames.

**When *not* to use:** tweened movement/scale/alpha → Phaser tweens; loading assets →
`phaser-core`; audio cues → `phaser-audio`; UI → `phaser-ui`; design → `game-feel`.

## Core workflow

1. **Load frames**: `this.load.spritesheet(key, url, { frameWidth, frameHeight })` or
   `this.load.atlas(key, png, json)`.
2. **Create animations once** (scene `create` or a boot scene):
   `this.anims.create({ key, frames, frameRate, repeat })`.
3. **Play** with `sprite.play(key)`; pass `true` as the second argument to ignore if already
   playing.
4. **Chain** one-shots with `sprite.anims.chain(next)` or listen for `animationcomplete`.
5. **React** to frames with `animationupdate` (or per-frame delays) for hit windows.
6. **Tune** `timeScale`, `msPerFrame`, `repeatDelay`, `yoyo` instead of duplicating animations.
7. **Destroy** local animations/scene-specific state when the scene shuts down.

## Patterns

### 1. Global animations from a spritesheet

```js
create() {
  this.anims.create({
    key: "run",
    frames: this.anims.generateFrameNumbers("dude", { start: 0, end: 7 }),
    frameRate: 12,
    repeat: -1,
  });

  this.anims.create({
    key: "attack",
    frames: this.anims.generateFrameNumbers("dude", { frames: [8, 9, 10, 9] }),
    frameRate: 14,
    repeat: 0,
  });

  this.player = this.add.sprite(100, 100, "dude");
  this.player.play("run");
}
```

- Create animations once; calling `create` again with the same key warns/overwrites depending on
  config.
- `repeat: -1` loops forever; `0` plays once.
- `generateFrameNumbers` for spritesheets; `generateFrameNames` for atlas frame names.
- Global animations are shared by all sprites; local ones (`sprite.anims.create`) are per sprite.

### 2. Play, chain and one-shots

```js
attack() {
  if (this.player.anims.isPlaying && this.player.anims.getName() === "attack") return;
  this.player.play("attack", true);
  this.player.anims.chain("run");
}
```

- `play(key, ignoreIfPlaying)` prevents restarting a looping animation every frame.
- `chain` queues the next animation after the current one completes; a forever-loop never
  completes unless stopped.
- For combos, chain `attack2` and `attack3` on input windows instead of one long clip.
- `this.anims.play(key, children)` plays the same animation on several sprites;
  `staggerPlay` offsets them.

### 3. Events and hit frames

```js
this.player.on("animationcomplete-attack", () => {
  this.player.play("run");
});

this.player.on("animationupdate", (anim, frame) => {
  if (anim.key === "attack" && frame.index === 2 && !this.didHit) {
    this.didHit = true;
    this.dealDamage();
  }
});
```

- `animationcomplete-<key>` filters by animation; plain `animationcomplete` fires for any.
- `animationupdate` gives the current frame; use it for hit windows, footsteps and VFX.
- Reset per-attack flags (`didHit`) when the attack starts, or the second attack does nothing.
- Looping animations never fire `animationcomplete`; listen for `animationstop`/`animationrepeat`.

### 4. Repeat, yoyo and delays

```js
this.anims.create({
  key: "pulse",
  frames: this.anims.generateFrameNumbers("orb", { start: 0, end: 3 }),
  frameRate: 8,
  repeat: -1,
  yoyo: true,
  repeatDelay: 200,
});
```

- `yoyo: true` plays forward then backward without extra frames.
- `repeatDelay` in ms between loops.
- `delay` before the first play; `showBeforeDelay`/`showOnStart`/`hideOnComplete` control
  visibility around it.
- `skipMissedFrames` (default true) drops frames on lag; set false for frame-accurate replays.

### 5. Speed and per-instance variation

```js
this.player.anims.timeScale = 1.2;      // 20% faster
this.player.anims.msPerFrame = 80;      // fixed ms per frame
this.player.setFrame(0);                // static pose
```

- `timeScale` scales the whole animation; `msPerFrame` overrides frame timing.
- To sync run speed with movement, set `timeScale` from velocity instead of making many clips.
- Local animations let one sprite use a different clip with the same key.

## Pitfalls

- **Animation restarts every frame** → `play(key)` without `ignoreIfPlaying` in `update`.
- **`animationcomplete` never fires** → the animation repeats forever. Use a one-shot or stop it.
- **Wrong frames** → spritesheet frame size mismatch or atlas frame names; log `sprite.texture.key`.
- **Hit window triggers twice** → no per-attack flag, or both `animationupdate` and a timer.
- **Flicker on state change** → playing a new animation without a transition frame or crossfade;
  align first frames or use `chain`.
- **Animations missing after scene restart** → created in a scene that shut down; create them in a
  boot scene or on `create`.
- **Sprites share animation state unexpectedly** → using global animations and mutating
  `timeScale`/`msPerFrame` on the manager instead of the sprite's `anims`.
- **Pixel-art blur** → `pixelArt: true` in game config and integer scaling.
- **Memory growth** → creating animations per spawn. Create once.

## References

- Read `references/anims-events-and-timing.md` for the animation config table, event flow,
  chain/repeat rules, timing properties and an animation test checklist.

## Related skills

- `phaser-core` — scenes, loading and sprites.
- `phaser-audio` — syncing sounds to animation events.
- `game-feel` — anticipation, hit frames and timing.
- `pixijs-animation` — frame animation in PixiJS.
- `unity-animation` / `unreal-animation` — engine equivalents.
