# Encounter phases and metrics

Depth for `boss-design`: one-pager, moves, arena and tests.

## Boss one-pager

```text
Name:
Fantasy (one line):
Tests (one skill):
Arena (size/hazards):
Phases: 1) teach 2) combine 3) twist
Signature move:
Counterplay:
Checkpoint:
Reward:
Accessibility options:
```

## Move table

| Move | Range | Wind-up | Active | Recovery | Counter |
|------|-------|---------|--------|----------|---------|
| Slam | close | 0.6 s | 0.2 s | 0.8 s | dodge back, punish |
| Sweep | mid | 0.5 s | 0.3 s | 0.6 s | jump/roll through |
| Volley | far | 0.8 s | 0.4 s | 1.0 s | strafe, close gap |
| Charge | any | 0.7 s | 0.6 s | 1.2 s | sidestep, punish wall hit |
| AoE | arena | 1.0 s | 0.5 s | 0.9 s | leave the marked ring |

- Vary sequence and combination, not the tell timing.
- Every phase should add or remix moves, not just multiply numbers.

## Phase transitions

```text
hp <= 66% -> phase 2: clear projectiles, 1.5 s i-frames, roar, music layer, arena change
hp <= 33% -> phase 3: new rule (e.g. floor burns), shorter cycles
hp <= 0   -> defeat: slow-mo, camera, reward, no lingering damage
```

- Transition is a reward, not a free hit on the player.
- Never let a DoT or projectile kill during a cutscene.

## Arena checklist

1. Player can see the whole boss and the telegraphs.
2. Camera pulls back for large attacks; obstructions fade.
3. No corner without an escape; no pit without recovery.
4. Hazards use the same telegraph language as moves.
5. Entry and exit are readable; checkpoint is close.
6. Adds have capped counts and telegraphed spawns.

## Playtest metrics

- Attempts: median, p90; quit rate at the gate.
- Time per attempt and phase reached.
- Death causes: top 3 damage sources.
- Consumable usage; build diversity among winners.
- First confusion and first "aha" from observation.

## Checklist

1. One sentence states what the boss tests.
2. First phase is readable without prior knowledge.
3. Every move has a wind-up and a punish window.
4. Telegraphs use two channels and consistent timing.
5. Phase transitions clear danger and grant i-frames.
6. Adds are capped and cleared on transition.
7. Retry is fast; checkpoint is at the gate.
8. Accessibility assists exist and are disclosed.
9. Reward is specific and changes the world or build.
10. Metrics show most players reach phase 2 and learn from deaths.
