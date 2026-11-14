---
name: extraction-shooter
description: >
  Build an extraction shooter: stash and loadout, raid risk/reward, loot value and rarity,
  extraction points and timers, PvPvE AI, insurance, trader/quest progression, persistent stash
  and wipe seasons. Use for a raid-based looter shooter or extraction mode.
---

# Extraction shooter

An extraction shooter is a risk contract: bring gear into a raid, loot, and leave — or lose
everything. The genre's tension comes from **irreversible loss**, and its balance comes from
making the expected value of a raid worth the risk. This is a **compositional** skill: it builds
on `multiplayer-netcode`, `game-economy`, `quest-design` and a shooter genre.

## When to use

- Use when building raid-based PvPvE with extraction, stash, and gear loss.
- Use when tuning loot value, insurance, extraction timers, or wipe seasons.

**When *not* to use:** battle royale (no persistent stash) → `battle-royale`; survival crafting
with persistent bases → `survival-crafting`; pure PvP arena → `fps-shooter`.

## Core loop

```text
stash -> choose loadout -> raid (loot, fight, survive) -> extract -> stash/progression
                                    \-> die -> lose carried gear (keep secure items)
```

- The **decision to extract** is the core tension: more loot vs. more risk.
- Death must be costly but not run-ending; the stash is the comeback mechanic.
- A raid should have a story: where you went, what you risked, what you got.

## Must-have systems

1. **Stash** — persistent inventory with capacity, sorting, value.
2. **Loadout** — equipped gear, consumables, secure container.
3. **Raid instance** — spawns, loot containers, AI, other players, timer.
4. **Extraction** — fixed/conditional points, channel time, requirements.
5. **Loot** — value tiers, spawn tables, rare keys/quest items.
6. **Death/loss rules** — what drops, what is secured, insurance.
7. **Progression** — traders/quests, unlocks, hideout/stash upgrades.
8. **Economy** — vendor buy/sell prices, flea market or not, inflation control.
9. **Wipe/season** — optional reset cadence for freshness.

## Risk and reward

```text
expected_value(raid) = P(extract) * loot_value + (1 - P(extract)) * insured_return
risk(loadout)        = gear_value_lost_on_death
```

- Early raids should be profitable with cheap gear; high-tier gear raises both.
- Secure container: small, high-value-only slot that survives death; cap its power.
- Insurance returns gear only if no one extracted it; it is a soft safety net, not a refund.
- Avoid "gear fear" paralysis: cheap viable loadouts and scav/rat runs.

## Loot design

| Tier | Example | Use |
|------|---------|-----|
| Junk | scrap | vendor fodder, crafting |
| Common | ammo, meds | sustain |
| Rare | optics, armor | power spike |
| Key/quest | keys, intel | progression gates |
| Legendary | rare weapons | story moments |

- Value density: small items worth a lot create extraction tension.
- Loot spawns server-side; containers have per-raid RNG with a seeded table.
- Quest items must be findable deterministically enough (keys, guaranteed spawns).
- Flea market: player-driven prices need sinks and listing fees or they inflate.

## Patterns

### 1. Extraction point state machine

```text
Inactive -> Available(requirements met) -> Extracting(timer) -> Extracted
                     \-> Interrupted (left zone / damaged)
```

- Requirements: item, payment, time window, or "both players present".
- Show the timer and cancel on leaving; do not silently reset progress.
- Some points one-use per raid; broadcast or hide depending on design.

### 2. Death and loss resolution

```text
on_death(player):
    drop(equipped + backpack except secure_container)
    mark insurer-eligible items
    record killer, location, time
    player -> results screen (stash intact)
```

- Server decides drops; clients never report their own death inventory.
- Secure container contents persist; cap slots and disallow large gear.
- Team members can extract fallen gear only if rules allow (dog tag/loot).

### 3. AI (scavs/guards)

- Patrol routes, hearing/sight cones, investigate last known position.
- Gear and accuracy scale with area difficulty, not player level only.
- AI should be a threat and a loot source, not a wall.
- Server-authoritative AI for fairness in PvPvE.

### 4. Progression

- Traders: loyalty levels gated by rep + quests + spend.
- Quests: find/extract/survive/kill with specific gear (see `quest-design`).
- Hideout: passive income and stash upgrades; a sink for loot.
- Wipe: reset stash/levels but keep cosmetics; announce dates.

### 5. Economy

- Vendor prices anchor value; flea market floats around it.
- Sinks: listing fees, insurance premiums, hideout upgrades, ammo.
- Watch inflation: if top-tier gear is common, raids lose tension.
- Rewards for extraction, not only kills; support stealth/loot playstyles.

## Anti-cheat and fairness

- Server owns loot, damage, extraction and stash writes.
- Validate movement speed, fire rate, and line of sight.
- Radar/ESP is the classic cheat; minimize client knowledge of distant players.
- Log suspicious stash growth; audit trades.
- Never trust a client-reported extraction.

## Pitfalls

- **Gear fear** → only expensive loadouts viable. Add cheap meta and scav runs.
- **Death is meaningless** → insured everything. Limit insurance and secure slots.
- **Death is too punishing** → quit after one loss. Stash safety net and quick re-entry.
- **Loot inflation** → flea market flooded. Fees, durability, wipes.
- **Extraction camping** → one exit. Multiple exits with requirements.
- **Quest item unfindable** → pure RNG. Guaranteed spawns/keys.
- **Wipe backlash** → announce, preserve cosmetics, offer catch-up.
- **Client-authoritative stash** → duplication exploits. Server transactions + audit.
- **AI terminator** → aimbot scavs. Accuracy caps, reaction delay.
- **No reason to extract** → loot has no use. Progression sinks and quests.

## Composition

- **Netcode:** `multiplayer-netcode` for server authority and reconnect.
- **Economy:** `game-economy` for faucets/sinks, flea market, inflation.
- **Quests:** `quest-design` for trader tasks and progression.
- **Combat:** `fps-shooter` for gunplay and hit validation.
- **Save:** `save-systems` for stash/loadout versioning.
- **UI:** `ui-architecture` for inventory, stash, extraction map.

## References

- Read `references/raid-loop-loot-and-economy.md` for risk math, loot tables, extraction rules,
  progression pacing and a test checklist.
