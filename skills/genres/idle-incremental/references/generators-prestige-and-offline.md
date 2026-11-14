# Generators, prestige and offline

Depth for `idle-incremental`: curve tables, prestige, offline and tests.

## Curve table (example)

| Tier | Cost | Income/s | Time to afford |
|------|------|----------|----------------|
| 1 | 10 | 1 | 10 s |
| 5 | 40 | 4 | 10 s |
| 10 | 160 | 12 | 13 s |
| 20 | 2,500 | 80 | 31 s |
| 30 | 40,000 | 600 | 67 s |
| 40 | 650,000 | 5,000 | 130 s |

- Time-to-afford should step up gradually, not explode.
- Insert milestone multipliers when the step exceeds ~2× the previous.

## Prestige math

```text
prestige_currency = floor(k * sqrt(total_earned / base))
multiplier        = 1 + prestige_currency * m
```

- Choose `k`, `base`, `m` so the first prestige doubles income.
- Each cycle: faster reach, higher multiplier; otherwise players repeat the same grind.
- Permanent unlocks: auto-buy, speed, cosmetics.

## Offline

```text
cap        = 8-24 h
efficiency = 0.5-1.0
gain       = rate * min(elapsed, cap) * efficiency
```

- `elapsed` from server time; clamp negatives after clock changes.
- If offline, queue the claim and show a summary on return.
- Competitive modes: validate on the server, not the client.

## Test checklist

1. First 5 minutes show visible growth.
2. No stall longer than ~2× the previous step before a new mechanic.
3. Prestige preview matches the granted multiplier.
4. Offline gain capped and correct after clock changes.
5. Numbers format correctly at 1e6/1e9/1e15/1e30.
6. Save/load preserves counts, multipliers and prestige state.
7. Update migration handles renamed generators.
8. Automation unlocks work after prestige.
9. Monetization does not gate the core loop.
10. Analytics show where players stall.
