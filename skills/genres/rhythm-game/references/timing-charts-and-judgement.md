# Timing, charts and judgement

Depth for `rhythm-game`: clocks, calibration, chart math and the judgement state machine.

## Clocks

| Platform | Clock | Notes |
|----------|-------|-------|
| Web Audio | `AudioContext.currentTime` | Seconds; advances per render block. |
| Godot | `Time.get_ticks_usec()` + `AudioServer` latency | Compensate mix + output latency. |
| Unity | `AudioSettings.dspTime` | Sample-accurate; schedule with `PlayScheduled`. |
| Phaser | `this.sound` seek/duration + Web Audio | Prefer the underlying Web Audio clock for judgement. |
| Console/mobile native | platform audio clock | Never use frame deltas. |

Formula:

```text
song_time = clock_now - song_start - calibration
```

## Calibration procedure

1. Play a steady click at 120 BPM.
2. Player taps 16–32 times.
3. Record `tap_time - nearest_beat_time`.
4. Discard the top/bottom 20 %, take the median.
5. Store per device; allow manual adjustment in ±5 ms steps.

- Positive offset = audio is late, so judgement time should be reduced.
- Re-calibrate after changing output device (headphones, Bluetooth, TV).

## Chart math

```text
seconds_per_beat = 60 / bpm
time(beat)       = chart_offset + beat * seconds_per_beat
```

BPM changes:

```text
for each section: time_at_section_start = previous + beats_in_section * 60 / bpm
```

- Store `chart_offset` in the chart (authoring), and `calibration` in settings (device). Never
  mix them.
- Validate: sorted times, lane bounds, no duplicate lane/time collisions, hold lengths > 0.

## Approach and spawn

```text
spawn when song_time >= note.time - approach_time
y = hit_y - (note.time - song_time) / approach_time * distance
```

- `approach_time` 0.8–2.0 s is common; scroll speed = distance / approach_time.
- Spawn slightly before the window to avoid pop-in.
- Pool note objects; charts can have thousands.

## Judgement state machine

```text
Pending --press within window--> Judged(grade)
Pending --song_time > late--> Missed
Holding --release before tail--> Broken
Holding --tail reached--> Complete
```

- `nearestUnjudged(lane, t)`: earliest note in the lane with `|t - note.time| <= max_window`.
- On press, consume at most one note.
- On update, mark misses for notes past `time + miss_window`.
- Holds: head judged on press; ticks every `tick_interval` while held; break on early release.

## Scoring

```text
grade_value: Perfect 1.0, Great 0.9, Good 0.6, Bad 0.3, Miss 0
accuracy = Σ(note_weight * grade_value) / Σ(note_weight)
```

- Hold weight = 1 + length_beats * 0.1 (example).
- Combo multiplier: `1 + min(combo, 100) * 0.01`, or stepped tiers.
- Cap score so a full perfect is achievable and a single miss is not catastrophic.
- Show early/late average; it doubles as calibration feedback.

## Test checklist

1. First note hittable after count-in.
2. Notes align with beats at 60/120/180 BPM.
3. Calibration shifts judgement consistently, not visuals only.
4. Pause/resume keeps song time continuous.
5. Holds: head, ticks, tail, early release.
6. Misses fire exactly once per note.
7. Chart with BPM change stays aligned.
8. 60/120/144 Hz displays judge identically for the same press time.
9. Results accuracy matches manual count.
10. Bluetooth/headset calibration changes results in the expected direction.
