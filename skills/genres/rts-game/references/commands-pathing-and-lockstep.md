# Commands, pathing and lockstep

Depth for `rts-game`: orders, crowds, fog, economy and tests.

## Order model

```text
Order = { type, target, position, queue: bool }
types: move, attack_move, attack_target, gather, build, patrol, hold, stop
```

- Right-click resolves context: enemy → attack, resource → gather, ground → move.
- Shift appends; without shift, replace the queue.
- Acknowledge the order immediately (voice/animation), even if the path is pending.

## Selection

```text
box select: units whose screen bounds intersect the rectangle
filter: player-owned, alive, selectable
group: store ids; prune dead ids each frame
```

- Double-click selects same type on screen.
- Ctrl+click removes from selection.
- Selection cap per group (e.g. 24–60) for readability and performance.

## Flow fields

```text
1. Build cost field from terrain (blocked = infinite).
2. Dijkstra/BFS from the goal over the grid -> integration field.
3. Each cell stores the best direction to the goal.
4. Units sample the field + local avoidance.
```

- One field per destination, shared by all units; recompute when the goal or terrain changes.
- A* per unit is fine for small counts; flow fields scale to hundreds.
- Add separation forces to avoid stacking at the goal.

## Fog filtering

```text
for each player:
    visible = units in vision radius and line of sight
    explored |= visible terrain
    send: visible enemies; explored terrain; remembered buildings (optional ghost)
```

- Never send hidden enemy positions "for effects"; clients can read them.
- Recompute visibility on a timer (e.g. 4–10 Hz), not every frame.

## Economy table (starting point)

| Worker | Gather rate | Node capacity | Expansion cost |
|--------|-------------|---------------|----------------|
| 1 | 5/s | 1,500 | 400 |
| 8 | saturation | — | — |
| 16 | over-saturated | — | — |

- Two workers per node is a common saturation point; tune to your game.
- Expansion pays back in 3–5 minutes; earlier if contested.

## Test checklist

1. Box select, shift-add, control groups survive unit death.
2. Attack-move engages on sight and resumes movement.
3. Queued orders execute in order and can be cancelled.
4. 200 units path to one goal without a single-file traffic jam.
5. Fog hides enemies from clients, not just visually.
6. Supply block warns and prevents production.
7. Counters work: armored vs piercing, air vs ground.
8. AI expands and counters with a human-like delay.
9. Lockstep replay reproduces the match; no desync after 20 minutes.
10. Minimap alerts on attacks and jumps the camera.
