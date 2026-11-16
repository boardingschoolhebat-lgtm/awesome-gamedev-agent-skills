---
name: metroidvania
description: >
  Design a metroidvania: ability-gated nonlinear exploration, lock-and-key map structure,
  backtracking and shortcuts, map/fog, ability pacing, sequence breaking, save rooms and boss
  gates. Use for an interconnected action-exploration game.
---

# Metroidvania

A metroidvania is a map you unlock with abilities. Progress is knowledge plus capability: see a
blocked path, remember it, find the ability, return. This is a **compositional** skill: pair with
`platformer`, `level-design` and `save-systems`.

## When to use

- Use when designing an interconnected map with ability gates, shortcuts and backtracking.
- Use when players get lost, sequence-break into softlocks, or backtracking feels like chores.

**When *not* to use:** linear platformer → `platformer`; open-world without gates → `level-design`;
roguelike runs → `roguelike`; pure puzzle rooms → `puzzle`.

## Core loop

```text
explore -> see a lock -> find the key/ability -> return -> shortcut -> new region
```

- The lock must be legible before the key is found: color, shape, sound, silhouette.
- The ability should change movement or combat, not just open one door.
- Every region teaches, tests, then connects back.

## Map grammar

| Element | Job |
|---------|-----|
| Corridor | pacing, combat, secrets |
| Hub room | orientation, multiple exits |
| Ability gate | locks progress behind a capability |
| Shortcut | rewards return trips, loops the map |
| Save room | checkpoint, refill, respite |
| Boss arena | gate to the next region |
| Secret | optional upgrade/lore |

- Draw a dependency graph first: regions as nodes, gates as edges.
- Critical path should be 8–15 hours; optional content adds breadth, not gating.
- One-way drops are fine if a shortcut opens the way back.

## Ability gating

```text
ability -> verb -> gate type -> region unlocked
double jump -> vertical -> high ledge -> upper city
dash -> horizontal -> wide gap -> transit tunnels
grapple -> traversal -> anchor points -> chasm
```

- Each ability needs a safe tutorial room, a test room, and a gate that uses it.
- Do not require two new abilities in the same room without teaching both.
- Gates should be readable at a glance and consistent across the map.
- Abilities double as combat tools; avoid keys that are only keys.

## Backtracking

- Make return trips faster: shortcuts, elevators, fast travel, speed upgrades.
- Place new content on old routes after each ability (a door now opens, an NPC moves).
- Reward revisits with upgrades, lore or a shortcut, not only filler enemies.
- Avoid long dead-end walks; put a landmark or a secret on the way.
- Track "unfinished business" in the map so players can plan.

## Map and guidance

- Fog of war with room outlines; mark save rooms, vendors, gates and objectives.
- Distinct region palettes and silhouettes; the player should know where they are.
- A map marker for a seen-but-unopenable gate reduces memory load.
- NPCs and environmental clues point to the next ability without a quest arrow.
- Optional: map percentage and completion stats.

## Sequence breaking and softlocks

- Decide policy: embrace skilled breaks (with fallbacks) or hard-gate them.
- Every one-way path needs a way back, or a respawn that does not lose progress.
- Test: can a player reach a region without the intended ability and get stuck?
- Boss gates should not close behind the player without a checkpoint.
- Death should respawn at the last save room with progress intact; optional corpse runs.

## Combat and bosses

- Combat spaces sized for the movement set; no cramped rooms with long-range enemies.
- Enemy variety tests the newest ability; reuse archetypes with new combinations.
- Bosses gate regions and test traversal + combat; checkpoints before the arena.
- Health/energy upgrades are optional power, not mandatory grind.

## Pacing

```text
0–20 min: movement + first gate
20–60 min: first ability, first shortcut
1–3 h: second region, mobility upgrade
3–8 h: ability chain, bosses, map loops
```

- A new ability every 30–60 minutes early, slower later.
- Alternate exploration, combat and boss beats; do not stack three gauntlets.

## Pitfalls

- **Lost players** → no landmarks, no map markers. Add region identity and gate markers.
- **Backtracking slog** → no shortcuts. Open loops after each ability.
- **Invisible locks** → gate looks like scenery. Use consistent visual language.
- **Softlock** → one-way drop with no return. Add a shortcut or respawn.
- **Ability is a key** → boring. Make it change movement/combat.
- **Difficulty spike** → new region assumes mastery not taught. Add a test room.
- **Map spoils everything** → show outlines, not secrets.
- **Collectible overload** → noise. Fewer, meaningful upgrades.
- **Boss gate without checkpoint** → retry fatigue. Save room at the door.
- **Sequence break breaks story** → gate critical scenes or support the skip.

## Composition

- **Platforming:** `platformer` for movement, coyote time, hazards.
- **Levels:** `level-design` for whiteboxing, sightlines and pacing.
- **Save:** `save-systems` for save rooms, respawn and versioned state.
- **AI:** `game-ai` for patrols, flying enemies and boss patterns.
- **UI:** `game-ui-ux` for map, markers and completion.

## References

- Read `references/map-gates-and-pacing.md` for a dependency graph template, gate table, ability
  pacing, softlock tests and a metroidvania checklist.
