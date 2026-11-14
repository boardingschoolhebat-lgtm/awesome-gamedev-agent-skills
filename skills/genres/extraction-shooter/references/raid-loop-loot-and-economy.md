# Raid loop, loot and economy

Depth for `extraction-shooter`: risk math, loot tables, extraction and tests.

## Risk math

```text
EV = p_extract * (loot_value + survival_bonus) - (1 - p_extract) * gear_loss
gear_loss = loadout_value - insured_return - secure_value
```

- Target positive EV for a player with ~40–50 % extraction rate on a cheap loadout.
- High-tier loadouts should have lower EV unless skill compensates.
- Track actual extraction rates per map/tier and compare to design.

## Loot table

```text
container_type -> tier weights -> item table -> quantity
area_difficulty multiplies rare weight (1.0–1.8)
guaranteed: quest keys at fixed spawns, 1 med + ammo per container cluster
```

| Container | Slots | Rare weight |
|-----------|-------|-------------|
| Drawer | 1–2 | 0.5× |
| Safe | 2–4 | 1.5× |
| Med bag | 1–3 | 0.8× |
| Weapon crate | 1–2 | 1.8× |

## Extraction rules

```text
point: { id, zone, requires_item?, cost?, channel_time, one_use }
on_enter: if requirements: start_timer
on_exit:  cancel (progress lost or paused per design)
on_timer: extract(player)
```

- Channel 5–15 s creates tension; instant extraction removes it.
- Multiple exits; some conditional (item, payment, timer window).
- Show extraction status on the map only if discovered.

## Progression pacing

| Stage | Gear access | Goal |
|-------|-------------|------|
| 1–5 raids | cheap, vendor | learn maps, extract once |
| 6–20 | tier 2, first quests | trader loyalty 2 |
| 20–50 | tier 3, hideout | specialized builds |
| 50+ | rare, flea market | endgame goals, wipe prep |

- Gate power by quests + rep + spend, not only money.
- Each stage needs a clear next goal; otherwise players quit.

## Test checklist

1. Death drops the right items; secure container persists.
2. Insurance returns only unextracted items.
3. Extraction requires the item/payment and cancels on leaving.
4. Duplicate stash writes impossible (server transaction + idempotency).
5. Loot spawns match tables over 1,000 rolls.
6. Quest items have a reliable spawn path.
7. Flea market fees prevent trivial flipping.
8. AI accuracy caps and reaction delay hold.
9. Wipe resets stash/levels but keeps cosmetics.
10. Reconnect mid-raid restores position/inventory or fails safely.
