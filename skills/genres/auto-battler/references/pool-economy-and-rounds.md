# Pool, economy and rounds

Depth for `auto-battler`: numbers, schedule, tests.

## Economy table (starting point)

| Action | Cost | Effect |
|--------|------|--------|
| Reroll | 2 | new shop |
| Buy XP | 4 | +4 XP |
| Buy unit | 1–5 | from shop |
| Sell unit | cost | returns to pool |

- Base income 5; interest +1 per 10 gold (max 5); streak up to +3.
- Level 6 by round 5 is a common tempo target; tune to your match length.

## Shop odds (example)

| Level | 1-cost | 2-cost | 3-cost | 4-cost | 5-cost |
|-------|--------|--------|--------|--------|--------|
| 3 | 65 | 30 | 5 | 0 | 0 |
| 5 | 40 | 35 | 20 | 5 | 0 |
| 7 | 20 | 30 | 33 | 15 | 2 |
| 9 | 10 | 15 | 30 | 30 | 15 |

- Publish odds in the UI; adjust per patch.
- Pool copies: 1-cost 29, 2-cost 22, 3-cost 18, 4-cost 12, 5-cost 10 (typical).

## Trait matrix

| Trait | 2 | 4 | 6 | Units |
|-------|---|---|---|-------|
| Guardian | shield 150 | 300 | 500 | 6 |
| Ember | burn 2%/s | 4% | 7% | 5 |
| Ranger | +1 range | +2 | +3 | 6 |

- Each breakpoint changes behavior, not only a number.
- Ensure every trait has at least 4 units across tiers.

## Round schedule

| Stage | Rounds | Content |
|-------|--------|---------|
| 1 | 1–3 | PvE, starter units |
| 2 | 4–6 | first PvP, level 4–5 |
| 3 | 7–9 | items, level 6 |
| 4 | 10–12 | 4-cost units |
| 5+ | 13+ | 5-cost, elimination |

- Planning 20–30 s; combat 5–15 s; fast-forward after first death.
- Sudden death at low HP to bound match length.

## Test checklist

1. Shop odds match the published table.
2. Buying/selling moves units in/out of the shared pool.
3. Interest and streak cap correctly.
4. Catch-up mechanics are disclosed and bounded.
5. Combat is deterministic from seed/board/items.
6. Trait breakpoints change behavior and are visible.
7. Positioning matters: clumps are punished, backline is threatened.
8. Damage scales by stage; no instant elimination early.
9. Bots fill seats and are labeled.
10. Post-match recap explains damage and economy.
