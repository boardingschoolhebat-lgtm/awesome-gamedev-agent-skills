# TTK, counters and tuning

Depth for `game-balance`: formulas, worksheets, difficulty and tests.

## Formulas

```text
real_dps = damage * rate * accuracy * uptime
ehp      = hp / (1 - mitigation)
ttk      = ehp / real_dps
mitigation = armor / (armor + K)        # K sets the curve
```

- `uptime` includes reload, cooldown and time on target.
- For burst, compute the shortest lethal window separately.

## Tuning worksheet

| Weapon | Damage | Rate | DPS | Range | Accuracy | TTK vs 100 HP |
|--------|--------|------|-----|-------|----------|----------------|
| Rifle | 30 | 4/s | 120 | 40 m | 0.9 | 0.93 s |
| SMG | 18 | 5/s | 90 | 20 m | 0.85 | 1.31 s |
| Shotgun | 100 | 2/s | 200 | 8 m | 0.7 | 0.71 s |
| Sniper | 150 | 1/s | 150 | 80 m | 0.95 | 0.70 s |

- Add falloff so close-range weapons lose at distance.
- Price mobility/utility in the same budget.

## Counter matrix

| Attacker \ Defender | Light | Heavy | Air |
|---------------------|-------|-------|-----|
| Rifle | 1.0 | 0.8 | 0.6 |
| Rocket | 0.7 | 1.3 | 1.2 |
| AA | 0.5 | 0.6 | 1.5 |

- Multipliers 0.5–1.5 keep counters soft; 0 or 2+ creates hard counters.
- Every row needs a viable target; no useless option.

## Difficulty levers (in order)

1. Information (telegraphs, indicators).
2. Reaction time and accuracy.
3. Aggression and group size.
4. Resource pressure (ammo, healing).
5. Raw HP/damage (last resort).

## Balance checklist

1. Target TTK range defined per weapon class.
2. Real DPS includes accuracy and uptime.
3. Counters are soft and have counterplay.
4. No option dominates pick and win rate.
5. Difficulty changes pressure before stats.
6. Progression power is bounded per tier.
7. Changes are one variable at a time with notes.
8. Outliers checked per skill bracket.
9. Monetization does not sell power.
10. Players can see the key numbers.
