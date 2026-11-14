---
name: procedural-audio
description: >
  Generate sound and music at runtime: oscillators, ADSR envelopes, noise, filters, SFX recipes,
  arpeggios, and adaptive layers. Engine bindings for Godot AudioStreamGenerator, Unity
  OnAudioFilterRead and Web Audio. Use for synthesized SFX, dynamic music, or audio without assets.
---

# Procedural audio

Procedural audio synthesizes samples from math instead of playing recorded files. It is ideal for
variation (footsteps, impacts), tiny builds, and adaptive music. This is a **compositional** skill:
pair it with `audio-design` for mixing and buses, and an engine audio skill for playback.

## When to use

- Use when generating SFX/music at runtime, or when you need endless variation without assets.
- Use when a game jam or prototype has no audio budget.

**When *not* to use:** recorded/orchestral sound is the goal → `audio-design`; simple playback and
mixing only → engine audio skill; DSP plugin development → out of scope.

## Building blocks

| Block | What it does | Typical use |
|-------|--------------|-------------|
| Oscillator | sine/square/saw/triangle at a frequency | tones, lasers, engines |
| Noise | white/pink random samples | explosions, wind, footsteps |
| Envelope | ADSR gain over time | removes clicks, shapes impact |
| Filter | low/high/band-pass | muffling, sweeps, resonance |
| Pitch envelope | frequency ramp over time | lasers, jumps, pickups |
| LFO | slow modulation | vibrato, tremolo, engine wobble |

Sample generation:

```text
phase += freq / sample_rate
sample = sin(phase * TAU) * envelope(t)
```

- Phase must wrap (`fmod(phase, 1.0)`) to avoid float precision loss.
- `sample_rate` is the output rate (44.1/48 kHz), not the frame rate.
- Always multiply by an envelope; raw on/off produces clicks.

## SFX recipes

```text
laser:      saw 1200 -> 300 Hz over 0.15 s, fast decay
explosion:  white noise, low-pass 800 Hz -> 80 Hz, 0.6 s decay
jump:       square 300 -> 600 Hz, 0.1 s, short attack
pickup:     two sines (880, 1320 Hz), 0.05 s each
footstep:   noise burst 30 ms, band-pass 400-1200 Hz, random pitch ±10 %
hit:        noise + sine 150 Hz, 60 ms, hard attack
UI click:   sine 1000 Hz, 15 ms, no sustain
engine:     saw at RPM-mapped freq + LFO, looped
```

- Randomize pitch (±5–15 %) and volume (±2 dB) per instance for variety.
- Layer a tonal component and a noise component for weight.
- Keep one-shots under ~1 s unless they are ambience.

## Music

- Pick a scale (minor pentatonic is forgiving), a tempo, and 4–8 chord roots.
- Arpeggiate chord tones on a grid (1/8 or 1/16 notes); add a bass root.
- Adaptive layers: intensity 0–1 crossfades percussion/bass/lead stems.
- Seed the generator so a track is reproducible; vary between sessions deliberately.

```text
beat_duration = 60 / bpm
note_time     = step * beat_duration / steps_per_beat
```

## Engine bindings

### Godot 4 — AudioStreamGenerator

```gdscript
@onready var player: AudioStreamPlayer = $AudioStreamPlayer
var playback: AudioStreamGeneratorPlayback
var phase := 0.0

func _ready() -> void:
    var gen := AudioStreamGenerator.new()
    gen.mix_rate = 22050.0        # lower rate is cheaper from GDScript
    gen.buffer_length = 0.1
    player.stream = gen
    player.play()
    playback = player.get_stream_playback()

func _process(_delta: float) -> void:
    var frames := playback.get_frames_available()
    for i in frames:
        playback.push_frame(Vector2.ONE * sin(phase * TAU) * 0.2)
        phase = fmod(phase + 440.0 / 22050.0, 1.0)
```

- `get_frames_available()` tells you how much the buffer can take; push exactly that.
- GDScript per-sample loops are expensive — the docs recommend C#/GDExtension or a lower
  `mix_rate` (11,025/22,050 Hz) for real-time generation.
- `AudioStreamGeneratorPlayback.get_skips()` reveals underruns; increase `buffer_length` if > 0.
- For one-shots, pre-render into an `AudioStreamWAV` and play normally.

### Unity — OnAudioFilterRead

```csharp
[RequireComponent(typeof(AudioSource))]
public class SynthVoice : MonoBehaviour {
    double phase;
    const double Freq = 440.0;

    void OnAudioFilterRead(float[] data, int channels) {
        double inc = Freq / AudioSettings.outputSampleRate;
        for (int i = 0; i < data.Length; i += channels) {
            float s = (float)System.Math.Sin(phase * 2.0 * System.Math.PI) * 0.2f;
            for (int c = 0; c < channels; c++) data[i + c] = s;
            phase += inc;
            if (phase > 1.0) phase -= 1.0;
        }
    }
}
```

- `OnAudioFilterRead` runs on the audio thread: no `UnityEngine` API calls, no allocations.
- A silent looping `AudioClip` on the `AudioSource` is needed to drive the filter.
- `AudioSettings.outputSampleRate` is the real rate; never assume 44.1 kHz.
- Spatialization is applied before the filter; multiply, do not overwrite, if you need panning.

### Web Audio

```js
const ctx = new AudioContext();
const osc = ctx.createOscillator();
const gain = ctx.createGain();
osc.type = "sawtooth";
osc.frequency.setValueAtTime(1200, ctx.currentTime);
osc.frequency.exponentialRampToValueAtTime(300, ctx.currentTime + 0.15);
gain.gain.setValueAtTime(0.0001, ctx.currentTime);
gain.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + 0.005);
gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.2);
osc.connect(gain).connect(ctx.destination);
osc.start(); osc.stop(ctx.currentTime + 0.22);
```

- Schedule with the audio clock (`currentTime`), not `setTimeout`.
- Exponential ramps cannot reach 0; use a small floor and stop the node.
- For many one-shots, pre-render an `AudioBuffer` and play via `AudioBufferSourceNode`.
- Resume the context on the first user gesture (autoplay policy).

## Mixing and performance

- Pre-render static SFX; reserve real-time synthesis for variation and music.
- Pool voices and cap simultaneous generators (e.g. 16–32).
- Normalize output and leave headroom; add a limiter on the bus.
- Generate on a worker/audio thread where possible; never allocate per sample.
- Spatialize after synthesis (engine 3D audio), not by hand-rolling pan.

## Pitfalls

- **Clicks/pops** → no attack or release; always envelope, and ramp gain.
- **Aliasing** → square/saw above Nyquist/2. Band-limit or use sine at high pitches.
- **DC offset** → asymmetric waveforms; add a high-pass at ~20 Hz.
- **Buffer underruns** → generating less than `get_frames_available()` per frame. Fill fully and
  check `get_skips()`.
- **Audio-thread violations** → Unity API calls or `new` inside `OnAudioFilterRead`.
- **Sample-rate mismatch** → assuming 44.1 kHz. Read the engine's actual rate.
- **GDScript too slow** → per-sample loops at 44.1 kHz. Lower mix rate or pre-render.
- **Deterministic machine-gun audio** → no pitch/volume randomization.
- **Music drifts** → scheduling notes off frame time instead of the audio clock.

## Composition

- **Mixing/buses:** `audio-design` for ducking, limiter, adaptive music structure.
- **Engine playback:** `godot-audio`, `phaser-audio`, `unreal-audio`; `ebitengine-audio`.
- **Rhythm:** `rhythm-game` for judgement and calibration.
- **Performance:** `performance-optimization` for voice budgets and GC.
- **Accessibility:** `accessibility` for captions/visual cues for generated audio.

## References

- Read `references/synthesis-recipes-and-engine-bindings.md` for oscillator math, ADSR/filter
  formulas, more recipes, note scheduling and an audio test checklist.
