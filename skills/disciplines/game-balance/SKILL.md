---
name: game-balance
description: >
  Balance combat and progression: time-to-kill, DPS and effective health, damage/armor curves,
  counters and matchups, difficulty tuning, power budgets and data-driven iteration. Use for
  weapon/unit balance, TTK tuning, or a meta with one dominant strategy.
---

# Game balance

Balance is not equal numbers; it is meaningful choices. You tune **time-to-kill, effective
health, counters and costs** so several strategies remain viable. This is a **compositional**
skill: pair with `game-economy` for costs and `analytics` for live data.

## When to use

- Use when tuning weapons, units, abilities, enemies, or progression power.
- Use when one strategy dominates, fights feel too fast/slow, or difficulty spikes.

**When *not* to use:** economy-only inflation → `game-economy`; AI behavior → `game-ai`;
matchmaking fairness → `matchmaking`; puzzle difficulty → `puzzle` design.

## Core quantities

```text
DPS          = damage * attacks_per_second
effective HP = HP / (1 - mitigation)          # or HP * armor_factor
TTK          = effective HP / DPS
power        = offense * defense * mobility * utility   (rough budget)
```

- Compare TTK across tiers, not raw damage.
- Burst vs sustain: same DPS can feel different; track burst window and reload.
- Include accuracy/reload/uptime in real DPS, not theoretical.

## Damage and armor

- Flat reduction favors many small hits; percentage favors big hits. Pick deliberately.
- Diminishing returns on armor prevent immortality: `mitigation = armor / (armor + K)`.
- Damage types vs armor types create counters; keep the matrix small (3–5 types).
- Show numbers the player can reason about; hidden formulas breed superstition.

## Counters and matchups

```text
A beats B (70/30), B beats C, C beats A   # rock-paper-scissors with skill room
```

- Counters should be soft (advantage, not immunity) unless the genre demands hard counters.
- Every unit/weapon needs a role, a counter and a counterplay.
- Avoid strict dominance: if A is better at everything, it is not a choice.
- Mobility and range are power; price them in the budget.

## Difficulty

- Tune enemy reaction time, accuracy, aggression and information — then stats.
- Damage and health scaling is the bluntest lever; use it last.
- Difficulty options should change pressure, not invalidate mechanics.
- Check the first 10 minutes: new players need early wins and clear failure feedback.

## Progression power

- Vertical power should be bounded per tier; horizontal options add choice.
- Cost curves price power (see `game-economy`); time-to-unlock is part of balance.
- Avoid pay-for-power; if monetized, disclose and cap.
- Respec/refund reduces the cost of experimenting, which improves balance data.

## Process

```text
1. Define the target experience (TTK range, fight length, build diversity).
2. Instrument: damage sources, deaths, win rates, pick rates.
3. Find outliers, not averages.
4. Change one variable per iteration; record it.
5. Re-measure with enough sample size.
6. Ship small, frequent changes with notes.
```

- Use a spreadsheet or a small simulator for closed-form checks before playtests.
- Keep a changelog with the reason and the measured effect.
- Balance for the median player, not only the top 1 %.

## Patterns

### 1. TTK table

```text
weapon      dps    target_hp   ttk_s
rifle       120    100         0.83
smg         90     100         1.11
shotgun     200*   100         0.50 (close range only)
sniper      150    100         0.67 (headshot 0.33)
```

- Add range falloff and accuracy so paper TTK matches practical TTK.

### 2. Power budget

```text
budget = 100
costs: damage 40, range 20, mobility 20, utility 20
```

- Every option spends the same budget; trade-offs become visible.

### 3. Win-rate sanity

- 45–55 % is healthy for asymmetric factions; 60 %+ needs a look.
- Low pick rate + high win rate = niche or slept-on; high pick + low win = popular but weak.
- Segment by skill bracket before nerfing.

## Pitfalls

- **One dominant strategy** → no counterplay. Add soft counters and raise its cost.
- **TTK too low** → fights decided by who saw first. Raise HP or lower burst.
- **TTK too high** → sponges. Lower HP or add weak points.
- **Armor immortality** → linear mitigation. Use diminishing returns and caps.
- **Buff/nerf whiplash** → large swings. Change one variable, small steps.
- **Balancing by average** → outliers hidden. Look at distributions and brackets.
- **Ignoring uptime** → theoretical DPS lies. Measure real combat.
- **Power creep** → each new tier invalidates old. Keep a power budget.
- **Hidden formulas** → players optimize rumors. Surface key numbers.

## Composition

- **Economy:** `game-economy` for costs, sinks and progression pacing.
- **Analytics:** `analytics` for pick/win rates and funnels.
- **Genres:** `fighting-game`, `fps-shooter`, `rts-game`, `mmorpg`, `tower-defense`.
- **AI:** `game-ai` for enemy difficulty knobs.
- **Playtest:** `playtest-qa` for measured iteration.

## References

- Read `references/ttk-counters-and-tuning.md` for formulas, a tuning worksheet, difficulty
  levers and a balance test checklist.
