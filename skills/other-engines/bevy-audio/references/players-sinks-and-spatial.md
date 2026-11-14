# Players, sinks and spatial audio (Bevy 0.20)

Depth for `bevy-audio`: the component model, sink API, spatial setup and volume math.

## Audio components

| Item | Role |
|------|------|
| `AudioSource` | Asset holding decoded audio data. |
| `AudioPlayer` | Component that starts playback of a handle. |
| `PlaybackSettings` | Initial mode, volume, speed, paused, muted, spatial, start/duration. |
| `PlaybackMode` | `Once`, `Loop`, `Despawn`. |
| `Volume` | `Linear(f32)` or `Decibels(f32)`. |
| `AudioSink` | Added by Bevy to a playing non-spatial sound. |
| `SpatialAudioSink` | Added for spatial sounds. |
| `AudioListener` | Marks the listener (camera). |
| `GlobalVolume` | Resource scaling all audio. |
| `AudioSinkPlayback` | Trait with volume/speed/play/pause/position/mute. |

`PlaybackSettings` is read when playback starts; later changes do not affect the running sound.

## Playback settings

```rust
PlaybackSettings {
    mode: PlaybackMode::Once,
    volume: Volume::Linear(0.8),
    speed: 1.0,
    paused: false,
    muted: false,
    spatial: false,
    spatial_scale: None,
    start_position: None,
    duration: None,
}
```

Convenience constants: `PlaybackSettings::ONCE`, `::LOOP`, `::DESPAWN`; builder methods like
`.with_volume(...)`, `.with_spatial(true)`.

## Sink API (`AudioSinkPlayback`)

| Method | Effect |
|--------|--------|
| `volume() -> Volume` | Current managed volume. |
| `set_volume(Volume)` | Change volume (works while muted, applies on unmute). |
| `speed() / set_speed(f32)` | Playback rate (1.0 normal). |
| `play()` / `pause()` / `toggle_playback()` | Transport control. |
| `is_paused()` | Whether paused. |
| `position() -> Duration` | Playhead. |
| `mute()` / `unmute()` / `is_muted()` | Mute without losing volume. |

- The sink is inserted asynchronously; systems must tolerate its absence.
- Despawning the entity stops the sound.
- `SpatialAudioSink` exposes the same playback control plus spatial behavior.

## Spatial audio

Checklist:

1. Add `AudioListener` to the camera entity.
2. Spawn the emitter with a `Transform` and `PlaybackSettings::LOOP.with_spatial(true)`.
3. Keep `spatial_scale` consistent across sounds (units per meter).
4. Update `Transform` as the emitter moves; no manual sink positioning needed.
5. Test with the listener moving around the emitter, not only at the origin.

Without a listener, spatial sounds cannot be placed correctly; with `spatial: false` the sound is
non-positional regardless of `Transform`.

## Volume math

```text
effective = GlobalVolume × master × group × per_sound
```

- Keep each factor in `[0, 1]` unless intentionally boosting.
- Use `Volume::Linear` for sliders; convert decibels only for display.
- Apply changed group volumes to live sinks; per-sound volume is set at spawn.
- Mute via the sink, not by setting 0, so unmute restores the level.

## Lifecycle

- One-shots: `PlaybackSettings::DESPAWN` removes the entity when playback ends.
- Loops: keep one entity per track; despawn on switch.
- Pause menu: pause the sink (or the whole audio via `GlobalVolume`), do not despawn.
- State changes: put music on a persistent entity outside the gameplay state, or respawn
  deliberately.

## Headless and CI

- CI machines may have no audio device; audio may fail or be silent.
- Gate audio spawns behind a resource/feature for tests, or run tests that do not require sound.
- Do not assert on audio timing in unit tests.

## Test checklist

1. SFX plays and its entity disappears afterwards.
2. Music loops and continues across gameplay state changes.
3. Pause/resume works and resumes at the same position.
4. Volume slider changes live music immediately; SFX use the new value on next play.
5. Mute/unmute restores the previous volume.
6. Spatial sound pans as the listener moves; silent without a listener.
7. Track switch leaves exactly one music entity.
8. Settings persist across restart (`bevy-save`).
9. Missing asset logs an error and does not crash.
10. CI/headless run does not hang on audio.
