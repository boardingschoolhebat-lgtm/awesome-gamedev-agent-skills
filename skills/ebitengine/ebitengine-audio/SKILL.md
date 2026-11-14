---
name: ebitengine-audio
description: >
  Audio in Ebitengine (Go): the audio context and sample rate, decoding Ogg/Vorbis, WAV and MP3
  with the F32 decoders, one-shot SFX with NewPlayerFromBytes, looping music with
  NewInfiniteLoopF32, volume and pause, fades, and bus-like volume scaling for music/SFX/UI. Use
  when an Ebitengine game needs sound effects, music or audio settings. Targets Ebitengine v2.10.5.
---

# Ebitengine audio

Ebitengine's `audio` package plays PCM streams through an audio context. Music is a long looping
stream; SFX are short players created on demand. There is no mixer graph — volume groups are your
own multipliers. Targets **Ebitengine v2.10.5**.

## When to use

- Use when an Ebitengine game needs SFX, background music, UI sounds or volume settings.
- Use when audio is silent, distorted, out of sync, or crashes on a missing decoder.

**When *not* to use:** mixing/adaptive-music design → `audio-design`; the game loop →
`ebitengine-core`; UI for volume sliders → `ebitengine-ui`.

## Core workflow

1. **Get the context** with `audio.CurrentContext()` inside the running game (not before
   `RunGame`); the default sample rate is 44100.
2. **Decode assets once** at startup with `vorbis.DecodeF32`, `wav.DecodeF32` or `mp3.DecodeF32`.
3. **SFX**: decode to bytes once, create a player per play with `NewPlayerFromBytes`.
4. **Music**: wrap the decoded stream in `audio.NewInfiniteLoopF32` and create one `PlayerF32`.
5. **Volume**: keep `musicVolume`, `sfxVolume`, `masterVolume` floats and apply
   `master * group` to each player.
6. **Dispose**: stop players you no longer need; a looping player lives for the track's lifetime.

## Patterns

### 1. Context and decoding

```go
import (
    "bytes"
    "github.com/hajimehoshi/ebiten/v2/audio"
    "github.com/hajimehoshi/ebiten/v2/audio/vorbis"
    "github.com/hajimehoshi/ebiten/v2/audio/wav"
)

var audioCtx *audio.Context

func initAudio() {
    audioCtx = audio.CurrentContext()   // available once the game is running
    if audioCtx == nil {
        audioCtx = audio.NewContext(44100)
    }
}

func decodeVorbis(data []byte) (*vorbis.Stream, error) {
    return vorbis.DecodeF32(bytes.NewReader(data))
}

func decodeWav(data []byte) (*wav.Stream, error) {
    return wav.DecodeF32(bytes.NewReader(data))
}
```

- `audio.CurrentContext()` returns nil before the game starts; create/assign inside `Update` or a
  lazy init.
- The context has one sample rate; every stream must match it. Use `DecodeWithSampleRate` (16-bit)
  or resample when assets differ.
- `DecodeF32` produces 32-bit float stereo, which pairs with `NewPlayerF32` and
  `NewInfiniteLoopF32`; do not mix 16-bit and F32 APIs for the same stream.

### 2. One-shot SFX

```go
var hitPCM []byte   // decoded once at startup

func playHit() {
    p := audioCtx.NewPlayerFromBytes(hitPCM)
    p.SetVolume(0.8 * sfxVolume * masterVolume)
    p.Play()
}
```

- `NewPlayerFromBytes` is cheap and designed for short SFX; create one player per play.
- A player is garbage-collected only after it stops; do not keep references you do not need.
- Many simultaneous players can distort; cap the number of active SFX yourself.
- For pitch variation, pre-decode variants or resample offline; the API has no pitch control.

### 3. Looping music

```go
func startMusic(data []byte) error {
    stream, err := vorbis.DecodeF32(bytes.NewReader(data))
    if err != nil {
        return err
    }
    loop := audio.NewInfiniteLoopF32(stream, stream.Length())
    p, err := audioCtx.NewPlayerF32(loop)
    if err != nil {
        return err
    }
    p.SetVolume(0.5 * musicVolume * masterVolume)
    p.Play()
    musicPlayer = p
    return nil
}
```

- `stream.Length()` is the loop length in bytes of the decoded stream.
- Keep one music player; create a new one only when the track changes.
- `Pause()`/`Play()` for pause menus; `SetVolume` for fades.
- `NewInfiniteLoopWithIntroF32` (if present) handles an intro + loop; otherwise decode the intro
  separately and start the loop when it ends.

### 4. Fades and pauses

```go
type fade struct {
    player *audio.Player
    from, to, t, dur float64
}

func (f *fade) update(dt float64) {
    if f.dur <= 0 { return }
    f.t += dt
    k := math.Min(f.t/f.dur, 1)
    f.player.SetVolume(f.from + (f.to-f.from)*k)
}
```

- Fade by updating volume in `Update` with delta time, not by sleeping.
- Pause the music player when the game pauses (if desired) and resume on unpause.
- Duck music under dialogue by multiplying the music volume for the duration.

### 5. Volume groups

```go
var (
    masterVolume = 1.0
    musicVolume  = 0.7
    sfxVolume    = 0.9
)

func musicGain() float64 { return masterVolume * musicVolume }
func sfxGain() float64   { return masterVolume * sfxVolume }
```

- Apply the product when setting a player's volume.
- When a slider changes, update the currently playing music immediately; SFX pick it up next play.
- `SetVolume` accepts values above 1 in v2.10+, but keep the product ≤ 1 unless you intentionally
  amplify.
- Persist the three values with the settings file (`ebitengine-save`).

### 6. Missing or unsupported audio

- On a machine with no audio device, the context may be silent; do not crash.
- WASM requires the browser's audio unlock (a user gesture) before sound; start music on first
  input if the browser blocks autoplay.
- A decode error means a bad asset or wrong decoder; log the path and continue without sound
  rather than failing the game.

## Pitfalls

- **Silence** → `audio.CurrentContext()` used before the game runs and left nil, or the player was
  never `Play()`ed.
- **Distortion** → too many simultaneous players. Cap SFX and lower per-player volume.
- **Wrong pitch/speed** → stream sample rate differs from the context. Decode with the matching
  rate or create the context at the asset rate.
- **No loop** → `NewPlayerF32` on a finite stream. Wrap with `NewInfiniteLoopF32`.
- **Music restarts on scene change** → a new player created per scene. Reuse the existing one.
- **Fade freezes** → fade advanced by frame count instead of delta time.
- **Memory growth** → decoded streams or players retained per SFX. Decode once; let players go.
- **Crackle at loop point** → encoder padding or a non-seamless loop. Trim the asset.
- **Mixing 16-bit and F32 APIs** → pairing `DecodeF32` with `NewPlayer` or vice versa. Be
  consistent.
- **WASM autoplay blocked** → start audio from a click/keypress handler.

## References

- Read `references/context-decoding-and-players.md` for the API table, decoder/player pairing,
  loop and fade patterns, volume grouping and an audio test checklist.

## Related skills

- `ebitengine-core` — the loop and input that trigger sounds.
- `ebitengine-ui` — volume sliders and mute toggles.
- `ebitengine-save` — persisting volume settings.
- `audio-design` — mixing, ducking and adaptive music design.
- `unity-audio` / `unreal-audio` — engine mixer equivalents.
