---
name: game-economy
description: >
  Design and balance a game economy: currencies, faucets and sinks, cost/reward curves,
  progression pacing, inflation control, reward schedules, and monetization ethics. Use for
  upgrade pricing, idle/incremental balance, shop design, or an economy that inflates or stalls.
---

# Game economy

An economy is a set of sources (faucets), drains (sinks), and converters between currencies.
Balance is the relationship between income rate and cost curve over time. This skill is
**compositional**: pair with `save-systems` for persistence and `multiplayer-netcode` for
server authority.

## When to use

- Use when pricing upgrades/items, tuning progression, or designing a shop/battle pass.
- Use when players stockpile currency, hit a wall, or trivialize the game.

**When *not* to use:** no persistent resources (pure arcade score) → scoring only; real-money
payments integration → store/platform docs plus this for design.

## Vocabulary

| Term | Meaning |
|------|---------|
| Faucet / source | anything that creates currency (kills, quests, idle income) |
| Sink / drain | anything that removes it (upgrades, repairs, fees, cosmetics) |
| Converter | exchange between currencies or time ↔ currency |
| Soft currency | earned, plentiful |
| Hard/premium | scarce, often purchased |
| Inflation | faucets outpace sinks; prices lose meaning |
| Deflation | sinks outpace faucets; progress stalls |

## Design targets

1. **Time-to-next**: how many minutes of play buy the next meaningful upgrade.
2. **Session shape**: earn → spend → feel stronger within one session.
3. **Long-run curve**: costs grow faster than income, but not so fast that progress stops.
4. **Sink coverage**: every faucet has somewhere to go; otherwise wealth accumulates.
5. **Choice**: at least two viable purchases at most decision points.

## Curves

```text
linear:       cost(n)   = base + step * n
exponential:  cost(n)   = base * growth^n          # typical growth 1.07–1.15
polynomial:   cost(n)   = base * n^1.5
income(n)     = base_income * income_growth^n      # usually slower than cost growth
```

- If `cost_growth > income_growth`, progress slows — that is the intended wall, but it must stay
  within session tolerance.
- Compute **time to afford**: `cost(n) / income(n)`; plot it. Flat-ish early, rising later.
- Prefer explicit tables over pure formulas for hand-tuned milestones.

### Example: upgrade ladder

```text
level  cost      income/s   time to afford
1      100       10         10 s
5      400       25         16 s
10     1,600     60         27 s
20     25,000    300        83 s
```

If time-to-afford grows without bound, add new income sources, not just bigger numbers.

## Faucet/sink table

| Source | Rate | Sink | Rate |
|--------|------|------|------|
| Enemy kills | 20/min | Upgrades | 300/level |
| Quest rewards | 500/quest | Repairs | 50/death |
| Idle income | 10/s offline | Cosmetics | 1,000 each |
| Daily bonus | 200/day | Respec | 500 |

- Sum per hour and compare; a healthy early game has sinks ≈ faucets.
- Late game needs larger sinks (prestige, housing, crafting) or the currency becomes noise.

## Reward schedules

- Fixed ratio (every N kills) is predictable; variable ratio is exciting but can feel manipulative.
- Pity systems: guarantee a rare after N failures; disclose odds where required.
- Duplicates: convert to shards/currency instead of dead rewards.
- Catch-up mechanics: reduced cost for older content, not free.

## Monetization ethics

- Sell cosmetics/time, not power, in competitive games.
- Disclose paid random item odds; follow platform policy (e.g. Roblox `PolicyService` for paid
  random items) and local law.
- No dark patterns: fake scarcity, countdown timers that reset, currency obfuscation.
- Premium currency packs should not leave unusable remainders by design.

## Telemetry

Track per session: currency earned by source, spent by sink, median balance, progression step,
first-purchase time, and quit points. Compare against the designed curve; fix the largest gap.

## Patterns

### 1. Simulation before tuning

```python
# Pseudocode: simulate a player who always buys the cheapest upgrade.
def simulate(minutes, income_fn, costs):
    gold, t, bought = 0, 0, 0
    while t < minutes:
        gold += income_fn(bought) * 1.0     # per minute
        if gold >= costs[bought]:
            gold -= costs[bought]; bought += 1
        t += 1
    return bought
```

- Run 10/60/600-minute horizons; check the curve is not a wall or a walk.
- Monte Carlo with different play rates (casual vs optimal).

### 2. Idle/offline earnings

```text
offline_gain = rate_per_second * min(offline_seconds, cap) * efficiency
```

- Cap offline time (8–24 h); efficiency 50–100 %.
- Never grant more than the active rate; idle is a catch-up, not the best strategy.

### 3. Prestige

- Reset progress for a permanent multiplier; requirement grows each cycle.
- Formula: `multiplier = 1 + sqrt(total_earned / base)`; tune so the first prestige is a clear win.
- Preserve cosmetics/unlocks; wipe only the run currency.

## Pitfalls

- **Faucet > sink** → inflation; prices become meaningless. Add sinks or cut rewards.
- **Exponential cost with linear income** → hard wall. Match growth rates or add income tiers.
- **Too many currencies** → cognitive load; 2–3 is usually enough.
- **Premium currency confusion** → unclear exchange rates; show the real-money equivalent.
- **Pay-to-win** → retention spike then churn; sell convenience/cosmetics.
- **Exploit-friendly client economy** → server owns balances and purchases.
- **No catch-up** → returning players bounce; add reduced costs or bonus events.
- **Rewards feel random** → no pity; bad-luck protection.
- **Numbers unreadable** → abbreviate consistently (K/M/B) and keep exact values in tooltips.

## Composition

- **Persistence:** `save-systems` for balances, purchases, versioning.
- **Security:** `multiplayer-netcode` (server authority), `roblox-datastores`.
- **UI:** `game-ui-ux` for shop readability, confirmations, currency display.
- **Genre bindings:** `roblox-simulator-economy` for idle/simulator formulas, `tower-defense` for
  wave income, `rpg` for loot and levels.

## References

- Read `references/sinks-faucets-and-curves.md` for the faucet/sink worksheet, curve fitting,
  time-to-afford math, prestige formulas and a balance test checklist.
