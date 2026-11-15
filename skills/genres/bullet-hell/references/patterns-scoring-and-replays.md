# Patterns, scoring and replays

Depth for `bullet-hell`: emitters, phases, scoring and tests.

## Bullet record

```text
struct Bullet { vec2 pos, vel; float radius, age, life; u8 type; u8 flags; }
pool: fixed array + free list; reset on spawn, never allocate mid-fight
```

- Update: `pos += vel * dt`; optional `vel = rotate(vel, turn * dt)`.
- Despawn on `age > life`, off-field margin, or collision.
- Group by type for drawing; one texture atlas per behavior family.

## Emitter pseudocode

```text
func fan(origin, count, spread_deg, speed, aim_at_player):
    base = aim_at_player ? angle_to(player) : 0
    for i in 0..count-1:
        a = base + lerp(-spread/2, +spread/2, i/(count-1))
        spawn(origin, dir(a) * speed)

func ring(origin, count, speed, offset):
    for i in 0..count-1:
        spawn(origin, dir(offset + i * 360/count) * speed)

func spiral(origin, speed, turn, interval):
    every interval: spawn(origin, dir(_angle) * speed); _angle += turn
```

- Aimed patterns should lead slightly or fire a fan so strafing is rewarded.
- Add a small random jitter only for visual variety, never for fairness-critical gaps.

## Phase script (data-driven)

```json
{
  "boss": "clockwork",
  "phases": [
    { "hp": 1.0, "patterns": ["aimed_fan"], "duration": 20 },
    { "hp": 0.7, "patterns": ["ring", "spiral"], "duration": 25 },
    { "hp": 0.4, "patterns": ["laser", "wall"], "duration": 30 },
    { "hp": 0.15, "patterns": ["spiral_fast", "aimed_fan"], "duration": 40 }
  ]
}
```

- On phase change: clear bullets, 1 s i-frames, camera/audio beat, then start.
- Timeout: advance phase and award time bonus instead of stalling.

## Scoring math (example)

```text
kill:     100 * chain
graze:    10 * chain
chain:    +1 per kill, resets after 3 s without a kill (or decays 1/s)
no-miss:  x1.2 at stage end
extend:   at 1,000,000 and 3,000,000
```

- Cap the chain multiplier so one long stage does not dwarf everything.
- Show a floating score popup only for meaningful events; avoid visual noise.

## Replay format

```text
header: version, seed, stage, ship, difficulty
frames: per fixed tick, packed input bits (left/right/up/down/focus/shot/bomb)
result: score, deaths, checksum of final state
```

- Simulate from the seed; never record positions.
- Validate the checksum on playback and flag desyncs.

## Test checklist

1. Player hitbox matches the visible dot; sprite does not cause hits.
2. Every pattern has a demonstrated safe route at each difficulty.
3. Bullets spawn on-screen with a telegraph, never inside the player.
4. Phase transitions clear bullets and grant i-frames.
5. Bomb clears bullets, grants i-frames and decrements the count.
6. Graze triggers only inside the graze radius and awards once per bullet.
7. 5,000 bullets hold 60 FPS with no per-frame allocations.
8. Bullet cap degrades patterns instead of dropping frames.
9. Homing bullets expire; lasers telegraph before damage.
10. Replay reproduces score/deaths from the same seed and inputs.
