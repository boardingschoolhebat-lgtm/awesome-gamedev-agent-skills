---
name: racing-game
description: >
  Build a racing game: arcade vs sim handling, raycast suspension or wheel colliders, steering
  and drift, checkpoints and lap timing, respawn, AI racing lines and rubber-banding, camera and
  HUD. Use for a racing/driving game or for tuning vehicle feel and lap logic.
---

# Racing game

A racing game is vehicle feel plus a trustworthy lap system. The car model decides whether the
game is arcade or simulation; the lap/checkpoint logic decides whether results are fair. This is a
**compositional** skill: it uses `physics-tuning`, `camera-systems` and `game-ui-ux`.

## When to use

- Use when building a racing/driving game, tuning car handling, or implementing laps/checkpoints.
- Use when cars flip, slide uncontrollably, or lap times are wrong.

**When *not* to use:** a pure driving sandbox with no race structure → vehicle physics only;
kart-style party game → keep the arcade model but add items; open-world driving → streaming and
traffic systems are separate.

## Core loop

**Choose car/track → countdown → drive laps → hit checkpoints in order → cross the finish line →
lap time recorded → best lap/position → race ends → results.**

## Must-have systems

1. **Vehicle model** — arcade (direct velocity/steering) or simulated (suspension + tire forces).
2. **Steering/assist** — speed-sensitive steering, traction control, ABS, auto-countersteer.
3. **Checkpoints** — ordered triggers that validate a lap; finish line is the last one.
4. **Lap timer** — starts on the start line, splits per checkpoint, stops at finish.
5. **Respawn/reset** — return to the last checkpoint, upright, with a short penalty.
6. **Camera** — chase with look-ahead, cockpit/bumper, FOV tied to speed.
7. **HUD** — speed, gear, lap, position, best/last lap, minimap.
8. **AI** — racing line following, avoidance, rubber-banding (optional).

## Arcade vs sim

| Aspect | Arcade | Sim |
|--------|--------|-----|
| Model | velocity + yaw, grip multipliers | suspension, tire slip, weight transfer |
| Steering | direct, speed-scaled | steering angle + Ackermann |
| Drift | scripted/handbrake | tire slip angle |
| Tuning | feel-first | measured-first |
| Risk | floaty, no weight | unforgiving, hard to tune |

Start arcade for a small game; add suspension only if the fantasy needs it. A common hybrid:
raycast suspension for bumps + simplified tire forces for grip.

## Patterns

### 1. Arcade car (velocity + yaw)

```python
# Pseudocode per fixed step.
speed = dot(velocity, forward)
speed += throttle * engine_power * dt
speed -= drag * speed * abs(speed) * dt
speed -= brake * sign(speed) * brake_power * dt

steer = steering_input * max_steer * clamp(speed / steer_ref_speed, 0, 1)
yaw_rate = steer * speed / wheelbase
yaw += yaw_rate * dt

velocity = forward * speed
position += velocity * dt
```

- Steering authority scales with speed but saturates; zero at standstill.
- Lateral grip: blend velocity toward `forward * speed` by a grip factor; lower grip = drift.
- Clamp `dt` to avoid tunneling at low frame rates; use a fixed physics step.

### 2. Raycast suspension (arcade-sim hybrid)

```text
for each wheel:
    ray from mount downward, length = rest_length + radius
    if hit:
        compression = (rest_length + radius - distance)
        force = stiffness * compression - damper * wheel_velocity_y
        apply force at mount along suspension normal
        grip = tire_curve(slip_angle, surface)
```

- Apply suspension and tire forces at the wheel contact, not the center of mass, or the car
  cannot pitch/roll.
- `stiffness`, `damper` and `rest_length` interact; change one at a time.
- A rigid body with 4 raycasts is enough for most arcade racers.

### 3. Engine-specific vehicles

**Godot 4.7** — `VehicleBody3D` + one `VehicleWheel3D` per wheel:

```gdscript
@onready var wheel_fl: VehicleWheel3D = $WheelFL
@onready var wheel_fr: VehicleWheel3D = $WheelFR

func _physics_process(delta: float) -> void:
    var steer := Input.get_axis("steer_left", "steer_right")
    wheel_fl.steering = steer * 0.5
    wheel_fr.steering = steer * 0.5
    var throttle := Input.get_axis("brake", "accelerate")
    wheel_fl.engine_force = throttle * 300.0
    wheel_fr.engine_force = throttle * 300.0
    brake = 10.0 if Input.is_action_pressed("handbrake") else 0.0
```

- `VehicleBody3D` uses raycast wheels; set `use_as_steering` on front wheels.
- Do not set the body's position/orientation directly; drive it with forces.
- Tune `suspension_stiffness`, `suspension_travel`, `suspension_max_force`, wheel friction.

**Unity** — `WheelCollider`:

```csharp
wheel.motorTorque = throttle * motorTorque;
wheel.steerAngle = steer * maxSteer;
wheel.brakeTorque = braking * brakeTorque;
wheel.GetWorldPose(out var pos, out var rot);
wheelMesh.SetPositionAndRotation(pos, rot);
```

- `WheelCollider` is a raycast spring-damper with slip-based friction.
- Update wheel meshes from `GetWorldPose`, not by parenting.
- Adjust `forwardFriction`/`sidewaysFriction` curves for grip and drift.

### 4. Checkpoints and lap validation

```text
checkpoints[0..n-1] in order; finish line is the last
on trigger enter:
    if index == next_checkpoint: next_checkpoint += 1
    if index == finish and next_checkpoint == n: lap_complete(); next_checkpoint = 0
```

- Require ordered checkpoints; a player cannot cut the course.
- Use trigger volumes wide enough for the full track, not a single point.
- Finish line should also require crossing direction (dot product with track forward > 0).
- On lap complete: record time, reset splits, increment lap, handle race end.
- Practice/qualifying: timer starts when crossing the line, not on spawn.

### 5. Lap timing

```text
lap_start = now()
on checkpoint: split[i] = now() - lap_start
on finish: lap_time = now() - lap_start; best = min(best, lap_time)
```

- Use the physics/simulation clock or a monotonic timer, not frame counts.
- Pause must pause the timer; countdown should not.
- Store best lap per track/car; persist with `save-systems`.
- Display last/best/delta; delta to best is the most useful feedback.

### 6. Respawn

- Store the last passed checkpoint transform (position + forward).
- On reset: place the car above the checkpoint, zero velocity/angular velocity, brief
  invulnerability, add a time penalty if the race is competitive.
- Pressing reset should not skip a checkpoint or grant a shorter lap.

### 7. AI and rubber-banding

- Follow a spline/racing line with look-ahead; steer toward a point ahead, not the car.
- Slow down for corners based on curvature; use a speed profile per segment.
- Avoidance: lateral offset when a car is close ahead.
- Rubber-banding: scale AI top speed/acceleration by distance to the player, with caps; too much
  feels fake.

## Pitfalls

- **Car flips instantly** → center of mass too high or suspension forces applied at the body
  center. Lower COM, apply at wheels.
- **Uncontrollable at speed** → steering not speed-scaled or too much grip. Scale steering and
  tune lateral grip.
- **Car slides forever** → no lateral friction/drag; add grip and rolling resistance.
- **Tunneling through track** → large `dt` or thin colliders. Fixed step + continuous collision.
- **Lap counts on reverse crossing** → no direction check or unordered checkpoints.
- **Checkpoint skipped** → trigger too small or respawn placed past it.
- **Timer drifts** → frame-count timing; use monotonic time and pause.
- **Camera nausea** → FOV/look-ahead too aggressive; add shake/FOV options.
- **Wheel meshes detached** → parented instead of updated from wheel pose.
- **AI drives on rails** → no avoidance or speed variation; add offsets and corner slowdown.

## Composition

- **Physics/feel:** `physics-tuning`, `game-feel`.
- **Camera:** `camera-systems`, `godot-camera` / `roblox-camera`.
- **UI:** `game-ui-ux` + engine UI skill for HUD and results.
- **Track building:** `level-design`; tile/grid only for 2D racers.
- **Save:** `save-systems` for best laps, unlocks, settings.
- **Audio:** `audio-design` for engine loops and tire/impact SFX.

## References

- Read `references/vehicle-laps-and-ai.md` for handling formulas, checkpoint validation, timing
  rules, AI speed profiles and a racing test checklist.
