# Zone, loot and match flow

Depth for `battle-royale`: timing tables, loot math, placement and tests.

## Zone timing (20-minute match example)

| Phase | Wait (s) | Shrink (s) | End radius (% map) | DPS |
|-------|----------|------------|--------------------|-----|
| 1 | 90 | 60 | 60 | 1 |
| 2 | 70 | 50 | 40 | 2 |
| 3 | 60 | 40 | 25 | 4 |
| 4 | 45 | 35 | 14 | 7 |
| 5 | 30 | 30 | 7 | 10 |
| 6 | 20 | 25 | 3 | 15 |
| 7 | 15 | 20 | 1 | 20 |

- Total ≈ 20 min including lobby/final.
- Shrink speed = `(r_start - r_end) / shrink_time`; check it against base run speed.
- Next center: sample inside current circle, bias toward POIs and away from the edge.

## Loot weights

```text
roll = rng.next()
cumulative weights -> tier
tier -> item table -> item
```

- Area multiplier: hot zone 1.5× rare weight, outskirts 0.7×.
- Guarantee: first container in a landing area contains a weapon.
- Ammo/consumables independent of weapon tier.
- Cap legendary per match; airdrops are contested sources.

## Placement rules

```text
solo: placement = players_alive_at_death
team: placement = teams_alive_when_last_member_dies
winner: last team/player alive
tie: same tick -> shared placement
```

- Record elimination order server-side for results and replays.
- Kills credited to the damage owner within a timeout window.

## Match state

```text
phase, phase_end_time, circle(center, radius), next_circle
alive_players[], alive_teams[], placements{}
loot_spawned, airdrops[]
```

- Serialize per-player view; never send the whole match to every client.
- Reconnect: restore player entity + placement + inventory.

## Test checklist

1. Full match runs start to victory without stuck phases.
2. Zone damage matches the phase table; outside players take ticks.
3. Next circle is inside the current circle and reachable.
4. Worst-case rotation is survivable at base speed.
5. Loot rolls are server-side and respect weights.
6. Landing guarantee gives a weapon.
7. Placement correct for solos and teams, including simultaneous deaths.
8. Disconnect/reconnect restores the match.
9. Spectate follows killer/teammates without ghosting.
10. 100-player load: tick budget, bandwidth, and frame time hold.
