---
name: boss-design
description: >
  Design boss encounters: purpose and fantasy, phase structure, telegraphed movesets, arena and
  camera, adds and hazards, checkpoints, difficulty and accessibility, rewards and playtest
  metrics. Use when building or fixing a boss fight.
---

# Boss design

A boss is a exam the player studies through failure: a compact set of rules, a readable tells,
and a climax that tests what the level taught. This is a **compositional** skill: pair with
`game-ai`, `game-balance` and `level-design`.

## When to use

- Use when designing a boss, mini-boss, elite or set-piece encounter.
- Use when a fight feels unfair, chaotic, too long, or players quit at the gate.

**When *not* to use:** regular enemy stats → `game-balance`; AI implementation → `game-ai`;
boss music/audio → `audio-design`; arena layout → `level-design`.

## Purpose

```text
teach -> test -> twist -> conclude
```

- Decide the one thing the boss tests (positioning, timing, resource, pattern reading).
- The fantasy matters: what does the player feel — dread, triumph, David vs Goliath?
- The arena and the moveset should express that fantasy.
- A boss is a narrative beat too: entrance, escalation, defeat.

## Phase structure

| Phase | Job | Duration |
|-------|-----|----------|
| Intro | establish scale and rules | 5–10 s |
| 1 | teach the moveset | 25–35 % |
| 2 | combine and pressure | 30–40 % |
| 3 | twist / desperation | 20–30 % |
| Defeat | payoff, no cheap death | 3–5 s |

- 2–3 phases is enough; more repeats rather than deepens.
- On transition: clear projectiles, grant i-frames, change music/arena, then resume.
- Health bar shows phase pips; never hide the current phase.

## Moveset

- 4–7 distinct moves, each with a clear purpose: poke, punish, zone, gap-close, AoE.
- Every move needs a wind-up, an active window and a recovery the player can punish.
- Telegraphs use at least two channels: animation + color/sound/ground decal.
- Keep telegraph timings consistent per move; vary the sequence, not the tell.
- Limit unblockable/unavoidable damage; if unavoidable, make it chip and telegraphed.
- Add one signature move players will remember and learn to bait.

## Arena

- Size for the intended dodge distance; too small turns into a corner trap.
- Cover and hazards must not block the camera or create safe cheese spots.
- No pits/ledges without a recovery; no softlock corners.
- Entrance and exit are readable; the player can see the boss at all times.
- Camera pulls back for large bosses; lock-on optional but never mandatory.

## Adds and hazards

- Adds should pressure, not replace the boss; cap their count.
- Add spawn points are telegraphed and reachable.
- Environmental hazards follow the same telegraph rules.
- Clear adds on phase transition to avoid overwhelming resets.

## Difficulty and recovery

- Checkpoint before the arena; retry is fast (≤10 s to re-enter).
- Consumables and builds should matter; do not hard-gate a single strategy.
- Accessibility: damage taken, telegraph speed, aim assist, pause, and optional assists.
- Optional summons/NPC help should be disclosed, not hidden.
- First-time players need a readable first phase; veterans get the later twist.

## Rewards

- Reward matches effort: unique gear, ability, lore, access.
- Do not lock the critical path behind an optional super-boss unless the story earns it.
- Post-fight state changes: arena, NPC dialogue, world.

## Metrics

```text
attempts to first kill (median and p90)
time per attempt
phase reached per attempt
damage sources on death
healing/bombs used
quit rate at the boss
```

- A boss that kills 90 % of players in phase 1 is a readability problem, not a skill problem.
- Watch 5 players: note the first confusion and the first "aha".

## Pitfalls

- **Unreadable one-shot** → no telegraph or instant damage. Add wind-up and counterplay.
- **Damage sponge** → long fight with no new decisions. Cut HP, add phases/moves.
- **Adds overwhelm** → boss becomes background. Cap adds, clear on transition.
- **Camera betrayal** → boss off-screen or behind geometry. Pull back, fade obstructions.
- **Corner softlock** → no escape from arena edge. Widen or add escape move.
- **Fake difficulty** → input reading or unavoidable hits. Telegraph and allow reaction.
- **Checkpoint too far** → retry fatigue. Spawn at the gate.
- **Phase repetition** → same moves faster. Change the rule, not only the speed.
- **No accessibility** → excluded players. Offer assists and remapping.
- **Reward mismatch** → anticlimactic loot. Make the payoff specific.

## Composition

- **AI:** `game-ai` for state machines, attack selection and steering.
- **Balance:** `game-balance` for HP, damage and TTK targets.
- **Levels:** `level-design` for arena flow and hazards.
- **Audio:** `audio-design` for tells, phase music and impact.
- **UI:** `game-ui-ux` for health bars, phase pips and lock-on.

## References

- Read `references/encounter-phases-and-metrics.md` for a boss one-pager, phase/move tables,
  telegraph timings, arena checklist and playtest metrics.
