---
name: auto-battler
description: >
  Design an auto-battler: shared unit pool, shop odds, economy and interest, synergies/traits,
  positioning, rounds and PvE, items, player damage, comeback and lobby pacing. Use for an
  autochess-style strategy game.
---

# Auto-battler

An auto-battler is a drafting game where the fight resolves itself. The player's skill is in
**economy, composition and positioning** under shared randomness. This is a **compositional**
skill: pair with `game-economy`, `game-ai` and `ui-architecture`.

## When to use

- Use when designing an autochess/auto-battler with a shared pool, shop and synergies.
- Use when lobbies snowball, rounds drag, or players cannot read why they lost.

**When *not* to use:** a card battler with manual plays → `card-game`; a tower-defense wave game →
`tower-defense`; a management sim → `management-sim`.

## Core loop

```text
income -> shop -> buy/reroll/level -> place -> fight -> damage -> repeat
```

- One meaningful decision per round; the fight is the feedback, not the input.
- Information is public: board, gold, level, streaks. Hidden info only for the next shop.
- The player should be able to explain the loss: composition, positioning or economy.

## Shared pool

```text
pool[cost][unit] = copies
shop rolls from pool; buying removes; selling returns
```

- Shared pool creates scarcity and scouting; disclose remaining copies or tiers.
- Pool size per cost tier controls contesting; too small feels random, too large feels flat.
- On elimination, return units to the pool (or not, if the design wants scarcity).
- Reroll odds by level must be visible in the UI.

## Economy

| Source | Amount | Notes |
|--------|--------|-------|
| Base income | 5/round | every round |
| Interest | +1 per 10 gold, max 5 | rewards saving |
| Win/loss streak | 1–3 | rewards stability |
| Combat win | +1 | small |
| Sell unit | cost | full refund for 1-star |

- Reroll costs 2; buying XP costs 4 (numbers are tuning examples).
- Interest creates the core tension: spend now or save for later.
- Catch-up: slight interest/income boost for bottom players, disclosed.

## Levels and odds

```text
level 1..9; XP to next; shop odds per cost tier
```

- Higher level = more units on board + better odds; it is the main power curve.
- Make the level-up decision compete with rerolls every round.
- Publish odds in a tooltip; hidden odds feel unfair.

## Synergies and traits

- Traits activate at 2/4/6 (or 3/6/9); each breakpoint changes the board, not only stats.
- Every unit has a primary trait and a secondary; avoid a trait with one viable unit.
- Contests: a trait should have 4–8 units across tiers so it can be drafted.
- Emblems/++ items can fake a trait; price them accordingly.
- Avoid "stat soup": traits should add verbs (shield, burn, summon, execute).

## Positioning

- Board is a grid; melee front, ranged back, assassins jump, AoE punishes clumps.
- Scouting the next opponent rewards repositioning; give enough time between rounds.
- Carousel/Shared draft is optional; it adds comeback and social pressure.
- Hidden opponent (ghost) rounds reduce unfair focus-fire; disclose.

## Combat and items

- Auto-combat: deterministic given seed, units, items and positions; replayable.
- Items combine (3 components → 1 completed); publish recipes.
- Cap item power; a single carry should not one-shot the board without counterplay.
- Player damage scales with surviving units and stage; avoid instant 20-damage spikes.
- PvE rounds give items/gold and a breather; do not make them a tax.

## Lobby and pacing

- 8 players (or 4/6) with elimination; ghost rounds fill odd counts.
- Round length: planning 20–30 s, combat 5–15 s; fast-forward for most fights.
- Match target 20–35 minutes; sudden-death at low HP.
- Bots for empty seats; label them and match their skill.
- Spectate after elimination; allow a fast exit.

## Fairness and clarity

- Seed the RNG; no hidden pity that only some players get.
- Same shop odds for everyone; same pool.
- Show combat results: damage breakdown, trait activation, item effects.
- Post-match: board history, economy graph, damage sources.
- Avoid monetized power; cosmetics only if monetized.

## Pitfalls

- **Snowball** → leader compounds. Add catch-up income, damage caps, carousel.
- **Reroll spam** → no decision. Price rerolls and reward saving.
- **Unreadable loss** → hidden math. Show traits, items and damage.
- **Dead traits** → too few units. Add units or merge traits.
- **Positioning irrelevant** → no assassins/AoE. Add threats that punish clumps.
- **Too-long rounds** → planning drag. Timer, presets, fast-forward.
- **Item overload** → spreadsheet. Limit components and combine clearly.
- **Pool feels random** → too few copies. Increase pool or show counts.
- **Instant elimination** → damage spike. Scale damage by stage.
- **Pay-to-win** → trust collapse. Sell cosmetics, not power.

## Composition

- **Economy:** `game-economy` for income, interest, sinks and inflation.
- **AI:** `game-ai` for bots and auto-combat resolution.
- **UI:** `ui-architecture` for shop, board, trait panel and damage recap.
- **Netcode:** `multiplayer-netcode` for lobbies and authoritative results.
- **Balance:** `game-balance` for unit/TTK and trait tuning.

## References

- Read `references/pool-economy-and-rounds.md` for economy tables, shop odds, trait matrix,
  round schedule and an auto-battler test checklist.
