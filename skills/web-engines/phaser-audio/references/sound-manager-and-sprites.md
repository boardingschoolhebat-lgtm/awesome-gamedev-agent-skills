# Sound manager and sprites (Phaser 4.2)

Depth for `phaser-audio`: the SoundManager API, instance methods, markers/audio sprites, unlock
flow and test checks.

## SoundManager (`this.sound`)

| Member | Notes |
|--------|-------|
| `add(key, config)` | Create a retained sound instance. |
| `play(key, config)` | Fire-and-forget; destroys on completion. |
| `addAudioSprite(key, config)` | Instance backed by an audio sprite. |
| `volume` / `setVolume(v)` | Master volume 0–1. |
| `mute` / `setMute(bool)` | Master mute. |
| `rate` / `detune` | Global multipliers. |
| `locked` | True until unlocked by a gesture. |
| `unlock()` | Manual unlock. |
| `pauseOnBlur` | Pause when tab loses focus (default true). |
| `setListenerPosition(x, y)` | Spatial listener (Web Audio). |
| `on("decoded", key)` / `on("decodedall")` | Decode progress. |
| `stopAll()` | Stop every sound. |

## Sound instance

| Member | Notes |
|--------|-------|
| `play(markerName?, config?)` | Start (from beginning). |
| `pause()` / `resume()` | Keep position. |
| `stop()` | Reset to start. |
| `destroy()` | Remove from manager. |
| `isPlaying` / `isPaused` | State. |
| `volume`/`setVolume`, `rate`/`setRate`, `detune`/`setDetune`, `pan`/`setPan` | Per-sound. |
| `loop` | Loop flag. |
| `seek` | Position in seconds. |
| `duration` | Length. |
| `addMarker({name, start, duration, config})` | Named section. |

Config keys: `volume`, `loop`, `rate`, `detune`, `pan`, `delay`, `seek`, `mute`.

## Markers

```js
const music = this.sound.add("music");
music.addMarker({ name: "intro", start: 0, duration: 8000 });
music.addMarker({ name: "loop", start: 8000, duration: 30000, config: { loop: true } });
music.play("loop");
```

- `start`/`duration` in seconds.
- A marker's `config` can override volume/loop for that section.
- Marker names must be unique per sound.

## Audio sprites

```js
this.load.audioSprite("sfx", ["sfx.ogg", "sfx.mp3"], "sfx.json");
const sfx = this.sound.addAudioSprite("sfx");
sfx.play("explosion");
```

JSON format:

```json
{
  "resources": ["sfx.ogg", "sfx.mp3"],
  "spritemap": {
    "explosion": { "start": 0, "end": 0.8, "loop": false },
    "coin": { "start": 1.0, "end": 1.2, "loop": false }
  }
}
```

- One decode, many short sounds; good for mobile request limits.
- `start`/`end` in seconds; overlapping ranges are a bug.

## Unlock flow

```text
page loads -> SoundManager created (locked)
first pointer/key event -> unlock() -> "unlocked" event
sound.play() before unlock -> queued or ignored depending on manager
```

- Always provide a visible "tap to start" path if music must begin immediately.
- Check `this.sound.locked` in `create` and start audio on `unlocked`.

## Test checklist

1. First SFX plays after a click/tap on mobile.
2. Music loops and survives scene transitions.
3. Volume/mute affects all sounds; per-sound volume still respected.
4. Pause on tab blur, resume on focus.
5. Markers play the right section; looping marker loops.
6. Audio sprite keys match the JSON spritemap.
7. No duplicate music instances.
8. Rate/detune vary without pitch artifacts.
9. HTML5 fallback still plays (no pan/spatial).
10. Stopping/destroying frees sounds; no manager growth.
