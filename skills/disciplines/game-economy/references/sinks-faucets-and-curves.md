# Sinks, faucets and curves

Depth for `game-economy`: worksheets, curve math, pacing and validation.

## Worksheet

| Item | Formula | Target |
|------|---------|--------|
| Income/min (early) | kills/min × reward | 1× baseline |
| Cost of first upgrade | base | 5–15 min of income |
| Cost growth | `base * g^n` | g = 1.07–1.15 |
| Income growth | `i0 * h^n` | h < g, close to g |
| Time to afford(n) | `cost(n) / income(n)` | < 2× previous tier |
| Sink coverage | Σsinks / Σfaucets per hour | 0.8–1.1 early |

## Curve fitting

Given desired time-to-afford `T(n)` and income `I(n)`:

```text
cost(n) = T(n) * I(n)
```

- Choose the time curve first (e.g. 30 s → 2 min → 5 min), then derive costs.
- If you want exponential costs, exponential income keeps time flat; sub-exponential income makes
  time grow.
- Hand-tune the first 10 purchases; formula from there.

## Prestige math

```text
prestige_currency = floor(k * sqrt(total_earned / base))
multiplier        = 1 + prestige_currency * m
```

- First prestige should be reachable in 30–90 min for an idle game.
- Each cycle should be faster than the last; otherwise players repeat the same grind.
- Keep a permanent unlock track so a reset never feels like pure loss.

## Gacha / random rewards

```text
P(rare in n pulls) = 1 - (1 - p)^n
expected pulls     = 1 / p
pity               = hard pity at N, soft pity ramp after N-k
```

- Display odds; obey platform rules for paid random items.
- Pity must be visible in the UI, not hidden in code.
- Avoid duplicate-only pools; convert duplicates.

## Balance checklist

1. Plot time-to-afford for 30 min / 2 h / 10 h.
2. Compare hourly faucets vs sinks at each stage.
3. Check the cheapest and most expensive upgrades are both considered.
4. Simulate a casual (50 % efficiency) and optimal player.
5. Verify no single strategy dominates (one upgrade or one income source).
6. Check numbers stay readable (abbreviation thresholds).
7. Verify purchases are server-validated and idempotent.
8. Test save/load preserves balances exactly (no float drift).
9. Confirm shop prices and currency packs cannot leave dead remainders.
10. Re-run after any reward-rate change; economies drift with content.
