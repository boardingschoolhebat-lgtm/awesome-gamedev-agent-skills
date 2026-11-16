# Turns, economy and victory

Depth for `4x-game`: yields, pacing, AI and tests.

## Turn budgets

| Era | Turns | New decision |
|-----|-------|--------------|
| Ancient | 1–75 | settle, scout, first tech |
| Classical | 76–150 | religion, first war |
| Medieval | 151–225 | alliances, wonders |
| Industrial | 226–300 | ideology, railroads |
| Modern | 301–400 | victory race |

- Tune to 200–400 turns for a 10–20 hour game.
- Every era adds a system or a stronger version of one; do not only scale numbers.

## Yield table (starting point)

| Terrain | Food | Production | Gold |
|---------|------|------------|------|
| Grassland | 2 | 0 | 0 |
| Plains | 1 | 1 | 0 |
| Hills | 1 | 2 | 0 |
| Forest | 1 | 2 | 0 |
| River | +1 gold adjacency | — | — |

- A city needs ~2 food per pop and enough production to finish a building in <15 turns.
- Special resources give a reason to settle; distribute them fairly.

## Tech pacing

```text
tier cost = base * growth^tier
research turns = cost / science_per_turn
```

- Target 8–15 turns per tech early, 5–10 later.
- Eureka boosts 20–40 %, optional but rewarding.
- Keep the tree width small enough that choices matter.

## Diplomacy state

```text
attitude: -100..100
grievances: list<{source, amount, turn}>
treaties: list<{type, expires}>
war_weariness: 0..100
```

- Attitude drives offers; grievances decay slowly; treaties expire visibly.
- AI should declare war with a reason and a buildup, not at random.

## AI checks

1. Expands to a reasonable city count by turn 100.
2. Researches toward a victory path, not randomly.
3. Defends its cities and retreats losing armies.
4. Accepts/declines trades consistently with attitude.
5. Does not see through fog.
6. AI-vs-AI games end before the turn limit, with varied winners.

## Test checklist

1. Turn one has a meaningful choice.
2. Every yield has a source and a sink.
3. Tall and wide are both viable.
4. Techs unlock verbs, not only percentages.
5. Combat preview matches resolution.
6. Diplomacy state is visible and consistent.
7. At least three victory paths are viable.
8. Late-game automation works and can be overridden.
9. Save/load a 200-turn campaign without drift.
10. AI-vs-AI produces varied, completed games.
