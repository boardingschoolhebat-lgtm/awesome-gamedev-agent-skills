# Mixers, spatial audio and import settings (Unity 6.3)

Depth for `unity-audio`: how routing and snapshots behave, how 3D attenuation is computed, and
which import settings keep builds clean on each platform.

## API used by the skill

| API | Form | Notes |
|-----|------|-------|
| `AudioSource` | component | `clip`, `volume`, `pitch`, `loop`, `playOnAwake`, `spatialBlend`, `outputAudioMixerGroup`. |
| `AudioSource.PlayOneShot` | `(AudioClip clip, float volumeScale = 1)` | Overlaps on the same source. |
| `AudioListener` | component | One active listener; `pause` stops all audio. |
| `AudioMixer` | asset | Groups, snapshots, exposed parameters. |
| `AudioMixer.SetFloat` | `(string name, float dB)` → `bool` | False when the parameter is missing or snapshots are being edited. |
| `AudioMixer.GetFloat` | `(string name, out float dB)` → `bool` | Use to verify exposure. |
| `AudioMixer.ClearFloat` | `(string name)` | Returns the parameter to snapshot control. |
| `AudioMixer.FindSnapshot` | `(string name)` → `AudioMixerSnapshot` | Exact name match. |
| `AudioMixerSnapshot.TransitionTo` | `(float seconds)` | Interpolates all parameters in the snapshot. |
| `AudioMixer.TransitionToSnapshots` | `(snapshots, weights, seconds)` | Weighted blend of several snapshots. |
| `AudioSource.PlayClipAtPoint` | static | Creates a temporary object; avoid in hot paths. |
| `AudioSettings.outputSampleRate` | static property | Platform output rate, not the clip rate. |

## Group routing

```text
Master
├── Music        (exposed: MusicVolume)
├── SFX          (exposed: SfxVolume)
├── UI           (exposed: UiVolume)
└── Ambience     (exposed: AmbienceVolume)
```

- Every source should have an `outputAudioMixerGroup`; a null group bypasses the mixer.
- Expose group volume in the Audio Mixer inspector; the exposed name is what `SetFloat` takes.
- Effects on a group (low-pass, compressor, reverb) apply to all routed sources — cheaper and
  more consistent than per-source effects.
- Master headroom: leave a few dB below 0 so summed SFX do not clip. Use a compressor/limiter on
  Master if the mix is dense.

## dB conversion

```text
dB   = 20 * log10(linear)
linear = 10 ^ (dB / 20)
```

| Linear | dB |
|--------|----|
| 1.0 | 0 |
| 0.5 | -6 |
| 0.25 | -12 |
| 0.1 | -20 |
| 0.01 | -40 |
| 0.0001 | -80 (practical silence) |

Slider 0 must not map to `log10(0)`; clamp to `0.0001` and optionally map the bottom of the slider
to the mixer's mute instead of `-80 dB`.

## Snapshots

- A snapshot stores the values of the mixer's parameters (and effect states) at authoring time.
- `TransitionTo(seconds)` interpolates from the current state to the snapshot.
- Exposed parameters are script-owned after `SetFloat`; `ClearFloat` returns control to snapshots.
- Typical snapshots: `Gameplay`, `Paused` (low-pass Music/SFX, UI audible), `Underwater`
  (low-pass + reverb), `Cutscene` (duck SFX).
- Call transitions on state changes only; calling `TransitionTo` every frame restarts the
  interpolation and produces a stuck fade.

## Spatial audio

| Setting | Effect |
|---------|--------|
| `spatialBlend` | 0 = 2D, 1 = 3D; in-between blends. |
| `minDistance` | Inside this radius the source is at full volume. |
| `maxDistance` | Outer limit for the rolloff curve. |
| `rolloffMode` | Logarithmic (natural), Linear (predictable), Custom (curve). |
| `dopplerLevel` | Pitch shift from relative velocity; 0 disables. |
| `spread` | Stereo spread for 3D sources on the edge of the listener. |

- The listener is normally on the main camera; a first-person camera makes the player's ears the
  listener.
- Distances are in Unity world units; a 2D game with 1 unit = 1 pixel needs very different
  `minDistance` values from a 1 unit = 1 m 3D game.
- For 2D games, keep most sources at `spatialBlend = 0` and use volume/pan for distance; true 3D
  attenuation in pixel space is rarely useful.

## Import settings

| Clip type | Load type | Compression | Notes |
|-----------|-----------|-------------|-------|
| Short SFX (< 2 s) | Decompress On Load | PCM or ADPCM | Lowest latency; memory cost grows with count. |
| Medium SFX | Compressed In Memory | Vorbis/ADPCM | Balance of memory and CPU. |
| Music / ambience | Streaming | Vorbis | Low memory; not for latency-sensitive sounds. |
| UI clicks | Decompress On Load | PCM | Must fire immediately. |

- `Force To Mono` for 3D sources saves memory; stereo only matters for 2D music.
- `Preload Audio Data` on short SFX avoids a first-play hitch.
- Platform overrides (Android/iOS/WebGL) can change compression per platform; check them in the
  build.
- Very long clips with `Decompress On Load` are a common memory spike; switch them to streaming.

## Platform checklist

1. Editor: every source has a mixer group; no missing-listener warning.
2. Build on the target platform: music streams, SFX latency acceptable, no crackle at peak.
3. Pause menu: game audio ducks/stops, UI sounds still play.
4. Volume sliders: 0 is silent, 1 is full, midpoints feel even (dB conversion).
5. Spatial: walk around a 3D source; attenuation and direction match the world.
6. WebGL: audio starts after a user gesture and survives a tab switch.
7. Mobile: backgrounding the app pauses audio and resumes cleanly.
8. Scene reload: pooled sources and listeners do not duplicate.
