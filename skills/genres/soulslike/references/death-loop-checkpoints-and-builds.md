# Death loop, checkpoints and builds

Depth for `soulslike`: loop, costs, builds, tests.

## Loop diagram

```text
[checkpoint] --explore--> [enemies] --currency--> [level up]
     ^                         |                        |
     |                         v                        |
     +------ die <---- [death drop] <---- die <----------+
                                |
                          recover once
```

- The drop is a place on the map; mark it and make it reachable.
- A second death before recovery loses the drop; state this clearly in the UI.

## Checkpoint table

| Function | Effect | Frequency |
|----------|--------|-----------|
| Respawn | reset enemies, refill flasks | every checkpoint |
| Level up | spend currency | every checkpoint |
| Fast travel | optional | hubs only |
| Shortcut | opens a loop | after major areas |
| Boss gate | retry point | before arena |

## Currency loss rules

```text
on death: drop = carried_currency; carried_currency = 0
on recovery: carried_currency += drop; drop = 0
on second death: drop = 0
```

- Keep key items, equipment and progress.
- Show the drop's location and value in the HUD/map.
- Optional ring of sacrifice: protects one drop, consumed on use.

## Build math (starting point)

```text
soft caps: vigor 40, endurance 30, primary damage stat 50
weapon upgrade: +10 % damage per level, capped at +10
equip load: <30 % fast, 30–70 % mid, >70 % heavy
```

- A build should reach its identity by ~1/3 of the game.
- Respec item: 3–5 per run, available after the second boss.

## Test checklist

1. Death drops currency at the exact death spot and respawns enemies.
2. Recovering the drop works; a second death clears it.
3. Checkpoint refills flasks and respawns enemies, not bosses.
4. Shortcut reduces the runback to under ~90 seconds.
5. Every attack has a punish window; stamina gates spam.
6. Healing has a commitment cost and is limited.
7. Boss checkpoint is at the gate; retry needs no consumable.
8. Builds come online in the first third; respec exists.
9. Accessibility options are available without disabling achievements (if any).
10. Players can name what killed them after a death.
