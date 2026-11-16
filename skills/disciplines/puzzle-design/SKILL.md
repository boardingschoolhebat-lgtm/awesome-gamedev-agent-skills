---
name: puzzle-design
description: >
  Design puzzles and their progression: rule sets and affordances, level grammar, teaching without
  text, difficulty curves, hint ladders, undo/reset, solvability verification and playtest metrics.
  Use when creating or fixing logic, spatial, deduction or physics puzzles.
---

# Puzzle design

A puzzle is a promise that the rules are enough. The player experiments, forms a hypothesis, and
feels the click when it lands. Design the **rule space** and the **sequence of constraints**, not
a pile of clever levels. This is a **compositional** skill: pair with `level-design`,
`tutorial-design` and the `puzzle` genre for implementation.

## When to use

- Use when designing a mechanic, puzzle set, difficulty curve, hints or a solver.
- Use when playtests show brute force, moon logic, or players quitting before the aha.

**When *not* to use:** match-3/grid resolution code → `puzzle` genre; onboarding flow only →
`tutorial-design`; level layout only → `level-design`; narrative puzzles → `narrative-design`.

## Rule-first design

```text
verbs + objects + constraints = puzzle space
```

- Define 3–6 verbs and 3–8 object types; interactions should compose.
- Every rule must be observable and consistent; no hidden exceptions.
- Prefer rules that interact (push + ice + weight) over many one-off objects.
- Write the rule table before building levels; it is the design contract.
- If a level needs a new rule, teach it in a safe room first.

## Puzzle types

| Type | Player action | Example |
|------|---------------|---------|
| Spatial | move/rotate/stack | block pushing, room rotation |
| Deduction | infer from clues | logic grid, whodunit |
| Constraint | allocate limited resources | bridges, circuits, scheduling |
| Physics | predict trajectories | catapults, momentum |
| Word/number | decode patterns | ciphers, arithmetic |
| Meta | use knowledge of the game | fourth-wall, save-file tricks |

- Mix types across a chapter; do not stack three deduction puzzles in a row.

## Level grammar

```text
introduce -> practice -> combine -> twist -> mastery
```

- Introduce one rule in isolation, with a safe failure.
- Combine two known rules; the solution should feel inevitable in hindsight.
- Twist: same rules, a non-obvious consequence.
- Mastery: optional hard levels for confident players.
- Difficulty rises through constraints (fewer moves, tighter space), not through obscurity.

## Teaching without text

- Design the room so the only sensible action demonstrates the rule.
- Use affordances: color, shape, sound, animation, a ghost solution.
- Let the player fail cheaply and reset instantly.
- A prompt is a fallback, not the primary teacher; see `tutorial-design`.

## Hints and recovery

- Hint ladder: nudge → rule reminder → next step → full solution.
- Hints should be optional, progressive and never auto-solve without consent.
- Undo one step, reset the room, and restart the chapter; all must be instant.
- Track moves/time but do not punish exploration.
- If a state is unwinnable, detect it and offer reset.

## Solvability and verification

- Write the intended solution and at least one alternate; if none, the puzzle may be too tight.
- Brute-force small state spaces; for large ones, use invariants or a solver.
- Check for softlocks: states with no legal move and no reset.
- Test with fresh players and with a speedrunner; both find different issues.
- Keep a puzzle spec: rules, intended solution, alternates, known exploits.

## Difficulty and metrics

```text
solve rate, time to first move, resets, hints used, quit rate
```

- A good early puzzle: 70–90 % solve without hints.
- A hard optional puzzle: 20–40 %, with a clear hint path.
- If players brute-force, the state space is too small or the rule is unclear.
- If players never move, the affordance is missing.

## Pitfalls

- **Moon logic** → solution depends on hidden knowledge. Teach the rule or change it.
- **One solution** → brittle and frustrating. Allow alternates.
- **Brute force** → few states. Add constraints or larger space.
- **Softlock** → no reset. Detect and offer undo/reset.
- **Text wall tutorial** → players skip. Teach in the room.
- **Difficulty cliff** → new rule + tight constraint at once. Split the beats.
- **Hint spoils** → full solution first. Use a ladder.
- **Padding** → repeated puzzles with bigger numbers. Add a twist instead.
- **Unreadable state** → players cannot plan. Show consequences and valid moves.
- **No spec** → cannot verify solvability. Write the solution down.

## Composition

- **Genre:** `puzzle` for board state, matching, undo and progression.
- **Teaching:** `tutorial-design` for onboarding and prompts.
- **Levels:** `level-design` for room layout and sightlines.
- **UI:** `game-ui-ux` for readable state, hints and reset.
- **Narrative:** `narrative-design` when puzzles carry story meaning.

## References

- Read `references/rules-hints-and-solvability.md` for a rule table template, level progression,
  hint ladder, solver checklist and puzzle playtest protocol.
