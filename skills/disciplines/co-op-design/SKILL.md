---
name: co-op-design
description: >
  Design cooperative play: player-count scaling, roles and synergy, revive/downed rules, shared
  vs instanced loot, friendly fire, drop-in/out, communication ping, difficulty and solo parity.
  Use for co-op modes, scaling encounters, or co-op that feels like parallel single-player.
---

# Co-op design

Co-op is not single-player with extra bodies. Every system must answer: what changes when a
second player joins, and does each player matter? This is a **compositional** skill: pair with
`multiplayer-netcode`, `game-ai` and `game-ui-ux`.

## When to use

- Use when adding 2–4 player co-op, scaling enemies, or designing revive/support mechanics.
- Use when co-op trivializes content or one player does everything.

**When *not* to use:** competitive PvP → `multiplayer-netcode` + genre; MMO-scale raids with
fixed roles → adapt this plus `matchmaking`; async/social features only.

## Design pillars

1. **Interdependence** — each player has something the others need.
2. **Readable chaos** — effects and callouts stay legible with N players.
3. **Failure is recoverable** — downed/revive, not instant wipe.
4. **Solo parity** — the game is still playable alone, or explicitly not.
5. **No dead weight** — joining late must not mean watching.

## Scaling

```text
enemy_hp      = base_hp * (1 + 0.6 * (players - 1))
enemy_damage  = base_damage * (1 + 0.25 * (players - 1))
enemy_count   = base_count + (players - 1) * adds_per_extra
loot_per_player = base_loot (instanced) or base_loot * players (shared)
```

- Scale health less than linearly or fights become bullet sponges.
- Add mechanics (adds, splits, simultaneous objectives) before raw stats.
- Scale by role: 2-player co-op needs duo mechanics, not half a 4-player raid.
- Test 1/2/3/4 players explicitly; mid-counts are where scaling breaks.

## Roles and synergy

| Role | Provides | Needs |
|------|----------|-------|
| Tank/breaker | space, aggro | healing, damage |
| DPS | damage | setup, cover |
| Support | heal/buff/revive | protection |
| Utility | crowd control, traversal | follow-up |

- Roles can be soft (weapons/abilities) rather than classes.
- Every role needs a solo-viable baseline; do not hard-gate progress on a partner.
- Synergy combos (freeze + shatter) reward coordination without requiring voice.

## Downed and revive

```text
on lethal damage: if revive_available: downed (bleedout timer)
teammate interact: revive progress -> restored at % health
bleedout: death -> respawn at checkpoint or spectate
```

- Bleedout 30–60 s; revive 3–5 s; both tunable by difficulty.
- Revive should be risky (channel, exposed), not free.
- Solo: self-revive item or checkpoint respawn instead.
- Prevent revive-camping by clearing enemies or granting brief invulnerability.

## Loot and progression

- **Instanced loot**: each player sees their own; no ninja-looting.
- **Shared loot**: tension and trade, but needs need/greed rules.
- **Shared progression**: quest credit for all participants in range.
- Cosmetic/account progression shared; power progression per player.
- Joining mid-mission: catch-up XP or synced level, not a fresh character.

## Communication

- Ping system: enemy, loot, objective, "come here", "help".
- Contextual callouts auto-generated ("player down") beat voice requirements.
- Screen-edge indicators for off-screen teammates.
- Subtitles/captions for all critical co-op audio (see `accessibility`).

## Drop-in/out

- Join anytime in non-competitive modes; host migration or server-held state.
- Leaving must not soft-lock an encounter: re-scale on player count change.
- Rejoin restores inventory and position within a grace window.
- Pause rules: solo pauses; co-op does not (or votes).

## Difficulty

- Scale to player count and to skill; offer difficulty modifiers.
- Avoid "more HP" as the only lever: add mechanics, timers, modifiers.
- Let players opt into harder scaling for better rewards, not required grind.
- Separate accessibility assists from difficulty.

## Pitfalls

- **HP sponge scaling** → fights drag. Scale damage/mechanics, not only health.
- **One player carries** → roles are cosmetic. Give each a unique lever.
- **Friendly fire frustration** → full FF with random matchmaking. Toggle or reduce.
- **Ninja looting** → shared loot without rules. Instance or add need/greed.
- **Revive trivializes death** → infinite revives. Limited charges/bleedout.
- **Late joiner useless** → no catch-up. Sync level or provide loaner gear.
- **Solo impossible** → co-op-only mechanics. Provide solo variant or label it.
- **Pause conflict** → one player pauses for all. Define host/vote rules.
- **Off-screen chaos** → no indicators. Add pings and edge markers.

## Composition

- **Netcode:** `multiplayer-netcode` for state and reconnect.
- **AI:** `game-ai` for enemies that target and split across players.
- **UI:** `ui-architecture` for party frames, pings, revive prompts.
- **Accessibility:** `accessibility` for captions and assists.
- **Quests:** `quest-design` for shared credit and co-op objectives.

## References

- Read `references/scaling-roles-and-revive.md` for scaling tables, revive math, loot rules and a
  co-op test matrix.
