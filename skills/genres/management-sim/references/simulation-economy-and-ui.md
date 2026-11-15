# Simulation, economy and UI

Depth for `management-sim`: ticks, needs, budget and save.

## Tick design

```text
sim_tick = 5 Hz (0.2 s)      # agents, production
economy_tick = 1 per in-game day/week
render = every frame, interpolate positions
speed multiplier scales sim time, never tick logic
```

- Run the same tick function headless in tests.
- Clamp catch-up after a hitch; do not simulate 10 minutes in one frame.

## Needs table (example)

| Need | Decay/min | Satisfier | Radius |
|------|-----------|-----------|--------|
| Food | 4 | shop | 300 m |
| Rest | 2 | home | — |
| Health | 1 | clinic | 500 m |
| Fun | 3 | park | 400 m |

- Satisfy by priority; if unreachable, mark the agent "unhappy" and surface it.
- Aggregate happiness as a distribution, not only an average.

## Budget math

```text
balance = income - upkeep - wages - construction
income = tax_rate * taxable_value * occupancy
upkeep = sum(building.upkeep)
```

- Show a 12-period history; forecast next period.
- Loans: principal, interest, term; bankruptcy when balance < debt service and no credit.

## Save schema

```json
{
  "v": 3,
  "time": { "day": 42, "tick": 1200 },
  "grid": { "w": 64, "h": 64, "cells": "base64" },
  "buildings": [{ "id": 1, "type": "house", "x": 4, "y": 7, "level": 2 }],
  "agents": { "count": 320, "aggregates": { "happy": 210, "unhappy": 110 } },
  "budget": { "balance": 12000, "tax_rate": 0.12 },
  "rng_seed": 987654
}
```

- Store aggregates when individual agents are not gameplay-relevant.
- Never store rendered state; recompute it.

## Test checklist

1. Sim runs headless and produces the same result from the same seed.
2. Pause and 4× speed do not change outcomes per in-game day.
3. Every need has a satisfier and a visible failure.
4. Budget sheet reconciles with building upkeep and income.
5. Bankruptcy has a recovery path.
6. Placement preview matches the committed result.
7. Long lists virtualize; overlays have legends.
8. Save/load restores grid, buildings, agents and budget.
9. Old save version migrates.
10. Disasters are optional and telegraphed.
