# Frame data, hitboxes and netcode

Depth for `fighting-game`: advantage math, hit resolution, input windows and rollback rules.

## Frame advantage

```text
on_hit   = hitstun   - (active + recovery)
on_block = blockstun - (active + recovery)
```

- Positive: attacker recovers first and can act.
- Negative: defender recovers first; attacker is punishable.
- Example: 5 startup, 3 active, 12 recovery, 18 hitstun → `18 - 15 = +3` on hit.
- Track per move: `startup`, `active`, `recovery`, `damage`, `hitstun`, `blockstun`, `hitstop`,
  `pushback`, `cancel_into`, `meter_gain`.

## Hit resolution order (per tick)

1. Read inputs, update state machines.
2. Apply movement/velocity.
3. Update hitbox/hurtbox positions.
4. Resolve hits (attacker first, deterministic order).
5. Apply hitstop/hitstun/blockstun/damage.
6. Advance timers, check KO/time-over.

- Resolve in a fixed order (e.g. player 1 then player 2) for determinism.
- One hit per attack per target; multi-hit moves use a hit ID and an interval.
- Trades: if both hit on the same tick, apply both or define a priority rule.

## Blocking

```text
blocking = holding_back && grounded && not in hitstun && not in attack recovery
```

- "Back" is relative to facing; crossing up flips the required direction.
- Blockstun prevents actions; pushback separates fighters.
- Chip damage optional; guard meter optional.

## Input buffer

| Input | Window (ticks) |
|-------|----------------|
| Button buffer | 2–4 |
| Quarter-circle | 6–10 |
| Dragon punch | 10–12 |
| Charge | 30–60 held, release within 5 |

- Store `(tick, direction, buttons)` in a ring buffer.
- Match motions backward from the current tick within the window.
- Consume the matched inputs so one motion cannot trigger twice.
- Prioritize specials over normals when both match.

## Hitstop

- Freeze both fighters for `hitstop` ticks on hit; keep the simulation tick running.
- Do not freeze the round timer or input recording.
- Apply inside the deterministic step, never in render code.

## Combo rules

- Damage scaling: e.g. 100 %, 90 %, 80 %, ... minimum 20 %.
- Hitstun decay after N hits to prevent infinites.
- Juggle limits: max air hits, gravity scaling.
- Combo counter resets on neutral/block.

## Rollback requirements

1. Fixed tick, deterministic simulation.
2. Serializable state (positions, velocities, states, timers, RNG).
3. Input history per tick.
4. Save states for the last N ticks (ring buffer).
5. On remote input arrival: restore the saved state, replay inputs, resimulate to now.
6. Render with prediction/interpolation; never mutate gameplay from render.

- Avoid engine physics bodies for gameplay; integrate your own deterministic movement.
- Seed RNG per tick and record it; do not use global random.
- Test: 100 ms latency + 5 % loss, both clients agree on hits and KO.

## Test checklist

1. Frame advantage matches the data table in training mode.
2. One attack hits once; multi-hit counts correctly.
3. Blocking requires holding back and facing the attacker.
4. Cross-ups flip block direction.
5. Motions come out within the buffer, not outside it.
6. Combos scale and cannot loop forever.
7. Hitstop freezes both fighters but not the timer.
8. Pause stops the simulation and timer.
9. Rollback: identical outcome under latency/jitter/loss.
10. Replays reproduce the match from recorded inputs.
