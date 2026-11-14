# Synthesis recipes and engine bindings

Depth for `procedural-audio`: math, envelopes, filters, scheduling and tests.

## Oscillator math

```text
phase += freq / sample_rate
sine     = sin(phase * TAU)
square   = phase < 0.5 ? 1 : -1
saw      = 2 * phase - 1
triangle = 1 - 4 * abs(phase - 0.5)
```

- Wrap phase with `fmod(phase, 1.0)`.
- Square/saw alias; at high frequencies prefer sine or band-limited variants.
- Detune two oscillators by a few cents for thickness.

## ADSR

```text
attack:  gain 0 -> 1 over A seconds
decay:   gain 1 -> S over D seconds
sustain: hold S while note held
release: gain S -> 0 over R seconds
```

- Minimum attack ~2 ms and release ~5 ms to avoid clicks.
- Percussive: A=0.001, D=0.1, S=0, R=0.05.
- Pad: A=0.3, D=0.4, S=0.6, R=0.8.

## One-pole low-pass

```text
alpha = dt / (RC + dt)
y += alpha * (x - y)
```

- `RC = 1 / (TAU * cutoff_hz)`.
- Sweep cutoff exponentially for natural-sounding filters.
- Resonance needs a state-variable/biquad filter; one-pole has none.

## Recipes (parameter table)

| Sound | Source | Pitch | Envelope | Filter |
|-------|--------|-------|----------|--------|
| Laser | saw | 1200→300 Hz / 0.15 s | A 1 ms, R 150 ms | low-pass 4 kHz |
| Explosion | noise | — | A 5 ms, D 0.6 s | LP 800→80 Hz |
| Jump | square | 300→600 Hz / 0.1 s | A 2 ms, R 80 ms | — |
| Pickup | sine ×2 | 880, 1320 Hz | 50 ms each | — |
| Footstep | noise | ±10 % | 30 ms | BP 400–1200 Hz |
| Hit | noise + sine | 150 Hz | 60 ms | LP 2 kHz |
| Engine | saw + LFO | RPM-mapped | sustain | LP by throttle |

## Note scheduling

```text
step_duration = 60 / bpm / steps_per_beat
next_note_time += step_duration
schedule(note, next_note_time)   // audio clock, not frame time
```

- Look ahead 100–200 ms; schedule events in the future.
- Re-sync to the audio clock on pause/resume.
- Quantize generative notes to the scale to avoid wrong-sounding randomness.

## Mixing

- Peak target around −1 dBFS on the master; leave headroom for SFX.
- Cap voices; steal the quietest/oldest.
- Add a limiter after summing generated + recorded audio.
- Use buses: SFX, music, UI, ambience; duck music under dialogue.

## Test checklist

1. No clicks at note start/stop.
2. No underruns (`get_skips()` = 0 / no dropouts).
3. Output level consistent across generated sounds.
4. Pitch randomization stays musical.
5. 44.1 and 48 kHz both sound correct.
6. Audio thread performs no allocations (Unity).
7. Autoplay resume works after a user gesture (web).
8. Pause/resume does not drift music.
9. Voice cap holds under spam.
10. Captions/visual cues exist for important generated sounds.
