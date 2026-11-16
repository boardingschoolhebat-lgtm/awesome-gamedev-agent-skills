---
name: soulslike
description: >
  Design a soulslike: stamina and commitment combat, checkpoints and enemy respawn, currency loss
  and recovery, interconnected shortcuts, boss gates, build variety, difficulty and accessibility.
  Use for a punishing action-RPG with a death loop.
---

# Soulslike

A soulslike turns death into a lesson and a cost. The loop is: commit, learn the pattern, spend
the currency, unlock a shortcut, try again. This is a **compositional** skill: pair with
`combat-design`, `boss-design` and `level-design`.

## When to use

- Use for a punishing action-RPG with stamina, checkpoints, respawning enemies and currency loss.
- Use when the death loop feels punishing without teaching, or runbacks are unbearable.

**When *not* to use:** pure action without loss → `combat-design`; metroidvania without the
currency loop → `metroidvania`; turn-based RPG → `rpg`.

## Core loop

```text
explore -> fight -> spend/level -> checkpoint -> die -> recover -> shortcut -> boss
```

- Death must teach: the player can name what killed them.
- The runback is part of the cost; keep it short once the lesson is learned.
- Shortcuts convert a long runback into a loop, which feels like progress.

## Combat

- Stamina gates attack, dodge, block and sprint; regeneration pauses while acting.
- Every attack commits; recovery is punishable. See `combat-design` for frame data.
- Defense triangle: dodge (i-frames), block (chip/guard break), parry (timing).
- Healing is a commitment: a long animation, limited flask count, refill at checkpoints.
- Poise/armor lets some attacks land through hits; show when it triggers.

## Death and currency

```text
die -> drop all currency at the death spot -> respawn at checkpoint
    -> enemies respawn -> reach the drop to recover
    -> die again before recovering -> drop is lost
```

- One recoverable drop; a second death overwrites it.
- Currency doubles as XP; spending it is a risk decision.
- Optional: a consumable that protects the drop, limited and expensive.
- Never delete equipment or key items on death.

## Checkpoints

- Checkpoint functions: respawn, refill healing, level up, fast travel (optional), reset world.
- Place before a boss and after a major shortcut; not so dense that tension disappears.
- Enemies respawn on rest; bosses do not (unless the design says otherwise).
- A checkpoint should be a readable landmark with a distinct sound/light.

## World and shortcuts

- Interconnected regions with one-way doors that open a shortcut back.
- Vertical loops: elevator, ladder, locked door from the far side.
- Optional areas hide upgrades, not critical keys.
- Map or mental model: landmarks, region palettes, visible gates.
- Runback target: under 60–90 seconds once the shortcut is open.

## Bosses and gates

- Bosses test the current lesson; see `boss-design` for phases and telegraphs.
- Checkpoint at the fog gate; no consumable tax to retry.
- Optional bosses give unique rewards; critical bosses gate regions.
- After a boss, open a shortcut or checkpoint so the trip back is short.

## Builds

- Stats with soft caps; a build should come online within the first third.
- Weapons differ by moveset, not only damage; upgrade materials are finite but respec exists.
- Armor weight affects mobility; show the breakpoint.
- Avoid one stat dominating every build; price stamina/health carefully.
- Respec should be available mid-game, costly but not prohibitive.

## Difficulty and accessibility

- Difficulty comes from patterns, pressure and cost — not hidden stats.
- Optional summons/assists; disclose them and their effect.
- Accessibility: remapping, camera speed, subtitle size, damage taken, telegraph speed,
  pause (if the design permits), and colorblind-safe tells.
- Do not gate the ending behind a no-hit run.

## Pitfalls

- **Runback too long** → players quit. Shortcut or checkpoint at the gate.
- **Death without a lesson** → unfair. Telegraph, and surface the damage source.
- **Currency loss feels empty** → no recovery decision. Make the drop visible and reachable.
- **Stamina trivial** → spam. Tie actions to stamina and pause regen.
- **Healing spam** → no commitment. Long animation, limited flasks.
- **Boss one-shots** → no learning. Add wind-up and partial mitigation.
- **Shortcut trivializes the level** → no tension. Keep some one-way pressure.
- **Build trap** → respec unavailable. Offer it mid-game.
- **Enemy respawn grind** → forced farming. Tune drops and level costs.
- **No accessibility** → excluded players. Add assists without changing the core.

## Composition

- **Combat:** `combat-design` for frame data, hit reactions, defense.
- **Bosses:** `boss-design` for phases, tells, arenas.
- **Levels:** `level-design` for loops, shortcuts and checkpoints.
- **Economy:** `game-economy` for currency, upgrade costs and sinks.
- **UI:** `game-ui-ux` for stamina, flasks, equip load and death screen.

## References

- Read `references/death-loop-checkpoints-and-builds.md` for a loop diagram, checkpoint table,
  currency-loss rules, build math and a soulslike checklist.
