# Context, decoding and players (Ebitengine v2.10.5)

Depth for `ebitengine-audio`: the audio context, decoder/player pairing, loop and fade math, and
volume grouping.

## API used by the skill

| API | Package | Notes |
|-----|---------|-------|
| `audio.CurrentContext()` | `audio` | Nil before the game runs. |
| `audio.NewContext(sampleRate)` | `audio` | Explicit context; one sample rate. |
| `(*audio.Context).NewPlayerF32(src)` | `audio` | Player for float32 streams. |
| `(*audio.Context).NewPlayerFromBytes(pcm)` | `audio` | Cheap one-shot player. |
| `audio.NewInfiniteLoopF32(src, length)` | `audio` | Loops a seekable F32 stream. |
| `(*audio.Player).Play/Pause` | `audio` | No error returns in v2. |
| `(*audio.Player).SetVolume(v)` | `audio` | Linear; > 1 allowed in v2.10+. |
| `vorbis.DecodeF32(r)` | `audio/vorbis` | Ogg/Vorbis → F32 stream. |
| `wav.DecodeF32(r)` | `audio/wav` | WAV → F32 stream. |
| `mp3.DecodeF32(r)` | `audio/mp3` | MP3 → F32 stream. |
| `(*vorbis.Stream).Length()` | `audio/vorbis` | Decoded length in bytes. |
| `audio.ResampleReaderF32(r, length, from, to)` | `audio` | Resample an F32 reader. |

## Format rules

- Stream format: 32-bit float little endian, 2 channels (stereo), for the F32 APIs.
- Context sample rate must equal the stream sample rate; typically 44100.
- 16-bit APIs (`NewPlayer`, `NewInfiniteLoop`, `DecodeWithoutResampling`) still exist; do not pair
  them with F32 decoders.
- The player does not close the source; close files yourself after decoding.

## Decoder/player pairing

| Decoder | Loop wrapper | Player |
|---------|--------------|--------|
| `vorbis.DecodeF32` | `NewInfiniteLoopF32` | `NewPlayerF32` |
| `wav.DecodeF32` | `NewInfiniteLoopF32` | `NewPlayerF32` |
| `mp3.DecodeF32` | `NewInfiniteLoopF32` | `NewPlayerF32` |
| `DecodeWithoutResampling` | `NewInfiniteLoop` | `NewPlayer` |

SFX path: decode once → keep `[]byte` PCM → `NewPlayerFromBytes` per play. Music path: decode once
→ `NewInfiniteLoopF32` → one long-lived `PlayerF32`.

## Loop math

```go
stream, _ := vorbis.DecodeF32(bytes.NewReader(ogg))
loop := audio.NewInfiniteLoopF32(stream, stream.Length())
```

- `Length()` is the decoded byte length; pass the exact value, not the compressed file size.
- Intro + loop: decode the intro separately and start the loop after the intro's duration; or use
  the WithIntro variant when available.
- Seamless loops need trimmed assets; encoder delay/padding causes a gap.

## Volume

```text
final = master * group * perSound
```

- Clamp to [0, 1] unless deliberately amplifying (v2.10 allows > 1).
- Set music volume live when sliders move; SFX volume applies on the next `NewPlayerFromBytes`.
- Store linear values; convert dB in the UI if you display dB.
- Mute = volume 0, not stopping the player, so unmute resumes instantly.

## Fade

```go
func step(cur, target, speed, dt float64) float64 {
    d := target - cur
    if math.Abs(d) <= speed*dt {
        return target
    }
    return cur + math.Copysign(speed*dt, d)
}
```

Or linear over a fixed duration; either way use `dt` from `Update`, not frame counts.

## Test checklist

1. SFX plays on the first input; no init-order crash.
2. 20 rapid SFX: no distortion, cap respected.
3. Music loops without a gap; pause/resume works.
4. Volume sliders change music immediately and SFX on next play; mute/unmute works.
5. Fade completes in the intended time at 30/60/144 fps.
6. Missing audio device: game runs silently.
7. WASM: audio starts after a user gesture; reload behavior is acceptable.
8. Bad asset: decode error logged, game continues.
9. Scene change does not restart or duplicate music.
10. Settings persist across restart (`ebitengine-save`).
