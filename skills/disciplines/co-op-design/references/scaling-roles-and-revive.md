# Scaling, roles and revive

Depth for `co-op-design`: tables, revive math, loot and tests.

## Scaling table (example)

| Players | Enemy HP | Enemy dmg | Adds | Loot |
|---------|----------|-----------|------|------|
| 1 | 1.00× | 1.00× | 0 | 1.0× |
| 2 | 1.60× | 1.25× | +1 | 2.0× instanced |
| 3 | 2.10× | 1.50× | +2 | 3.0× instanced |
| 4 | 2.50× | 1.75× | +3 | 4.0× instanced |

- HP sub-linear, damage low, mechanics additive.
- Re-tune per encounter; bosses need bespoke scaling.

## Revive math

```text
downed_time      = 45 s (easy 60, hard 30)
revive_channel   = 4 s
revive_health    = 40 % max
revive_charges   = 1 per player per encounter (or item-based)
```

- Revive under fire should require cover or a tank.
- Bleedout accelerates after the first failed revive (optional pressure).
- Solo: one self-revive per run or checkpoint respawn.

## Loot rules

```text
instanced:  personal drops, no conflict
shared:     need/greed/pass, loot master optional
proximity:  quest credit within radius; damage contribution threshold
```

- Quest credit: participation (damage/heal/objective) within a time window.
- Boss loot: personal chest or guaranteed token to avoid disputes.

## Test matrix

| Players | What to verify |
|---------|----------------|
| 1 | solo parity, no co-op-only gates |
| 2 | duo mechanics, scaling, revive |
| 3 | mid-count balance (most likely broken) |
| 4 | chaos readability, performance |
| join mid-run | catch-up, no soft-lock |
| leave mid-run | re-scale, no stuck encounter |
| disconnect/reconnect | inventory/position restored |

## Checklist

1. Every role has a solo-viable baseline.
2. Scaling tested at all counts, not just 1 and 4.
3. Downed/revive has counterplay and limits.
4. Loot rules are explicit and visible.
5. Quest credit shared for participants.
6. Pings cover enemy/loot/objective/help.
7. Off-screen teammates visible.
8. Co-op pause rules documented.
9. Late joiners can contribute immediately.
10. Performance holds at max players + effects.
