# Ball, rules and team AI

Depth for `sports-game`: constants, rule states, AI scoring and tests.

## Ball constants (starting points)

```text
mass            0.43 kg (soccer)
radius          0.11 m
restitution     0.6–0.8
linear drag     0.1–0.3 /s
angular drag    0.05–0.2 /s
max shot speed  25–30 m/s
CCD             on (continuous)
```

- Tune drag so a long pass is playable, not floaty.
- Spin force: `F = k * (ω × v)`; clamp to avoid curve chaos.

## Rule states

```text
InPlay -> Goal -> Kickoff
InPlay -> OutOfBounds -> ThrowIn/Corner/GoalKick
InPlay -> Foul -> FreeKick/Penalty
Any -> HalfTime -> Kickoff
Any -> FullTime
```

- Each transition records the event, actors, position and match time.
- Restart states freeze the ball and position players legally.

## Offside snapshot

```text
on pass event:
    store positions of attackers, defenders, ball at that tick
on reception:
    attacker ahead of second-last defender and ball at pass time -> offside
```

## AI decision scoring

```text
score(pass) = lane_clear * 0.4 + receiver_open * 0.3 + progress * 0.2 - risk * 0.1
score(shoot) = angle * 0.5 + distance_score * 0.3 + keeper_out * 0.2
```

- Evaluate every 100–200 ms; add hysteresis so players do not oscillate.
- Formation: anchor + offset; return force proportional to distance.
- Stamina affects speed and decision quality, not teleporting stats.

## Test checklist

1. Ball rolls, bounces, and stops believably on each surface.
2. Shots at max speed do not tunnel through the goal.
3. Goal only when the ball fully crosses the line.
4. Out-of-bounds restarts correct for each edge.
5. Offside uses pass-time positions.
6. Clock stops/starts correctly per period and added time.
7. AI keeps formation; no 10-player swarm.
8. Keeper saves and distribution are plausible.
9. Replay matches the recorded event.
10. Online: both clients agree on score and goals.
