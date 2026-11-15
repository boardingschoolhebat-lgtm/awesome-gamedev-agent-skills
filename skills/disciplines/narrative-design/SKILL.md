---
name: narrative-design
description: >
  Design game story and structure: premise, theme, character want/need, beat sheets, pacing,
  branching and foldback, meaningful choices and consequences, environmental storytelling, and
  ludonarrative consonance. Use when shaping a plot, questline or branching narrative.
---

# Narrative design

Narrative design is the structure that makes player actions feel like a story. It is not the
dialogue engine and not the quest log: it is **who wants what, why now, what it costs, and what
changes**. This is a **compositional** skill: pair with `dialogue-systems` and `quest-design` for
implementation.

## When to use

- Use when designing a premise, story beats, character arcs, factions or endings.
- Use when a branching story sprawls, choices feel fake, or pacing drags.

**When *not* to use:** dialogue trees/conditions → `dialogue-systems`; objective tracking and
rewards → `quest-design`; tutorial teaching → `tutorial-design`; level layout → `level-design`.

## Core questions

```text
Who is the player? What do they want? What do they need? What stands in the way?
Why now? What happens if they fail? What changes by the end?
```

- **Want** drives plot; **need** drives arc. Conflict comes from the gap.
- Theme is a question the game argues about, not a moral pasted on the ending.
- Stakes must be legible: personal, immediate and escalating.

## Structure

| Structure | Shape | Use |
|-----------|-------|-----|
| Three-act | setup → confrontation → resolution | clean commercial arcs |
| Five-act | inciting → rising → midpoint → falling → denouement | longer RPGs |
| Kishōtenketsu | introduction → development → twist → conclusion | no-conflict slice-of-life |
| String of pearls | hub + episodic set-pieces | open-ish RPGs |
| Foldback | branches rejoin at fixed beats | scope-controlled choice |
| Gauntlet | linear with varied encounters | shooters, action |

- Pick the structure before writing scenes; it caps scope.
- A beat is a change: information, relationship, power or location.
- Every act ends on a decision or a reversal, not a cutscene.

## Pacing

- Alternate tension and release; a quiet beat makes the next loud one land.
- Escalate cost, not only enemy count.
- Cut scenes that do not change a relationship, a goal or the world.
- Front-load a hook in the first 10 minutes; earn the exposition later.
- Use a beat sheet with columns: beat, purpose, player action, change, next.

## Choice and consequence

Meaningful choices are:

1. **Informed** — the player understands the trade-off.
2. **Irreversible** — or costly to reverse.
3. **Thematic** — they express values, not just loot.
4. **Consequential** — the world or characters remember.

| Choice type | Scope | Cost |
|-------------|-------|------|
| Cosmetic | dialogue tone, outfit | low |
| Tactical | approach, faction, resources | medium |
| Narrative | who lives, who rules | high |
| Ending | final state | highest |

- Foldback keeps production finite: branch for a scene, rejoin at the next act.
- Telegraph consequences; a surprise betrayal still needs setup.
- Delayed consequences are powerful but must be traceable in the journal/recap.
- Avoid fake choices with one real outcome; players notice.

## Characters

```text
want (external goal) + need (internal lack) + flaw + pressure = arc
```

- Give antagonists a coherent logic; "evil" is not a motive.
- Relationships change through scenes; track affinity/faction state only if it changes content.
- Voice: vocabulary, rhythm, what they refuse to say.
- Kill/retire characters only when it changes the plot or the player's options.

## Environmental storytelling

- Show cause and effect: damage, barricades, graves, overheard lines.
- Let props and layout imply the story; do not put the lore in a note next to the object.
- Negative space: what is missing is often louder than what is present.
- Audio and lighting carry tone cheaply; use them before another cutscene.
- Optional lore (codex, audio logs) should deepen, never gate understanding.

## Ludonarrative consonance

- Mechanics should express the theme: scarcity for survival, decay for loss, bureaucracy for
  dystopia.
- Dissonance appears when the story says "hurry" and the loop rewards looting every box.
- Test: describe the core loop and the premise in one sentence each; do they agree?

## Documentation

- **Story bible:** world rules, factions, timeline, character sheets, tone.
- **Beat sheet:** ordered changes, player actions, branch points.
- **Node map:** scenes and gates, with foldback points marked.
- **Choice matrix:** choice → state flag → payoff scene → ending.
- **Lore budget:** what the player must know vs optional depth.

## Pitfalls

- **Lore dump opening** → players skip. Start with a decision, reveal through action.
- **Branch explosion** → combinatorial content. Fold back at act boundaries.
- **Fake choices** → trust collapses. Cut them or make them cosmetic and honest.
- **Theme stated, not played** → ending feels unearned. Encode it in mechanics.
- **Pacing flat** → no quiet beats, constant noise. Alternate tension/release.
- **Character arc reset** → no consequence. Persist state and acknowledge it.
- **Collectible lore carries the plot** → most players miss it. Put essentials in the main path.
- **Retcons** → contradicting established rules. Keep a canon timeline.

## Composition

- **Dialogue:** `dialogue-systems` for nodes, conditions and variables.
- **Quests:** `quest-design` for objectives, rewards and anti-softlock.
- **Levels:** `level-design` for environmental storytelling and pacing.
- **Genres:** `rpg`, `visual-novel`, `horror-game`, `mmorpg`.
- **UI:** `game-ui-ux` for journal, recap and choice presentation.

## References

- Read `references/beats-choices-and-docs.md` for a beat-sheet template, foldback diagrams,
  a choice matrix and a narrative review checklist.
