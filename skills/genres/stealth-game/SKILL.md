---
name: stealth-game
description: >
  Build a stealth game: vision cones, hearing and light, suspicion meters, patrol and search AI,
  takedowns, distractions, level routing and ghost/assault playstyles. Use for stealth levels,
  stealth-action, or detection systems that feel unfair.
---

# Stealth game

Stealth is information and permission: the player reads patrols, predicts sight and sound, and
chooses when to move. Fairness comes from consistent, readable detection rules. This is a
**compositional** skill: pair with `game-ai`, `level-design` and `audio-design`.

## When to use

- Use when building detection, patrols, vision cones, takedowns, or stealth level layouts.
- Use when players say detection feels random or guards see through walls.

**When *not* to use:** horror chases with little hiding → `horror-game`; full combat AI →
`fps-shooter`/`game-ai`; extraction raids where stealth is one option → `extraction-shooter`.

## Detection model

```text
seen = in_cone(angle, distance)
       and line_of_sight(clear)
       and light_level > threshold
       and target_not_fully_occluded
```

- **Vision**: cone angle, range, peripheral falloff, vertical limit.
- **Hearing**: noise radius per action (walk/run/door/landing), attenuated by walls.
- **Light**: shadow zones reduce detection speed, not immunity.
- **Occlusion**: raycast to head/chest; partial cover should partially hide.

## Suspicion meter

```text
0-30    unaware      patrol
30-70   suspicious   investigate, look toward stimulus
70-99   alert        search area, call allies
100     detected     chase/combat
```

- Fill rate depends on distance/light/noise; decay slower than fill (commitment).
- Show state with animation, audio and an optional UI meter; never hidden randomness.
- One global meter per guard; group alerts propagate with a delay and a cap.

## AI states

| State | Behavior |
|-------|----------|
| Patrol | waypoints, pauses, look-arounds |
| Suspicious | stop, turn to stimulus, approach cautiously |
| Search | sweep last known position + nearby hiding spots |
| Alert | chase, call backup, guard exits |
| Return | resume patrol after cooldown |

- Last-known-position, not omniscient tracking.
- Search should be escapable: a timer, a path, and a clear "lost you" cue.
- Guards communicate via sight/sound, not telepathy.

## Player tools

- Crouch/sneak (slower, quieter), cover peek, lean optional.
- Distractions: throwables, noise traps, lights, disguises.
- Takedowns: lethal/non-lethal, from behind/above, with detection risk.
- Hiding spots: shadows, lockers, crowds; entering must be quick and readable.
- Recon: binoculars, drone, marking enemies (limited).

## Level design

- Multiple routes: low (shadows), mid (cover), high (vents/roofs).
- Patrol loops with overlapping cones create timing puzzles, not walls.
- Safe observation points before each challenge.
- Checkpoints after major rooms; stealth failure should not erase 20 minutes.
- Ghost, pacifist and assault paths should all be viable where the fiction allows.

## Difficulty

- Adjust cone range, suspicion fill rate, search duration, checkpoint density.
- Do not make detection binary at higher difficulty; make recovery harder.
- Accessibility: colorblind cone cues, subtitle for guard barks, reduced flashes.

## Pitfalls

- **Detection through walls** → LOS missing or mask wrong. Raycast to multiple points.
- **Instant detection at the cone edge** → no falloff or grace. Scale fill with distance/light.
- **Guards forget instantly** → no search state; unsatisfying. Search last known area.
- **Guards track through walls** → global target position. Use last-known-position.
- **No readable state** → player cannot tell suspicion. Animate/audio cues.
- **Stealth is the only viable path but untelegraphed** → forced ghosting. Show tools/routes.
- **Checkpoint starvation** → one mistake replays the level. Checkpoint per room.
- **Cone visuals lie** → debug draw must match the actual test.
- **Allies alert instantly across the map** → propagate with delay/range.

## Composition

- **AI:** `game-ai`, `ai-behavior-trees-utility-ai` for patrol/search states.
- **Levels:** `level-design` for routes, cover and sightlines.
- **Audio:** `audio-design` for noise cues and guard barks.
- **UI:** `game-ui-ux` for suspicion/hiding feedback.
- **Horror overlap:** `horror-game` when the fantasy is fear over planning.

## References

- Read `references/detection-patrols-and-levels.md` for cone math, meter tuning, patrol/search
  pseudocode and a stealth test checklist.
