---
name: rhythm-game
description: >
  Build a rhythm game: audio-clock timing, offset calibration, chart format (BPM, beats, lanes,
  holds), judgement windows, input latency compensation, combo/score, and engine bindings for
  Godot, Unity, Web Audio and Phaser. Use for a rhythm/music game or beat-synced gameplay.
---

# Rhythm game

A rhythm game is a timing system: notes are scheduled on the audio clock, the player presses on
the beat, and a judgement window converts timing error into a grade. Everything else (art, charts,
scoring) hangs off that clock. This is a **compositional** skill: it uses `audio-design` for
mixing, `localization` for menus, and an engine UI skill for the interface.

## When to use

- Use when notes must be hit in time with music, or when designing judgement windows and scoring.
- Use when audio and visuals drift, inputs feel late, or calibration is needed.

**When *not* to use:** a game with music but no timing judgement → `platformer`/`action` +
`audio-design`; pure music sequencing → your DAW; general input → `input-systems`.

## Core loop

**Music plays → notes approach the judgment line → the player presses a lane key → the game
compares press time to note time within a window → grade, combo, score → the chart ends and
results are shown.**

The audio clock is the source of truth. Never drive note timing from frame counts.

## Must-have systems

1. **Audio clock** — a monotonic time source tied to playback (not `delta` accumulation).
2. **Calibration** — a global audio/visual offset the player can tune.
3. **Chart data** — BPM (and changes), note times in beats/seconds, lanes, hold lengths.
4. **Spawner/approach** — notes appear `approach_time` before their hit time.
5. **Input handling** — lane presses timestamped at the audio clock, buffered.
6. **Judgement** — windows per grade; miss when the note passes the late window.
7. **Scoring/combo** — weights per grade, combo multiplier, accuracy.
8. **Results** — accuracy, max combo, grade, replay/retry.

## Timing model

```text
song_time = audio_clock_now - song_start_time - calibration_offset
note_y    = hit_line_y - (note.time - song_time) / approach_time * travel_distance
```

- `song_time` comes from the audio clock, in seconds.
- `approach_time` is how long a note is visible before its hit time.
- `calibration_offset` is positive when the player's audio is late relative to visuals.
- Judge `abs(press_time - note.time) <= window[grade]`.

### Calibration

Offer a calibration screen: metronome or a known beat, player taps N times, take the median
offset (robust to outliers), store per device. Audio output latency differs by platform, browser
and Bluetooth headset; one global offset is a compromise, per-device is better.

## Judgement windows

Typical starting points (tune to your game; tighter = harder):

| Grade | Window (ms) |
|-------|-------------|
| Perfect | ±25 |
| Great | ±50 |
| Good | ±90 |
| Bad | ±130 |
| Miss | beyond late window |

- Windows are symmetric unless you deliberately bias early/late.
- A press outside every window is ignored (not a miss) until a note is in range, or it consumes
  the nearest note — pick one rule and keep it consistent.
- Holds judge the head, then tick health; a released hold before the tail is a break.

## Patterns

### 1. Audio-clock song time (Web Audio)

```js
const ctx = new AudioContext();
const startAt = ctx.currentTime + 0.1;      // schedule ahead
source.start(startAt);

function songTime() {
  // currentTime is the audio hardware clock; baseLatency is the output buffer.
  return ctx.currentTime - startAt - calibration;
}
```

- `AudioContext.currentTime` advances in render blocks; it is still the right clock for audio.
- `baseLatency`/`outputLatency` describe output delay; fold them into calibration rather than
  guessing per frame.
- Do not use `performance.now()` for note judgement; it drifts from the audio device.

### 2. Godot audio clock

```gdscript
var _start_usec: int
var _latency: float

func _ready() -> void:
    _latency = AudioServer.get_time_to_next_mix() + AudioServer.get_output_latency()
    _start_usec = Time.get_ticks_usec()
    $Music.play()

func song_time() -> float:
    var t := (Time.get_ticks_usec() - _start_usec) / 1_000_000.0
    return maxf(0.0, t - _latency)
```

- `AudioServer.get_output_latency()` plus `get_time_to_next_mix()` estimates when sound reaches
  the speakers.
- `AudioStreamPlayer.get_playback_position()` alone is coarse; add
  `AudioServer.get_time_since_last_mix()` and subtract latency for sub-frame accuracy.
- Pause the clock with the music; do not keep counting while paused.

### 3. Unity audio clock

```csharp
double startDsp = AudioSettings.dspTime + 0.1;
music.PlayScheduled(startDsp);

double SongTime() => AudioSettings.dspTime - startDsp - calibration;
```

- `AudioSettings.dspTime` is sample-accurate and unaffected by frame rate.
- Schedule with `PlayScheduled` so the first beat lands exactly.
- Use `AudioSource.timeSamples` only as a cross-check; it is quantized.

### 4. Chart format

```json
{
  "bpm": 128,
  "offset": 0.042,
  "notes": [
    { "beat": 4.0, "lane": 0, "type": "tap" },
    { "beat": 4.5, "lane": 2, "type": "hold", "length": 2.0 }
  ]
}
```

- Store beats, convert to seconds with BPM changes: `time = offset + beat * 60 / bpm`.
- For BPM changes, precompute a cumulative time per beat section.
- Keep the chart independent of the engine; the game converts beats to song time.
- Validate charts (sorted times, lanes in range, no overlapping notes in one lane).

### 5. Input and judgement

```js
function onLanePress(lane) {
  const t = songTime();
  const note = nearestUnjudged(lane, t);
  if (!note) return;
  const error = t - note.time;
  const grade = gradeFor(Math.abs(error));
  if (!grade) return;
  judge(note, grade, error);
}
```

- Timestamp at the audio clock as close to the input event as possible.
- Buffer presses briefly (a few ms) so a note spawned this frame can be hit.
- Judge the nearest unjudged note in that lane within the widest window; do not scan the whole
  chart every press.
- A miss is generated when `song_time > note.time + miss_window` without a judgement.

### 6. Scoring and results

```text
accuracy = sum(note_weight * grade_value) / sum(note_weight)
score    = base_per_note * combo_multiplier(grade)
```

- Weight holds by length; a long hold should matter more than a tap.
- Combo multiplier: linear or stepped; cap it so one break does not zero the run.
- Show early/late bias in results ("you hit 12 ms early on average") — good feedback and helps
  calibration.

## Pitfalls

- **Notes drift** → timing accumulated from `delta`. Use the audio clock.
- **Inputs feel late** → no calibration, or calibration applied to visuals only. Apply one offset
  to the judgement, not to both.
- **First note always misses** → music starts before the clock/notes are ready. Schedule a lead-in
  and a count-in.
- **Frame-rate-dependent judgement** → comparing to `frame time` rather than the press timestamp.
- **Audio and visual disagree** → visual approach uses a different clock than audio. One clock.
- **Pause desyncs** → clock keeps running while music pauses. Pause both.
- **Bluetooth/headset players fail** → latency varies; per-device calibration and a wider "good"
  window at lower difficulties.
- **Holds impossible** → tail judged against head time or release events missed. Track hold state
  separately.
- **Chart off by a constant** → chart offset vs audio offset doubled. Keep one `offset` in the
  chart and one calibration in settings.
- **Overlapping notes in a lane** → chart validation missing; disallow or merge.

## Composition

- **Audio:** `audio-design` for mixing, latency, and music loops.
- **UI:** `godot-ui-control` / `unity-ui` / `phaser-ui` for lanes, judgement text, results.
- **Input:** `input-systems` for lane bindings, keyboard/gamepad/touch.
- **Save:** `save-systems` for scores, settings, calibration.
- **Localization:** `localization` for menus and song metadata.

## References

- Read `references/timing-charts-and-judgement.md` for clock formulas, calibration procedure,
  chart math, judgement state machine and a rhythm test checklist.
