---
name: phaser-audio
description: >
  Audio in Phaser 4.2: this.sound (SoundManager), adding and playing sounds, fire-and-forget
  sound.play, looping music, volume/rate/detune/pan, markers and audio sprites, spatial audio
  listeners, Web Audio unlock and tab-blur behavior. Use when a Phaser game needs SFX, music or
  volume settings. Targets Phaser 4.2.
---

# Phaser audio

Phaser routes audio through one `SoundManager` per game (`this.sound` in every scene), backed by
Web Audio or HTML5 Audio. Sounds are cached by key; you either play them fire-and-forget or keep an
instance for control. Targets **Phaser 4.2**.

## When to use

- Use when a Phaser game needs SFX, music, UI sounds, markers or volume settings.
- Use when sounds are silent on mobile, music overlaps, or volume sliders do nothing.

**When *not* to use:** animation events → `phaser-animation`; loading assets → `phaser-core`;
mixing design → `audio-design`; UI for sliders → `phaser-ui`.

## Core workflow

1. **Load** audio before `create` (`this.load.audio(key, [urls])`) or an audio sprite.
2. **Fire-and-forget** with `this.sound.play(key, config)` for one-shots.
3. **Keep an instance** (`this.sound.add(key, config)`) for music/looping and live control.
4. **Unlock** audio on the first user gesture (Phaser does this automatically, but check
   `this.sound.locked` and offer a tap-to-start).
5. **Control** volume/mute globally and per sound; pause music on scene change if needed.
6. **Markers** for sections of a track or an audio sprite for many short SFX.
7. **Test** on iOS Safari and after tab switches.

## Patterns

### 1. Fire-and-forget SFX

```js
create() {
  this.sound.play("hit", { volume: 0.7, rate: 1.1 });
}
```

- `this.sound.play` adds, plays and destroys the instance on completion.
- Config: `volume`, `loop`, `rate`, `detune`, `pan`, `delay`, `seek`.
- For rapid repeats, this creates a new source each time (Web Audio handles it); cap the rate to
  avoid distortion.

### 2. Music with an instance

```js
create() {
  this.music = this.sound.add("theme", { volume: 0.5, loop: true });
  this.music.play();
}

setMusicVolume(v) {
  this.music.setVolume(v);        // 0..1
}

stopMusic() {
  this.music.stop();              // resets to start
  this.music.destroy();           // remove from manager when done
}
```

- `add` keeps the instance; `play()` starts from the beginning.
- `pause()`/`resume()` keep position; `stop()` resets it.
- A destroyed sound cannot be replayed; keep it if you need to restart.
- Music should live in a persistent scene or survive scene changes (Phaser's manager is global,
  but the instance reference is yours).

### 3. Global volume and mute

```js
this.sound.volume = 0.8;   // master
this.sound.mute = true;    // mute all
this.sound.setVolume(0.8); // chainable
```

- Per-sound and global volumes multiply; rate/detune likewise.
- Persist settings in `localStorage` and apply on boot.
- Respect `pauseOnBlur` (default true) so music pauses when the tab loses focus.

### 4. Markers and audio sprites

```js
// Markers on a single track
const music = this.sound.add("music");
music.addMarker({ name: "intro", start: 0, duration: 8000 });
music.addMarker({ name: "loop", start: 8000, duration: 30000, config: { loop: true } });
music.play("loop");

// Audio sprite: one file, many short sounds
this.load.audioSprite("sfx", "sfx.ogg", "sfx.json");
const sprite = this.sound.addAudioSprite("sfx");
sprite.play("explosion");
```

- Markers are named sections with start/duration and optional config.
- Audio sprites reduce requests and decode cost for many short SFX.
- `this.sound.play("key", { marker: ... })`? Use an instance when playing markers repeatedly.

### 5. Spatial audio

```js
this.sound.setListenerPosition(x, y);   // Web Audio only
sound.play({ pan: -0.5 });               // -1 left .. 1 right
```

- `setListenerPosition` positions the 2D listener; sounds can set `pan`.
- Full 3D spatial audio needs Web Audio and the relevant config; HTML5 fallback ignores it.
- Update the listener when the camera moves.

### 6. Unlock and lifecycle

```js
if (this.sound.locked) {
  this.sound.once("unlocked", () => this.startMusic());
} else {
  this.startMusic();
}
```

- Browsers block autoplay until a gesture; Phaser unlocks on first input.
- `this.sound.on("decoded", key)` / `"decodedall"` help loading screens.
- Remove sounds you no longer need with `destroy()` to keep the manager small.
- Stop sounds on scene shutdown if they should not continue.

## Pitfalls

- **Silent on mobile** → audio not unlocked; start after a tap and check `this.sound.locked`.
- **Music restarts on scene change** → sound re-added/played in the new scene. Keep one instance
  or check `isPlaying`.
- **Overlapping music** → several instances playing; stop the previous one.
- **Volume slider does nothing** → setting `this.sound.volume` while a per-sound volume is 0, or
  using `mute` unintentionally; check both.
- **Sound not found** → key not loaded before `create`, or the file failed (codec support).
- **Clicks/pops** → cutting a sound abruptly; use a short fade via tweens on volume.
- **Too many SFX** → fire-and-forget every frame. Rate-limit or pool instances.
- **Audio sprite drift** → marker durations must match the JSON spritemap.
- **HTML5 fallback differences** → no pan/spatial and higher latency; test the fallback.

## References

- Read `references/sound-manager-and-sprites.md` for the SoundManager/Sound API table, marker and
  sprite formats, unlock flow and an audio test checklist.

## Related skills

- `phaser-core` — loading and scenes.
- `phaser-animation` — syncing sounds to frames.
- `phaser-ui` — volume sliders and mute buttons.
- `audio-design` — mixing, ducking and adaptive music.
- `pixijs-ui` / `threejs-ui` — UI for web audio settings.
