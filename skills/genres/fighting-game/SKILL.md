---
name: fighting-game
description: >
  Build a fighting game: fixed-tick simulation, frame data (startup/active/recovery), hitboxes
  and hurtboxes, input buffering and motion inputs, hitstun/blockstun, cancels and combos, rounds,
  and rollback-friendly netcode. Use for a 2D/3D fighter or a combat system with frame data.
---

# Fighting game

A fighting game is a deterministic, fixed-tick state machine: two fighters, frame data, hitboxes,
and input buffering. Fairness depends on the simulation running at a fixed rate and on hit
resolution being identical on both machines. This is a **compositional** skill: it uses
`input-systems`, `game-feel` and `game-ui-ux`.

## When to use

- Use when building a 1v1 fighter or a combat system with startup/active/recovery frames.
- Use when combos drop, inputs eat each other, or online matches desync.

**When *not* to use:** beat-'em-up crowds or action combat → `game-feel` + `game-ai`; shooter
gunplay → `fps-shooter`; turn-based combat → `rpg`.

## Core loop

**Neutral (move, poke, whiff-punish) → hit/block → advantage → combo or pressure → knockdown →
reset to neutral → rounds until a fighter wins.**

## Must-have systems

1. **Fixed tick** — 60 Hz simulation, decoupled from rendering.
2. **State machine** — idle, walk, dash, jump, attack, block, hitstun, blockstun, knockdown, wakeup.
3. **Frame data** — startup, active, recovery, damage, hitstun, blockstun, cancel windows.
4. **Hit/hurtboxes** — per-frame boxes, one hit per attack per target.
5. **Input buffer** — directional and button history with leniency.
6. **Motion inputs** — quarter-circle, dragon punch, charge; with a buffer window.
7. **Combos/cancels** — cancel windows into specials/supers, hit-confirm rules.
8. **Rounds/timer** — best-of-3, 99-second timer, KO/time-over.
9. **Netcode** — rollback (preferred) or delay-based, with input prediction.

## Frame data

```text
startup:   frames before the hitbox is active
active:    frames the hitbox exists
recovery:  frames after, before returning to neutral
on hit:    hitstun - (active + recovery) = frame advantage
on block:  blockstun - (active + recovery) = frame advantage
```

- A move `-2 on block` means the attacker recovers 2 frames after the defender.
- `+` on hit means the attacker can link another move; `-` means punishable.
- Track these as data, not code, so balancing does not require a rewrite.

## Patterns

### 1. Fixed-tick loop

```text
accumulator += min(frame_dt, 0.25)
while accumulator >= TICK:
    step_simulation(TICK)   # inputs, physics, hit detection, state
    accumulator -= TICK
render(alpha = accumulator / TICK)   # optional interpolation
```

- 60 Hz ticks; never step gameplay with a variable `dt`.
- Clamp the frame delta to avoid a spiral of death after a hitch.
- Record inputs per tick for replays/rollback.

### 2. Hitbox/hurtbox resolution

```text
for each attacker's active hitbox:
    for each defender hurtbox:
        if overlap and not already_hit_this_attack:
            if defender blocking and facing attacker:
                apply blockstun, pushback, chip
            else:
                apply hitstun, damage, hitstop
            mark hit
```

- One hit per attack per target (unless multi-hit with a hit ID).
- Blocking requires holding back (relative to facing) and not being in hitstun.
- Hitstop freezes both fighters for a few frames on hit; it sells impact and gives hit-confirm
  time.
- Resolve hitboxes after movement in the same tick, deterministically.

### 3. Input buffer and motion inputs

```text
buffer: last N ticks of (direction, buttons)
quarter-circle forward: down, down-forward, forward within 6-10 ticks
dragon punch: forward, down, down-forward within 10-12 ticks
```

- Store inputs per tick; motions match a sequence within a window, not exact frame adjacency.
- Buffer a button press for 2–4 ticks so it can come out on the first actionable frame.
- Consume inputs when a move starts; do not let one press trigger two moves.
- Prefer "lenient" buffers for casual games; expose strict timing for competitive modes.

### 4. State machine and cancels

```text
Attack states: startup -> active -> recovery -> idle
Cancel: during active/recovery (per move), if input matches and meter allows -> next move
```

- Cancel windows are data per move (`cancel_into`, `cancel_start`, `cancel_end`).
- Hit-confirm: only cancel on hit/block if the design requires it; otherwise allow whiff cancels
  deliberately.
- Track `has_hit` per attack for combo scaling and one-hit rules.
- Combo scaling: damage decay per hit; hitstun decay to prevent infinite loops.

### 5. Rounds and timer

- Best-of-3; round timer 99 s; time-over compares health percentage.
- Reset positions, health, meter, and state between rounds.
- Pause stops the tick; menus do not advance it.

### 6. Netcode

- **Rollback**: simulate locally, predict remote inputs, roll back and resimulate on mismatch.
  Requires deterministic fixed-tick simulation and no reliance on render state.
- **Delay-based**: buffer remote inputs by N frames; simpler, feels laggy.
- Keep gameplay logic free of engine physics that is not deterministic across machines.
- Test with artificial latency/jitter/loss; verify both clients resolve the same hit.

## Pitfalls

- **Variable-dt gameplay** → different outcomes at different frame rates. Fixed tick.
- **Dropped combos online** → input buffer too strict or rollback simulation not deterministic.
- **One attack hits twice** → no per-attack hit flag/hit ID.
- **Blocking works from either side** → block check ignores facing.
- **Infinite combos** → no hitstun decay/scaling or repeated relaunches without limits.
- **Motions eat each other** → overlapping sequences without priority/consumption rules.
- **Hitstop desyncs online** → hitstop applied outside the deterministic simulation.
- **Physics-based knockback** → engine physics diverges; use deterministic velocity/state.
- **Round timer keeps running in pause** → timer driven outside the tick.
- **Training mode lies** → frame advantage display computed from render frames, not ticks.

## Composition

- **Input:** `input-systems` for bindings, gamepad, buffering.
- **Feel:** `game-feel` for hitstop, shake, impact.
- **AI:** `game-ai` for CPU opponents.
- **UI:** engine UI skill for health bars, timer, combo counter, frame-data display.
- **Netcode:** `godot-multiplayer` / `unity-networking` / `unreal-replication` for transport;
  rollback logic is yours.

## References

- Read `references/frame-data-hitboxes-and-netcode.md` for frame-advantage math, hitbox rules,
  buffer windows, rollback requirements and a fighting-game test checklist.
