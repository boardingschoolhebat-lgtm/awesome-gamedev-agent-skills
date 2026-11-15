# Beats, choices and docs

Depth for `narrative-design`: templates and checks.

## Beat sheet template

| # | Beat | Purpose | Player does | Change | Next |
|---|------|---------|-------------|--------|------|
| 1 | Inciting | hook | choose to help | goal set | 2 |
| 2 | Threshold | commit | enter dungeon | no return | 3 |
| 3 | Midpoint | reversal | learn the truth | ally becomes rival | 4 |
| 4 | Crisis | cost | sacrifice | power at a price | 5 |
| 5 | Climax | choice | decide fate | ending branch | 6 |

- Every row must change information, relationship, power or place.
- Mark branch points and where they fold back.

## Foldback

```text
act 1 --+--> branch A --+
        |               +--> act 2 --+--> branch C --+--> ending 1
        +--> branch B --+            +--> branch D --+--> ending 2
```

- Branches live inside an act; acts rejoin at a gate.
- The gate can acknowledge the branch with a line, a prop or an NPC, cheaply.

## Choice matrix

| Choice | Flag | Immediate | Delayed | Ending |
|--------|------|-----------|---------|--------|
| Spare the spy | `spy_alive` | ally joins | intel in act 3 | ending B |
| Execute the spy | `spy_dead` | fear +1 | ambush in act 3 | ending A |

- Every flag needs a payoff or it is dead state.
- Keep the number of ending-critical flags small (3–5).

## Scene checklist

1. Who wants what in this scene?
2. What changes by the end?
3. What does the player do besides watch?
4. Is the exposition earned by a question or a conflict?
5. Does the choice have a visible cost?
6. Is the consequence traceable later?
7. Does the scene fit the act's tension curve?
8. Can it be cut without breaking the plot?

## Narrative review

- Premise, theme and core loop agree.
- The first 10 minutes contain a hook and a choice.
- Every act ends on a reversal or decision.
- Branch count and endings fit the production budget.
- All ending-critical flags have payoffs.
- Essential lore is on the main path; optional lore is optional.
- Character voices are distinguishable without name tags.
- A recap can reconstruct the player's choices.
