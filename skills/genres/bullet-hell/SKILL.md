---
name: bullet-hell
description: >
  Build a bullet-hell / shoot-'em-up: tiny hitboxes, readable bullet patterns, aimed/spread/ring/
  spiral/laser attacks, boss phases, grazing and scoring, bombs, difficulty ranks, pooling and
  deterministic replays. Use for a danmaku, shmup or twin-stick bullet game.
---

# Bullet-hell

A bullet-hell is a readability and pattern-design problem disguised as a shooter. The player
survives by reading a dense screen and threading a tiny hitbox through it. This is a
**compositional** skill: pair with `game-feel`, `audio-design` and `performance-optimization`.

## When to use

- Use for a danmaku/shmup with dense patterns, bosses, grazing or score chains.
- Use when patterns feel unfair, bullets are unreadable, or the frame rate collapses.

**When *not* to use:** twin-stick with sparse projectiles → `fps-shooter`/`roguelike` adapt;
tower defense → `tower-defense`; a single-bullet platformer → `platformer`.

## Core loop

```text
dodge -> position -> graze -> damage -> phase clear -> score -> next pattern
```

- The hitbox is a point (or a few pixels), not the sprite.
- The screen is a contract: every bullet is visible, distinct and dodgeable.
- Patterns alternate pressure and release; constant density is exhausting.

## Readability rules

- Hitbox dot visible during focus/slow mode; sprite can be much larger.
- Bullet color encodes behavior: e.g. pink = aimed, blue = ring, yellow = laser warning.
- Keep bullet speed and size consistent per type; do not reskin a fast bullet as a slow one.
- Background contrast: dark, low-detail playfield; bullets are the brightest layer.
- Cap on-screen bullets; when exceeded, simplify the pattern rather than dropping frames.
- Telegraph lasers and big attacks for at least 0.5–1 s.

## Pattern vocabulary

| Pattern | Shape | Use |
|---------|-------|-----|
| Aimed | single/fan at player | pressure, punishes standing still |
| Spread | fixed fan | area denial |
| Ring | circle outward | forces repositioning |
| Spiral | rotating emitter | sustained movement |
| Wall | line with a gap | reads as a gate |
| Laser | telegraphed line | burst punishment |
| Homing | slow tracking | forces movement, needs a lifetime cap |
| Curving | acceleration/turn | late-fight complexity |

- Compose phases from 2–4 patterns, then a rest beat.
- Give every pattern a safe lane or a dodge route; test with a replay, not just visually.
- Density comes from overlap and timing, not only bullet count.

## Boss phases

```text
phase 1: slow aimed fans (teach)
phase 2: rings + movement (test)
phase 3: spiral + laser (combine)
phase 4: desperation, shorter cycles, score bonus
```

- Clear or convert bullets on phase transition; never kill the player during a cutscene.
- Time limit per phase; timeout advances instead of soft-locking.
- Health bar with phase pips; show the next phase countdown.

## Player systems

- Focus/slow mode: reduced speed, visible hitbox, tighter shot.
- Bombs: invulnerability window, bullet clear, limited count; death-bomb optional.
- Lives/continues: extends at score thresholds; continue resets score or rank.
- Graze: near-miss radius grants score/energy; show a subtle spark.
- Shot types: spread vs focused, with a clear trade-off.

## Scoring

```text
score = base * chain * graze_bonus * no_miss_bonus
```

- Chain: keep killing within a window; decays instead of resetting harshly.
- Risk/reward: point-blank kills, grazing, collecting items at the top of the screen.
- Show the multiplier and its timer; hidden scoring is not a choice.
- Replays: store input per fixed tick and the seed; verify determinism.

## Technical

- Bullets as structs in a pooled array (SoA: position, velocity, type, age, radius).
- Fixed timestep for simulation; render interpolation for smoothness.
- Collision: uniform grid or spatial hash; player hitbox tested separately and cheaply.
- Bullet cap (e.g. 2,000–10,000) with graceful pattern degradation.
- Batch draw by bullet type/atlas; avoid per-bullet `SpriteBatch.Begin`.
- Cull outside the playfield with a margin; recycle immediately.

## Difficulty

- Rank/dynamic difficulty: increase density with survival time, decrease on deaths.
- Difficulty modes change patterns and bullet speed, not only health.
- Practice mode: stage/boss select, slowdown, infinite lives.
- Accessibility: hitbox size option, reduced flash, slower bullets, auto-bomb.

## Pitfalls

- **Unreadable walls** → same color/speed for everything. Encode behavior, keep contrast.
- **Unfair off-screen kills** → spawn outside the visible area with a warning.
- **Frame drops at bullet cap** → per-bullet allocations/begin-end. Pool and batch.
- **Homing forever** → no lifetime cap. Expire or cap turn rate.
- **Death during dialogue/transition** → clear bullets, grant i-frames.
- **Patterns repeat forever** → no phase/rest structure. Alternate pressure and release.
- **Hidden scoring** → players cannot improve. Show chain, graze and multiplier.
- **Bomb trivializes everything** → limit count and rank impact.
- **Replay desync** → variable dt or unseeded RNG. Fixed tick + stored seed.
- **Tiny hitbox invisible** → show it in focus mode and in the options preview.

## Composition

- **Feel:** `game-feel` for hit-stop, shake, flash and graze feedback.
- **Audio:** `audio-design` for shot/bomb/graze layers and boss music phases.
- **Performance:** `performance-optimization` for pooling and draw batching.
- **Levels:** `level-design` for stage pacing and safe-lane reads.
- **UI:** `game-ui-ux` for score, chain, lives and pause clarity.

## References

- Read `references/patterns-scoring-and-replays.md` for emitter pseudocode, pattern tables,
  phase scripting, scoring math and a bullet-hell test checklist.
