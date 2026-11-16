---
name: combat-design
description: >
  Design action combat: commitment and cancel windows, frame data, hitboxes, hit-stop, hitstun,
  poise, block/parry/dodge, lock-on, enemy tells, crowd control and combat feedback. Use when
  melee or action combat feels weightless, unfair or spammy.
---

# Combat design

Action combat is a conversation of commitments: every attack commits you, every enemy tell gives
you a response window, and every hit changes the state of both fighters. This is a
**compositional** skill: pair with `game-feel`, `game-ai` and `game-balance`.

## When to use

- Use when designing melee/action combat, enemy archetypes, parry/dodge or hit reactions.
- Use when combat feels weightless, input-mushy, spammy, or unfair.

**When *not* to use:** turn-based combat → `rpg`; shooter gunplay → `fps-shooter`;
2D versus frame data/rollback → `fighting-game`; pure numbers → `game-balance`.

## The commitment loop

```text
read tell -> choose response -> commit -> resolve -> recover -> reset
```

- Attacks have startup, active and recovery; recovery is where skill is expressed.
- The player must be able to cancel *some* windows (e.g. recovery into dodge), not all.
- Inputs buffer briefly (100–200 ms) so actions feel responsive without masking spam.
- Every action has a cost: time, stamina, position or resource.

## Frame data

| Attack | Startup | Active | Recovery | Cancel |
|--------|---------|--------|----------|--------|
| Light 1 | 8 f | 3 f | 10 f | light 2, dodge |
| Light 2 | 10 f | 3 f | 14 f | heavy, dodge |
| Heavy | 20 f | 5 f | 24 f | none |
| Parry | 5 f | 8 f | 18 f | — |

- Values are examples at 60 fps; pick a baseline and stay consistent.
- Faster weapons trade damage/range for safety; slower weapons need poise or range.
- Recovery must be long enough to be punishable, short enough to feel responsive.

## Hitboxes and hurtboxes

- Separate the damage volume from the visual; debug-draw both.
- Hitboxes active only during the active frames; disable on hit to avoid double hits.
- Hurtboxes follow animation; do not use one capsule for a sprawling boss.
- Multi-hit attacks need a per-target hit cooldown.
- Test verticality and slopes; 3D combat needs depth-aware hit volumes.

## Hit reactions

```text
hit -> hit-stop (2–8 f) -> hitstun -> knockback -> recovery
```

- Hit-stop sells impact; scale it by damage, cap it for multi-hits.
- Hitstun must be shorter than the attacker's recovery or combos become infinite.
- Poise/armor: heavy enemies resist stagger; show when an attack is armored.
- Knockback direction and wall splats add readable outcomes.
- Damage numbers optional; use them for builds, not for every tick.

## Defense

- **Dodge:** i-frames on startup/middle, recovery vulnerable; cost stamina or cooldown.
- **Block:** chip damage, guard break, directional guards if the game supports them.
- **Parry:** tight window, high reward, whiff punish; never the only viable defense.
- **Positioning:** the best defense; spacing and backsteps should matter.
- Every defense needs a counter-enemy: grab beats block, anti-air beats jump, etc.

## Enemy design

- Archetypes: fodder, shield, ranged, charger, flyer, elite, boss.
- Each enemy has one clear tell and one clear punish window.
- Attack tokens: only 1–2 enemies attack at once; others circle and reposition.
- Ranged enemies force movement; melee enemies force timing.
- Elite variants remix a rule (shielded, explosive, summoner) instead of adding HP.

## Lock-on and camera

- Lock-on optional; soft-target the input direction when off.
- Target switching must be predictable; never snap to off-screen enemies.
- Camera pulls back for crowds and large enemies; fade obstructions.
- In 2D, keep both fighters in frame; avoid camera shake that hides tells.

## Feedback

- Hit-stop, flash, sound layer, particles and controller rumble together.
- Distinguish block (clang, sparks), parry (bright flash, slow-mo), and hit (impact).
- Enemy death is readable: stagger, dissolve, loot pop.
- The player's health and stamina must be visible without leaving the fight.

## Balance and metrics

- TTK targets per enemy tier; see `game-balance` for math.
- Track: damage taken by source, dodge/parry usage, death location, combo length.
- If one attack dominates, raise its commitment or lower its reward.
- If players never parry, the window or the payoff is wrong.

## Pitfalls

- **Weightless hits** → no hit-stop, no reaction, same sound. Add layered feedback.
- **Input mush** → long buffers or no cancel windows. Buffer ~150 ms, allow cancel.
- **Spam wins** → fastest attack has no recovery. Add commitment and stamina.
- **Unfair hits** → off-screen or instant attacks. Telegraph and keep enemies visible.
- **Infinite combos** → hitstun ≥ recovery. Shorten stun or add combo scaling.
- **Parry mandatory** → one correct answer. Offer dodge/block alternatives.
- **Crowd chaos** → everyone attacks at once. Use attack tokens.
- **Armored sponges** → no feedback. Show armor and stagger thresholds.
- **Camera betrayal** → shake/zoom hides tells. Tone down and test.
- **Stats hide feel** → tuning numbers without frame data. Fix timing first.

## Composition

- **Feel:** `game-feel` for hit-stop, shake and easing.
- **AI:** `game-ai` for attack selection, tokens and spacing.
- **Balance:** `game-balance` for TTK, damage and scaling.
- **Animation:** `animation-systems` for cancel windows and event markers.
- **Bosses:** `boss-design` for encounter-level structure.
- **Genres:** `fps-shooter`, `fighting-game`, `soulslike`-style action, `metroidvania`.

## References

- Read `references/frame-data-and-feel.md` for frame tables, hit-reaction recipes, enemy
  archetypes, debug overlays and a combat test checklist.
