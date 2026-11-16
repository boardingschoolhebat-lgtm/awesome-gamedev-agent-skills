---
name: 4x-game
description: >
  Design a 4X strategy game: explore/expand/exploit/exterminate turns, map generation, cities and
  yields, tech and civics trees, units and combat, diplomacy, victory conditions, AI and late-game
  pacing. Use for a turn-based empire builder.
---

# 4X game

A 4X is a long-horizon optimization game: explore the unknown, expand, exploit the map, and
exterminate or outlast rivals. The design problem is **decision density over time** — the first
turn should matter, and the last turn should not be a click-through. This is a **compositional**
skill: pair with `game-economy`, `game-ai` and `ui-architecture`.

## When to use

- Use when designing a turn-based empire/civilization game with cities, tech and diplomacy.
- Use when the late game drags, the AI is passive, or victory is a foregone conclusion.

**When *not* to use:** real-time strategy → `rts-game`; city builder without rivals →
`management-sim`; tactical squad game without empire layer → `level-design`/`combat-design`.

## Core loop

```text
explore -> settle -> improve -> research -> negotiate/fight -> victory
```

- Each turn should offer a meaningful choice, not only "next turn".
- The map is the main content: terrain, resources, chokepoints, neighbors.
- Victory conditions define the strategies; without them, the game is a sandbox.

## Turn structure

| Phase | Player action | Automation |
|-------|---------------|------------|
| Start | resolve yields, events | auto |
| Move | units, scouts | auto-move |
| Build | cities, queues | production queue |
| Research | tech/civic choice | queue |
| Diplomacy | trade, treaties, war | AI proposals |
| End | confirm, AI turns | fast-forward |

- Keep end-turn short; batch notifications and let the player act from the report.
- Auto-explore and auto-move reduce late-game clicks; allow override.
- Simultaneous turns only in multiplayer, with a clear resolution order.

## Map and exploration

- Generate with a guaranteed start: food, production, a settle spot, and a neighbor at distance.
- Fog of war: unexplored, seen, visible; scouts reveal.
- Terrain yields and features create settlement choices; avoid one dominant tile.
- Chokepoints and continents shape early war and expansion.
- Map size and rival count are difficulty knobs, not only numbers.

## Cities and yields

```text
city yields = terrain + buildings + population + policies - upkeep
growth: food surplus -> population -> more tiles
production: hammers -> buildings/units
science/culture/faith/gold: parallel currencies with distinct sinks
```

- Each city needs a reason to exist: resource, chokepoint, port, holy site.
- Distinguish tall (few, developed) vs wide (many, cheap) strategies.
- Housing/amenities/upkeep prevent infinite sprawl.
- Queue UI must show turns remaining and allow reordering.

## Tech and civics

- Two trees (science/culture) create competing priorities; do not make one strictly better.
- Techs unlock verbs (units, buildings, abilities), not only +10 %.
- Eureka/inspiration boosts reward playing the game, but must not be mandatory.
- Avoid dead-end techs; every node needs a payoff or a path.
- Era transitions can raise costs and obsolete units; telegraph them.

## Units and combat

- Rock-paper-scissors of unit classes, terrain modifiers, ranged vs melee, siege vs walls.
- Stacking limits (one unit per tile, or armies) determine the war game.
- Combat resolution should be readable: strength, modifiers, predicted damage.
- Attrition and healing make wars costly; no infinite unit spam without upkeep.
- Barbarians/neutrals pressure early expansion without deciding the game.

## Diplomacy

- AI agendas are legible: expansionist, builder, aggressor, trader.
- Treaties: peace, trade, open borders, alliances; each has a cost and a duration.
- Diplomatic state must be visible: attitude, grievances, deals, war weariness.
- Betrayal needs telegraphing; random backstabs feel unfair.
- Victory conditions interact with diplomacy (shared science, cultural pressure).

## Victory and pacing

```text
domination / science / culture / religion / diplomacy / score
```

- At least three viable paths; each has a distinct late-game loop.
- Set a turn limit with score fallback; avoid infinite stalemates.
- Escalate eras with new decisions, not only bigger yields.
- Late-game micromanagement: queues, governors, auto-improve, rally points.
- A "one more turn" hook: a near-complete build/research/objective each turn.

## AI

- AI must expand, research, build and fight competently; bonuses should be disclosed.
- Use the same rules where possible; cheat via difficulty modifiers, not omniscience.
- Tactical AI: defend cities, mass units, retreat when losing.
- Diplomatic AI: remember treaties and grievances; avoid random flip-flops.
- Test AI vs AI at speed to find stalemates and runaway leaders.

## UI for data density

- Map overlays for yields, resources, danger, diplomacy.
- City screen: tiles, worked tiles, queue, specialists.
- Tech tree with search, current research, and path preview.
- End-turn report: what changed, what needs attention, click to jump.
- Tooltips explain modifiers; never hide the formula for combat.

## Pitfalls

- **Late-game drag** → too many clicks. Automate queues, governors, auto-move.
- **Runaway leader** → snowball with no catch-up. Maintenance, war weariness, coalitions.
- **Passive AI** → no pressure. Agendas, expansion, tactical aggression.
- **One viable victory** → solved meta. Balance paths and make them interact.
- **Dead techs** → false choices. Every node unlocks a verb or a clear bonus.
- **Infinite city spam** → no upkeep. Housing, amenities, corruption.
- **Unreadable combat** → hidden math. Show predicted damage and modifiers.
- **Map start luck** → unwinnable starts. Guarantee food/production/settle.
- **Diplomacy whiplash** → random betrayal. Telegraph and remember.
- **No turn-one decision** → slow opening. Give a scout, a settler choice, a rival.

## Composition

- **Economy:** `game-economy` for yields, costs, inflation and sinks.
- **AI:** `game-ai` for strategic/tactical layers and diplomacy.
- **UI:** `ui-architecture` for data-dense screens and overlays.
- **Procedural:** `procedural-gen` for maps and starts.
- **Save:** `save-systems` for long campaigns and versioned state.
- **Multiplayer:** `multiplayer-netcode` for simultaneous turns.

## References

- Read `references/turns-economy-and-victory.md` for a turn loop, yield tables, tech pacing,
  diplomacy state, AI checks and a 4X test checklist.
