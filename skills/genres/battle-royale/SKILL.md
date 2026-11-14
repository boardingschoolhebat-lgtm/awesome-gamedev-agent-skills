---
name: battle-royale
description: >
  Build a battle royale: lobby/drop, loot distribution, shrinking zone with damage phases, last-
  player-standing win condition, spectate, matchmaking/backfill, bots, and server-authoritative
  combat at scale. Use for a BR/last-one-standing mode or its zone and loot systems.
---

# Battle royale

A battle royale is a match lifecycle plus a shrinking play space. The genre's hard problems are
scale (many players, one match), fairness (server authority, loot RNG) and pacing (drop → loot →
rotate → endgame). This is a **compositional** skill: it builds on `multiplayer-netcode`,
`game-economy` for cosmetics, and a shooter/action genre for combat.

## When to use

- Use when building a last-player-standing mode with a closing zone, loot, and drop-in.
- Use when tuning zone timing, loot tables, bot backfill, or spectate flow.

**When *not* to use:** small-session deathmatch → `fps-shooter` + `multiplayer-netcode`; survival
with persistent worlds → `survival-crafting`; extraction shooters (different risk loop) → adapt
this plus economy.

## Match lifecycle

```text
lobby (queue, party, ready)
  -> deploy (drop choice / skydive)
  -> loot phase (first circle, low pressure)
  -> rotation phases (zone closes, fights)
  -> endgame (small circle, few players)
  -> victory / defeat -> results -> lobby
```

- Target match length explicitly (e.g. 15–25 min) and derive zone timings from it.
- Every phase has a clear player goal; dead time between circles is the enemy.
- Results screen: placement, kills, damage, survival time, XP.

## Must-have systems

1. **Zone** — center, radius, phase timings, damage per second, safe/next circle preview.
2. **Loot** — spawn tables by tier/area, containers, ground items, inventory limits.
3. **Drop/deploy** — spawn selection, skydive/parachute, landing.
4. **Combat** — server-authoritative hits, TTK tuned for the mode.
5. **Inventory** — slots, ammo/consumables, quick-use.
6. **Match state** — alive count, placement tracking, win condition.
7. **Spectate** — follow killer/teammates, free camera, report.
8. **Backfill/bots** — fill matches quickly without ruining fairness.
9. **Anti-cheat** — server validation, rate limits, killcam/replay.

## Zone design

```text
phase n: wait_time, shrink_time, radius_end, dps
center_next = random point inside current circle, biased to land
```

- Publish the next circle early so rotations are decisions, not surprises.
- Damage escalates per phase; early zone should hurt, not execute.
- Shrink rate must be survivable at base movement speed; test the worst-case rotation.
- Final circles: small, readable, with cover — not open fields.
- Handle players outside: damage tick, direction indicator, screen edge marker.

## Loot design

| Tier | Where | Power | Share |
|------|-------|-------|-------|
| Common | everywhere | low | ~60 % |
| Uncommon | buildings | medium | ~25 % |
| Rare | hot zones | high | ~12 % |
| Legendary | airdrops/boss | spike | ~3 % |

- Weight by area risk: hot drops get better loot but more fights.
- Guarantee a minimal kit near landing to avoid "no weapon" deaths.
- Cap total power to keep TTK predictable.
- Server rolls loot; clients never decide drops.
- Disclose paid cosmetic odds; no pay-for-power.

## Patterns

### 1. Zone state machine

```text
Idle -> Waiting(phase) -> Shrinking(phase) -> Waiting(next) ... -> Final
```

- Only the server advances phases; broadcast phase index + timestamps.
- Clients interpolate the visual circle from server time; never simulate damage locally.
- On reconnect, sync to the current phase and remaining time.

### 2. Placement and win condition

```text
on_player_eliminated(p):
    p.placement = alive_count
    alive_count -= 1
    if alive_count == 1: end_match(winner)
```

- Placement is decided by elimination order, ties broken by damage/time.
- Teams: placement when the last member dies; spectator stays on teammates.
- Handle simultaneous deaths deterministically (same tick).

### 3. Bots and backfill

- Bots use the same movement/combat rules; no aimbot-perfect shots.
- Scale bot skill with lobby MMR; mark bots in results for honesty where required.
- Replace disconnected players only before a cutoff (e.g. first circle).
- Bots should rotate toward the zone like players.

### 4. Spectate

- Follow the killer by default; allow teammate cycling.
- Delay spectate feed slightly to prevent ghosting.
- Hide enemy positions not visible to the spectated player if competitive integrity matters.

### 5. Matchmaking

- Queue by region, MMR, party size, input device.
- Start when lobby is full or after a timeout; backfill with bots.
- Never split a party across matches.

## Scale and performance

- Relevance: replicate only nearby players/loot; distant fights are irrelevant.
- Cap entities per cell; despawn far loot.
- Snapshot rate can drop with distance; prioritize nearby combatants.
- Server tick budget: zone + 100 players + loot is heavy — profile per tick.
- Client: pool loot meshes, impostors for distant players, LOD.

## Anti-cheat and fairness

- Server owns position validation, hit registration, loot, and placement.
- Rate-limit fire/interact; validate line of sight and ammo.
- Log suspicious stats (accuracy, headshot rate) for review.
- RNG seeded and logged per match for dispute/replay.

## Pitfalls

- **Dead mid-game** → zone timings too slow; tighten rotations.
- **Unwinnable final circle** → no cover or uphill; hand-place endgame areas.
- **No weapon landing** → no minimum kit guarantee.
- **Loot starvation** → spawn density too low for player count.
- **Client-side zone damage** → cheaters sit outside; server applies damage.
- **Placement wrong on team wipe** → counting players instead of teams.
- **Bots too strong/weak** → fixed skill; scale with lobby.
- **Spectate ghosting** → real-time enemy positions; add delay/filter.
- **Reconnect loses match** → no session resume; restore state by player id.
- **Queue never fills** → no timeout/bot backfill; players wait forever.

## Composition

- **Netcode:** `multiplayer-netcode` for authority, relevance, lag compensation.
- **Combat:** `fps-shooter` or a third-person action skill.
- **Loot/economy:** `game-economy` for cosmetics and reward pacing.
- **Level:** `level-design` for named POIs and rotations.
- **UI:** `game-ui-ux` + `ui-architecture` for zone map, inventory, results.
- **Audio:** `audio-design` for distant gunfire and zone cues.

## References

- Read `references/zone-loot-and-match-flow.md` for zone timing tables, loot weights, placement
  rules and a BR test checklist.
