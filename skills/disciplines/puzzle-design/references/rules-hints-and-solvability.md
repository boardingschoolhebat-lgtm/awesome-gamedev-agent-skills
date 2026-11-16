# Rules, hints and solvability

Depth for `puzzle-design`: templates and verification.

## Rule table

| Object | Verb | Rule | Interaction |
|--------|------|------|-------------|
| Crate | push | moves one cell, stops at walls | fills pits, holds switches |
| Ice | slide | continues until blocked | changes routing |
| Switch | step | toggles linked gate | one-time or persistent |
| Portal | enter | teleports to pair | preserves momentum |

- Every row must be observable and testable in one room.
- Mark which rules combine; those pairs are your puzzle engine.

## Level progression

| Level | New | Known | Constraint |
|-------|-----|-------|------------|
| 1 | push | — | none |
| 2 | — | push | one crate |
| 3 | ice | push | slide routing |
| 4 | — | push + ice | two crates |
| 5 | switch | all | move limit |

- Add one variable per level; combine at most two.

## Hint ladder

```text
1. "Look at the ice."                  (attention)
2. "Crates stop on ice only at walls." (rule)
3. "Push the crate left first."        (step)
4. Show the full solution.             (answer)
```

- Hints are opt-in; record which level was used.
- The full solution should be available for accessibility, not forced.

## Solvability checklist

1. Write the intended solution as a move list.
2. Find at least one alternate solution, or justify the single path.
3. Enumerate small state spaces; check every reachable state for a legal move.
4. Detect dead states and confirm reset/undo is available.
5. Verify no solution depends on frame-perfect timing unless the genre demands it.
6. Test the level after a rule change; old solutions may break.

## Playtest protocol

- Observe without hinting; note the first move and the first reset.
- Ask "what did you think the rule was?" after the solve.
- Record solve time, resets, hints and quits per level.
- Re-test with new players after changes; compare per-level funnels.

## Checklist

1. Rules fit on one page and are consistent.
2. Every level teaches or tests a rule.
3. Early levels solve without text.
4. Hint ladder exists and is opt-in.
5. Undo/reset is instant; softlocks are detected.
6. At least one alternate solution or a justified single path.
7. Difficulty rises through constraints, not obscurity.
8. Metrics cover solve rate, resets, hints and quits.
9. A puzzle spec records rules and solutions.
10. Accessibility: colorblind-safe state, no audio-only clues.
