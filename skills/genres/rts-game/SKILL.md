---
name: rts-game
description: >
  Build a real-time strategy game: selection and commands, unit movement and crowds, fog of war,
  resource economy and production, build orders, combat counters, AI opponents and lockstep or
  server-authoritative networking. Use for an RTS, RTT or large-scale unit command game.
---

# RTS game

An RTS is a command interface over a simulation: many units, one player intent, and a fog that
hides information. The hard parts are control (selection/orders), pathing at scale, and keeping
the simulation fair and readable. This is a **compositional** skill: pair with `game-ai`,
`multiplayer-netcode` and `level-design`.

## When to use

- Use when building an RTS/RTT with unit selection, production, resources and fog of war.
- Use when units clump, pathing collapses, or multiplayer desyncs.

**When *not* to use:** squad tactics with a few units → `fps-shooter`/`co-op-design`; turn-based
strategy → adapt `rpg`/`puzzle` systems; tower defense → `tower-defense`; city building without
armies → `management-sim`.

## Core loop

```text
scout -> expand economy -> produce army -> fight for map control -> tech -> destroy/defend
```

- The player's attention is the scarce resource: minimap, alerts, control groups.
- Every faction needs a clear economic and military identity.

## Command layer

| Input | Behavior |
|-------|----------|
| Click / box drag | select |
| Shift | add to selection |
| Ctrl+group / group key | control groups |
| Right-click | context order (move/attack/gather) |
| Attack-move | move but engage on sight |
| Patrol / hold | stance behavior |

- Orders are queued; show the queue and allow cancel.
- Context orders must be unambiguous (unit under cursor, terrain, resource).
- Selection should be stable: dead units leave the group cleanly.
- Provide attack-move and stop; without them, players cannot micro.

## Movement and crowds

- Pathfinding: A* on a coarse grid, then local avoidance; flow fields for many units to one goal.
- Formation offset around the destination to avoid a single-stack blob.
- Unit collision: soft separation, not hard physics that jams corridors.
- Path requests are budgeted per frame; queue and spread them.
- Stuck detection: repath after a short timeout.

## Fog of war

```text
hidden (never seen) -> explored (terrain remembered) -> visible (units shown)
```

- Visibility from units/buildings; explored terrain persists.
- Enemy units hidden outside vision; buildings may remain as remembered ghosts.
- Server/simulation decides visibility per player; never send hidden units to clients.
- Minimap respects the same fog.

## Economy and production

- Resources: gather rate, worker count, saturation per node, expansion cost.
- Production: queue, build time, supply/population cap, tech prerequisites.
- Supply blocks are a core skill expression; warn clearly.
- Build placement rules: grid, terrain, creep/roads, adjacency bonuses.
- Upkeep/repair and worker defense shape pacing.

## Combat

- Damage types vs armor types; counters create composition decisions.
- Range, projectile speed, overkill, friendly fire (usually off).
- Focus fire and retreat must be responsive; no input lag on orders.
- Engagement readability: health bars, attack indicators, clear silhouettes.
- Deathballs: encourage spread objectives and positional advantage.

## AI opponents

- Economic build order with time-based checkpoints.
- Scouting and reaction: counter the player's composition with a delay.
- Difficulty via decision quality, reaction time and income bonus (declare it), not perfect micro.
- AI should use the same command interface as the player where possible.

## Networking

- **Lockstep**: deterministic simulation, only commands exchanged; needs fixed-point math and
  identical builds. Cheaper bandwidth, brutal desync debugging.
- **Server-authoritative**: server simulates, clients send commands and interpolate; easier to
  secure, heavier bandwidth.
- Command delay (turn rate) hides latency; keep it consistent for all players.
- Reconnect: replay commands or resync a snapshot; never trust client unit counts.

## UI

- Minimap with attack alerts and camera jump.
- Control groups, idle worker button, production tab.
- Resource/supply always visible; low-supply warning.
- Command card with hotkeys; rebindable.
- Post-game: build order, income graph, army value.

## Pitfalls

- **Units clump into one stack** → no separation/formation. Add local avoidance + offsets.
- **Pathfinding spikes** → all units repath every frame. Budget and cache paths.
- **Fog leaks** → server sends hidden units. Filter per player before serialization.
- **Orders feel laggy** → no command acknowledgment or high delay. Acknowledge immediately.
- **Deathball dominates** → no spread objectives or AoE. Add map pressure and counters.
- **Supply block unclear** → no warning. Surface supply and queue status.
- **AI cheats invisibly** → bonus resources without disclosure. Declare difficulty modifiers.
- **Desync in lockstep** → floats/engine physics. Fixed-point, deterministic ordering.
- **Selection breaks on death** → stale ids. Clean groups on unit death.
- **Minimap ignored** → no alerts. Ping and flash on attacks.

## Composition

- **AI/pathing:** `game-ai` for strategic layers; flow fields for crowds.
- **Netcode:** `multiplayer-netcode` for authority/prediction, or lockstep determinism.
- **Balance:** `game-balance` for counters, TTK and economy curves.
- **Levels:** `level-design` for expansions, chokes and map symmetry.
- **UI:** `ui-architecture` for command cards, minimap and alerts.

## References

- Read `references/commands-pathing-and-lockstep.md` for order/selection pseudocode, flow-field
  pathing, fog filtering, economy tables and an RTS test checklist.
