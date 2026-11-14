# Vehicle, laps and AI

Depth for `racing-game`: handling math, checkpoint/lap validation, AI profiles and tests.

## Handling model

### Arcade

```text
speed   += throttle * power * dt
speed   -= drag * speed * |speed| * dt
speed   -= brake * sign(speed) * brake_force * dt
steer    = input * max_steer * clamp(speed / ref_speed, 0, 1)
yaw_rate = steer * speed / wheelbase
```

- Grip blends velocity toward the forward axis: `v = lerp(v, forward*speed, grip*dt)`.
- Drift: reduce grip on handbrake, add countersteer assist.
- Downforce: increase grip with speed for stability.

### Raycast suspension

```text
compression = rest_length + radius - hit_distance
spring      = stiffness * compression
damper      = damping * compression_velocity
force       = clamp(spring - damper, 0, max_force)
```

- Apply along the contact normal at the wheel mount.
- Tire force: `lateral = -slip_angle * cornering_stiffness`, clamped by friction circle.
- Friction circle: `sqrt(long^2 + lat^2) <= mu * load`.

## Tuning order

1. Mass and center of mass.
2. Suspension rest length/travel (visual ride height).
3. Spring stiffness (bounce), then damping (oscillation).
4. Tire grip (cornering), then engine/brake force.
5. Steering range and speed scaling.
6. Assists (traction control, stability, auto-countersteer).

Change one parameter at a time; log values.

## Checkpoints

```text
next = 0
on enter(i):
  if i == next:
    next += 1
    split[i] = now - lap_start
  if i == finish and next == count:
    lap_time = now - lap_start
    lap_start = now
    next = 0
```

- Ordered checkpoints prevent cuts.
- Direction check: `dot(car_forward, track_forward) > 0`.
- Finish line = checkpoint 0 after the last checkpoint.
- Respawn at `checkpoints[next-1]`.
- Invalid lap if a checkpoint was skipped: reset `next` to 0.

## Timing

- Start timer on crossing the start line, not on spawn.
- Pause when the game pauses; do not count countdown.
- Use monotonic time (`Time.get_ticks_usec`, `AudioSettings.dspTime` is audio-only; use
  `Time.timeAsDouble`/`Stopwatch`).
- Store best/last/splits; show delta to best.

## AI

```text
target = racing_line.point_at(distance + look_ahead * speed)
steer  = angle_to(target) * steer_gain
target_speed = speed_profile(curvature_ahead)
throttle = clamp((target_speed - speed) * gain, -1, 1)
```

- Speed profile: `v = sqrt(mu * g / curvature)` clamped by car top speed.
- Avoidance: lateral offset when another car is within a cone ahead.
- Rubber-band: `ai_speed *= 1 + clamp((player_distance - ai_distance) * k, -0.1, 0.1)`.
- Add small driving-line offsets per AI for variety.

## Test checklist

1. Car accelerates, brakes, and reverses predictably.
2. Steering is stable at low and high speed.
3. Handbrake drifts and recovers.
4. Suspension absorbs bumps without launching.
5. Car cannot cut checkpoints; reverse crossing does not count.
6. Lap timer starts/stops on the line; pause pauses it.
7. Respawn returns to the last checkpoint, upright, no lap gain.
8. AI completes laps without stuck states and slows for corners.
9. Rubber-banding keeps races close without teleporting.
10. Camera and HUD stay readable at top speed.
