# Detection, patrols and levels

Depth for `stealth-game`: cone math, meter tuning, AI and tests.

## Cone math

```text
to_target = normalize(target.pos - guard.pos)
angle = acos(dot(guard.forward, to_target))
in_cone = angle <= half_angle and distance <= range and raycast_clear
```

- Half-angle 30–45° for a focused guard, 60° for a relaxed one.
- Peripheral zone: wider angle, slower fill, shorter range.
- Vertical limit prevents seeing up cliffs.

## Fill/decay

```text
fill_rate = base * distance_factor * light_factor * motion_factor
distance_factor = 1 - clamp(distance / range, 0, 1) * 0.7
motion = crouch 0.5, walk 1.0, run 1.6
```

- Fill 0→100 in ~1.0–1.5 s in plain sight at mid range.
- Decay at ~40 % of fill rate; a guard should commit for a few seconds.
- Sound adds a one-shot suspicion spike, not continuous fill.

## Patrol pseudocode

```text
Patrol:
  move to waypoint
  wait and scan (rotate cone)
  next waypoint
Suspicious:
  face stimulus, pause 0.5 s
  if stimulus persists: Search
Search:
  sample 3-5 points around last_known
  inspect hiding spots
  after timer: Return
Alert:
  chase visible target
  if lost: Search last_known
```

## Test checklist

1. Cone visual matches the actual detection test.
2. Walls block sight at every angle.
3. Distance/light change fill time noticeably.
4. Sound creates investigation without instant detection.
5. Search is escapable and ends with a clear cue.
6. Guards do not track through walls after losing sight.
7. Takedowns require the intended position and state.
8. Checkpoints are frequent enough to learn from failure.
9. Ghost and assault routes both complete the level.
10. Accessibility cues exist for detection state.
