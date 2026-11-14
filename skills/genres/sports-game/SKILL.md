---
name: sports-game
description: >
  Build a sports game: ball/puck physics, rules engine and officials, team AI roles and
  formations, match flow and clock, camera/broadcast presentation, replays, career modes and
  online match sync. Use for soccer/basketball/hockey-style games or sports minigames.
---

# Sports game

A sports game is a rules engine wrapped in a physics toy and a broadcast. The ball must behave,
the rules must be enforced consistently, and the presentation must make a pass readable. This is
a **compositional** skill: pair with `physics-tuning`, `game-ai`, `multiplayer-netcode`.

## When to use

- Use when building a sports title or a sports minigame with rules, teams and a match clock.
- Use when the ball feels wrong, AI teammates abandon positions, or the referee is inconsistent.

**When *not* to use:** arcade party sports with no rules → a party/action genre; racing →
`racing-game`; pure physics sandbox → `physics-tuning`.

## Layers

```text
input -> player controller -> ball interaction -> rules engine -> match state -> presentation
```

- Keep the rules engine separate from physics: it observes events, it does not live in the ball.
- Match state (score, clock, period, fouls) is the single source of truth.
- Presentation (commentary, replays, overlays) reads state; it never changes it.

## Ball physics

- Use a rigid body with continuous collision for fast shots.
- Tune restitution, friction, drag, spin; a ball that stops too fast feels dead.
- Magnus/spin is optional but sells curve; apply as a force based on angular velocity.
- Dribble: short impulses or a soft constraint, not parenting the ball to the foot.
- Goalkeeper/deflection: explicit collision response, not random.

## Rules engine

| Rule | Event | Resolution |
|------|-------|------------|
| Goal | ball crosses line fully | score, restart |
| Out of bounds | ball leaves pitch | throw-in/corner/goal kick |
| Foul | contact above threshold | free kick/card |
| Offside | pass + position at pass time | indirect free kick |
| Clock | period timer | stop/start per sport |

- Implement rules as explicit states and events; log every decision for debugging.
- Offside needs a snapshot of positions at the pass frame, not at reception.
- Officials: deterministic calls; optional VAR-like review for close calls.
- Test edge cases: ball on the line, simultaneous events, last-second shots.

## Team AI

| Role | Responsibility |
|------|----------------|
| Ball carrier | dribble, pass, shoot decision |
| Support | create passing lanes, overlap |
| Marker | track opponent, intercept |
| Cover | fill space behind |
| Keeper | positioning, shot-stopping |

- Formation as anchor positions + dynamic offsets; players return to shape.
- Decisions on a tick (e.g. 5–10 Hz), movement every frame.
- Pass evaluation: lane clear, receiver open, risk vs progress.
- Avoid all 10 players swarming the ball: role weights and spacing penalties.

## Match flow

```text
kickoff -> play -> goal/out -> restart -> halftime -> play -> full time
```

- Clock rules per sport (stopped vs running); handle added time.
- Substitutions, fatigue, injuries (optional).
- Difficulty via AI reaction time, pass error, keeper skill — not stat inflation alone.

## Camera and presentation

- Broadcast camera follows the ball with look-ahead and zoom; avoid nausea.
- Replay: record transforms at fixed rate, replay from a ring buffer, free camera.
- Commentary: event-driven lines, cooldowns, no repetition; localize.
- HUD: score, clock, period, cards, possession, minimap.

## Online

- Server-authoritative ball and score; clients predict their player.
- Input delay for shots/passes; validate possession and goals server-side.
- Desync-prone: physics. Use a deterministic or server-simulated ball; clients reconcile.
- Pause/timeout rules; reconnect restores match state.

## Career/franchise (optional)

- Season schedule, transfers, training, morale.
- Simulate matches statistically when not played; keep results consistent.
- Save schema versioned (`save-systems`).

## Pitfalls

- **Ball glued to feet** → no dribble physics. Use impulses and touch radius.
- **Referee inconsistency** → ad-hoc checks. Central rules engine + tests.
- **Offside wrong** → positions sampled at reception. Snapshot at pass.
- **Everyone chases the ball** → no role spacing. Formation anchors + penalties.
- **Clock wrong at period end** → frame-based timer. Use match state time.
- **Replay desync** → recording render state. Record simulation transforms.
- **Online goal disputes** → client-authoritative ball. Server validates.
- **Camera nausea** → too much look-ahead/zoom. Add smoothing and options.
- **Difficulty = stat boost** → AI cheats visibly. Tune reaction/error instead.

## Composition

- **Physics:** `physics-tuning` for ball/body tuning and CCD.
- **AI:** `game-ai`, `ai-behavior-trees-utility-ai` for roles and decisions.
- **Netcode:** `multiplayer-netcode` for authority and prediction.
- **Camera:** `camera-systems` for broadcast/replay cameras.
- **UI:** `game-ui-ux` for scoreboards and menus.
- **Save:** `save-systems` for career modes.

## References

- Read `references/ball-rules-and-team-ai.md` for physics constants, rule state tables, AI
  decision scoring and a sports test checklist.
