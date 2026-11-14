# State machines, blending and root motion

Depth for `animation-systems`: graph design, blend math, ownership rules and debugging.

## Graph design

Keep three layers of responsibility separate:

| Layer | Owns | Example |
|-------|------|---------|
| Gameplay | what the character is doing | `is_grounded`, `speed`, `attack_id` |
| Animation graph | how that looks | Idle/Run/Jump, attack states |
| Presentation | events and VFX | footstep, dust, hit spark |

Rules:

- One writer for each parameter (the controller), one reader (the graph).
- States represent *postures*, not every clip. A blend tree inside one state covers speed ranges.
- Prefer 5–10 states per character; if you need 30, the graph is encoding gameplay logic.
- AnyState transitions only for interrupts (hit, death), never for normal flow.

## Blend math

1D:

```text
t = clamp((speed - min_speed) / (max_speed - min_speed), 0, 1)
pose = lerp(walk, run, t)
```

2D freeform:

```text
p = Vector2(dot(v, right), dot(v, forward)) / max_speed
weights = inverse-distance to sample points (engine handles it)
```

- Normalize inputs to the same units the clips were authored for.
- Sync phases: if walk is 0.8 s and run is 0.5 s, sync by normalized time, not raw time.
- Additive layers: breathing, lean, aim offset — keep amplitudes small or they overpower base.

## Root motion

Choose the owner per state:

| State | Owner | Why |
|-------|-------|-----|
| Locomotion | controller | responsive input |
| Attack lunge | animation | exact reach |
| Vault/climb | animation (warped) | precise alignment |
| Knockback | physics/controller | gameplay-driven |

- Root motion + capsule movement = double displacement; disable one.
- For networked games, root motion must be simulated on the server or replayed from inputs.
- Bake root motion into clips consistently; mixing in-place and root-motion clips causes pops.

## Events and notifies

- Emit named events, not raw frame numbers, from the clip.
- Exactly one listener per event type per character.
- Guard against duplicate fires during blends and re-entry.
- Keep the event table next to the frame data so combat and animation agree.
- In multiplayer, hit windows are server-authoritative; local events are cosmetic.

## IK

- Foot IK: raycast below each foot, adjust `TwoBoneIK` target; blend by ground distance.
- Hand IK: attach to weapon grip; disable when the weapon is holstered.
- Look-at: clamp yaw/pitch, blend out at range.
- IK after animation evaluation, before skinning; costs scale with affected bones.

## Debugging checklist

1. Log the parameter values each frame; do they match gameplay?
2. Visualize the current state and transition (engine debugger).
3. Freeze the blend parameter and step through poses.
4. Check clip import settings (loop, root motion, events) after re-export.
5. Compare capsule velocity to animation velocity for foot sliding.
6. Verify layers/masks: disable layers one at a time.
7. Test at 30/60/144 FPS; parameter damping must be delta-time based.
8. Re-enter every state twice; events must not double-fire.
