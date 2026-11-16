# Map, gates and pacing

Depth for `metroidvania`: graph, gates, tests.

## Dependency graph

```text
Start -> Forest -> [Dash] -> Tunnels -> [Grapple] -> Chasm
   |        |                    |                      |
   +------> Village <-----------+----------------------+
                 |
              [Double jump] -> Upper City -> Boss -> End
```

- Draw nodes (regions/rooms) and edges (gates); mark the critical path.
- Every edge needs a gate type and the ability that opens it.
- Optional edges reward exploration; they must not be required by the critical path.

## Gate table

| Gate | Visual | Ability | Fallback |
|------|--------|---------|----------|
| High ledge | cracked wall, upward arrow | double jump | stairs after shortcut |
| Wide gap | broken bridge, wind | dash | lower route |
| Anchor | metal ring | grapple | elevator |
| Boss door | sealed sigil | boss key | none (checkpoint outside) |

- Same gate type = same visual language everywhere.
- A gate seen early should be memorable: unique silhouette, sound, color.

## Ability pacing

| Time | Ability | Test |
|------|---------|------|
| 0–20 min | base move | gap, ledge |
| 20–60 min | dash | wide gap, dodge |
| 1–2 h | double jump | vertical shaft |
| 2–4 h | grapple | chasm, combat pull |
| 4–6 h | traversal upgrade | shortcut loop |

- Teach in a safe room, test in the next room, gate within 10 minutes.
- Avoid two abilities in the same beat unless they combine immediately.

## Softlock audit

1. List every one-way drop and closed door.
2. For each, verify a return path exists with the current ability set.
3. Verify respawn keeps key items and flags.
4. Verify boss doors open after defeat and do not trap the player.
5. Verify sequence breaks either have a fallback or are blocked by geometry.

## Checklist

1. Dependency graph has no orphan regions.
2. Every gate has a consistent visual and an ability that opens it.
3. Each ability has a tutorial, a test, and a gate.
4. Shortcuts loop the map after each major ability.
5. Map shows outlines, save rooms and seen gates.
6. Region identity is readable without the map.
7. Death respawns at a save room without progress loss.
8. No one-way path lacks a return.
9. Bosses have a checkpoint at the door.
10. Optional upgrades are power, not required grind.
