# Unity 3D controllers and cameras

Reference material for `SKILL.md`. Targets **Unity 6.3 LTS (6000.3)**.

## Controller comparison

| Approach | Strengths | Costs | Use for |
|----------|-----------|-------|---------|
| `CharacterController` | Crisp stops, built-in slope/step handling, no tipping | No physics forces, not pushed by rigidbodies, manual gravity | FPS/TPS players, NPCs on navmesh |
| `Rigidbody` (dynamic) | Forces, collisions, moving platforms, ragdolls | Tipping, sliding, needs damping/friction tuning | Physics-driven players, vehicles, props |
| `Rigidbody` (kinematic) + `MovePosition` | Full control, interacts with dynamic bodies | Manual collision resolution | Elevators, moving platforms, scripted actors |

Never put a `CharacterController` and a `Rigidbody` on the same player: two movement authorities
fight over the transform.

## CharacterController properties

| Property | Effect | Typical player value |
|----------|--------|----------------------|
| `height` | Capsule height | 1.8–2.0 m |
| `radius` | Capsule radius | 0.3–0.4 m |
| `center` | Capsule offset from the transform | `(0, height/2, 0)` |
| `slopeLimit` | Maximum climbable angle | 45° |
| `stepOffset` | Maximum step height | 0.3 m |
| `skinWidth` | Collision tolerance | 0.02–0.08 m |
| `detectCollisions` | Collision response | On unless you resolve manually |
| `minMoveDistance` | Ignore micro-moves | 0.001 m |

`skinWidth` too small causes jitter against walls; too large makes the capsule hover. Keep it
around 10% of the radius.

## Gravity and jump

```csharp
verticalVelocity.y += gravity * Time.deltaTime;   // gravity is negative, e.g. -24
controller.Move(verticalVelocity * Time.deltaTime);
```

Jump impulse for a target height `h` under gravity `g`:

```text
v = sqrt(h * -2 * g)
```

With `h = 1.2` and `g = -24`, `v ≈ 7.6 m/s`. Keep gravity stronger than real gravity (-9.81) for
game feel; most action games use -20 to -40.

Ground snapping: when grounded and falling, set vertical velocity to a small negative value
(`-2`) so the capsule stays in contact instead of skipping down slopes.

## Ground checks

| Method | Gives | Cost | Notes |
|--------|-------|------|-------|
| `controller.isGrounded` | Boolean | Free | Updated by `Move`; false for a frame after jumping |
| `Physics.SphereCast` down | Hit, normal, distance | One query | Best for slopes, step detection, moving platforms |
| `Physics.CheckSphere` | Boolean | One query | Cheap but no normal |
| Trigger volume under feet | Enter/exit events | Event-driven | Lags by a physics step; fine for coyote time |

For a SphereCast ground check, start slightly above the capsule bottom and use a radius just under
the controller radius, with a layer mask that excludes the player.

## Camera rigs

### First person

```text
Player (yaw)
└── CameraPivot (pitch, at eye height)
    └── Main Camera
```

- Yaw on the player so movement follows the view.
- Pitch on the pivot, clamped to about ±89°.
- Lock the cursor in play mode and re-lock on click after Escape.

### Third person

```text
Player (yaw)
└── CameraPivot (pitch, at shoulder height)
    └── OrbitCamera (position/rotation driven by LateUpdate)
```

- The camera is not parented to the pivot; the script places it each `LateUpdate`.
- SphereCast from the pivot along `-pivot.forward` and clamp the distance.
- Smooth position with `1 - exp(-k * dt)`, rotation with `Quaternion.Slerp` or `LookRotation`.
- Cinemachine 3 (`com.unity.cinemachine`) is an alternative follow/collision implementation; check
  the component names against the installed package version before scripting against them.

## Layers and queries

- Put the player on a `Player` layer, level geometry on `Ground`/`Default`, and set the ground mask
  to exclude `Player`.
- Use `QueryTriggerInteraction.Ignore` for solid geometry checks; `Collide` when triggers matter.
- `Physics.Raycast` for hitscan and line of sight; `SphereCast` for anything with volume (ground,
  camera, character sweeps).

## Moving platforms

`CharacterController` is not carried by a moving collider. Two workable options:

1. Parent the player to the platform while grounded (watch for scale changes).
2. Record the platform's position delta each frame and add it to `controller.Move` while standing
   on it.

For Rigidbody players, add the platform's velocity to the body while grounded, or use a moving
platform component that applies the delta.

## Playtest checklist

1. Walk into a wall: no jitter, no climbing, no tunneling at max speed.
2. Ramp at `slopeLimit - 5°`: climbable; at `slopeLimit + 5°`: blocked or sliding.
3. Stairs at `stepOffset - 0.05 m`: climb smoothly; higher steps block.
4. Jump on flat ground, up a slope, and off a ledge: arc matches the intended height.
5. Camera at a wall corner and under a low ceiling: pulls in instead of clipping.
6. Cursor lock/unlock (Escape, alt-tab) leaves the camera controllable on return.
7. Frame rate drop (or `Time.timeScale` change) does not change mouse sensitivity or camera
   smoothing feel.
8. Rigidbody variant: no tipping, no jitter in `FixedUpdate`, interpolation enabled if the camera
   stutters.
