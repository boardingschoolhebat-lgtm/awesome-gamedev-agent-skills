---
name: idle-incremental
description: >
  Build an idle/incremental game: generators and multipliers, cost/reward curves, offline
  earnings, prestige loops, automation, big-number formatting and save integrity. Use for an idle,
  clicker, tycoon or incremental game.
---

# Idle / incremental

An incremental game is a curve you can feel: numbers grow, costs grow faster, and prestige
resets the curve with a permanent multiplier. The design is mostly math plus respect for the
player's time. This is a **compositional** skill: pair with `game-economy` for sinks and
`save-systems` for persistence.

## When to use

- Use when building an idle/clicker/tycoon/incremental game, or tuning its pacing.
- Use when offline earnings are exploitable or progress stalls.

**When *not* to use:** a simulator with active gameplay → `roblox-simulator-economy` or the
relevant genre; a management game with real-time pressure → `rts`/tycoon systems.

## Core loop

```text
earn -> buy generator/upgrade -> earn faster -> unlock multiplier -> prestige -> repeat faster
```

- The first 5 minutes must show visible growth.
- Each purchase should change the rate, not just the number.
- Prestige is the answer to "the curve is slowing"; make it a choice with a clear payoff.

## Generators and multipliers

```text
income = Σ (generator.count * generator.base_rate * generator.multiplier)
       * global_multiplier * prestige_multiplier * boost
```

- Additive generators (more of the same) early; multiplicative upgrades later.
- Keep multipliers few and legible; stacking 12 hidden bonuses makes balance opaque.
- Show "per second" and "time to afford" everywhere.

## Curves

```text
cost(n)   = base * growth^n        # growth 1.07–1.15 typical
income(n) = i0 * h^n               # h slightly below growth
time(n)   = cost(n) / income(n)
```

- Early: seconds to afford; mid: minutes; late: hours or prestige.
- If time-to-afford grows without a new mechanic, the game is stalling.
- Milestones (x2 at 25/50/100) create visible jumps without new systems.

## Offline earnings

```text
offline_seconds = clamp(now - last_seen, 0, cap)
offline_gain    = rate_per_second * offline_seconds * efficiency
```

- Cap 8–24 h; efficiency 50–100 %; never exceed the active rate.
- Use **server time** for anything competitive; client clocks are cheatable.
- Show a "welcome back" summary with the earned amount; let players claim it.
- Handle timezone/DST and clock changes defensively.

## Prestige

```text
prestige_currency = floor(k * sqrt(total_earned / base))
multiplier        = 1 + prestige_currency * m
```

- First prestige reachable in 30–90 min; each cycle faster than the last.
- Keep permanent unlocks (automation, cosmetics) so a reset is not pure loss.
- Require confirmation and preview the multiplier gain.

## Automation and active play

- Auto-buyers, auto-clickers and managers are rewards, not starting features.
- Active play should be a multiplier or a skill check, not the only way to progress.
- Respect idle players: no mechanic that punishes being away.
- Optional minigames for boosts; never mandatory.

## Big numbers

- Use `decimal`/big-number libraries, not floats, past ~1e15.
- Format with suffixes (K, M, B, T, Qa, Qi…) and keep exact values in tooltips.
- Avoid scientific notation unless the theme wants it.
- Test formatting at 1e6, 1e9, 1e15, 1e30.

## Save integrity

- Save `last_seen` server-side or signed; validate offline gains server-side if competitive.
- Version saves; migrate generator ids.
- Anti-cheat: cap offline gain, detect impossible rates, but do not punish legitimate idle.
- Backup/export for players; cloud saves where possible.

## Monetization ethics

- Sell convenience/cosmetics, not mandatory power; disclose odds.
- No paywalled offline earnings that make the base loop feel broken.
- Ads optional and rewarded, never interrupting idle progress.
- Respect platform policies for paid random items.

## Pitfalls

- **Curve wall** → time-to-afford explodes. Add prestige or income tier.
- **Numbers unreadable** → float precision and long digits. Big-number library + suffixes.
- **Offline exploit** → client clock. Server time and caps.
- **Prestige feels like loss** → no permanent carryover. Keep automation/cosmetics.
- **Too many currencies** → opacity. 2–3 max.
- **Idle punished** → active-only boosts. Let idle be viable.
- **Save corruption on update** → no migration. Version and migrate.
- **Pay-to-win** → mandatory purchases. Sell time, not power.
- **No feedback** → numbers change silently. Animate gains and milestones.

## Composition

- **Economy:** `game-economy` for sinks/faucets and inflation.
- **Save:** `save-systems` for offline time and migration.
- **UI:** `game-ui-ux` for readable numbers and generators.
- **Analytics:** `analytics` for progression funnels and stall points.
- **Roblox:** `roblox-simulator-economy` for platform-specific formulas.

## References

- Read `references/generators-prestige-and-offline.md` for curve tables, prestige math, offline
  caps and an incremental test checklist.
