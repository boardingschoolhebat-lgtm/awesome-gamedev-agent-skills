---
name: management-sim
description: >
  Build a management/city-builder sim: simulation ticks, agent needs and pathing, economy and
  budgets, build/placement tools, data-dense UI, failure states and save/load of the simulated
  world. Use for a tycoon, city builder, park, hospital or colony management game.
---

# Management sim

A management sim is a simulation the player steers with policy: build, price, staff, expand.
The fun is watching a system respond and diagnosing why it did not. This is a **compositional**
skill: pair with `game-economy`, `game-ui-ux` and `save-systems`.

## When to use

- Use when building a tycoon/city/colony/management game with simulated agents and budgets.
- Use when the sim is opaque, the UI is unreadable, or saves break on load.

**When *not* to use:** idle/incremental with no spatial simulation → `idle-incremental`; RTS with
armies → `rts-game`; survival crafting → `survival-crafting`.

## Core loop

```text
observe -> diagnose -> build/adjust policy -> simulate -> measure -> repeat
```

- The player must see *why* numbers move; feedback beats realism.
- Every system needs a visible input, throughput and output.

## Simulation architecture

```text
world grid/zones -> agents (needs, pathing) -> services (jobs, housing, health)
      |                    |                          |
   economy <--------- statistics <--------------- events/log
```

- Fixed tick for simulation (e.g. 4–20 Hz), render every frame.
- Separate simulation state from view; the sim must run headless for tests.
- Use an event log for "what happened" (opened, hired, went bankrupt).
- Time controls: pause, 1×, 2×, 4×; simulation must be stable at the fastest speed.

## Agents and needs

| Need | Satisfier | Failure |
|------|-----------|---------|
| Housing | residential zone | homelessness, leaving |
| Work | jobs nearby | unemployment, crime |
| Food | shops/farms | hunger, health drop |
| Health | clinic | death, productivity loss |
| Fun | park/service | happiness drop |

- Needs decay at different rates; satisfy the most urgent first.
- Pathfinding on a road/grid graph; cache paths, recompute on network change.
- Agents are a sample, not every citizen, if scale demands it — but be consistent.

## Economy and budget

- Income: taxes/fares/sales; expenses: upkeep, wages, construction.
- Loans and bonds add a failure/recovery loop; bankruptcy must be recoverable.
- Show a monthly/weekly balance sheet, not just a running total.
- Demand curves (residential/commercial/industrial) drive growth; cap runaway feedback.
- Inflation/land value can add depth, but only if surfaced.

## Building and placement

- Grid or free placement with snapping; show valid/invalid before commit.
- Roads/utilities connect; preview coverage (water, power, service radius).
- Demolish/upgrade with refunds and confirmation for expensive actions.
- Undo for placement in pause mode; not for time that already simulated.

## UI for data density

- One screen per question: budget, population, traffic, services.
- Sparklines and deltas beat raw totals; color + icon + label (not color alone).
- Alerts are actionable: click to jump to the problem.
- Overlays for coverage/heatmaps; legend always visible.
- Search/filter for lists (buildings, citizens) and virtualize long lists.

## Failure and difficulty

- Failure states: bankruptcy, mass exodus, disaster. Offer recovery or a clear restart.
- Disasters should be optional or difficulty-gated.
- Sandbox mode with unlimited money for building.
- Scenario goals (population, profit, happiness) teach the systems.

## Save/load

- Serialize the full simulation: grid, agents (or aggregates), budget, time, policies.
- Version the schema; migrate old saves; test load at different tick rates.
- Deterministic RNG seeded and saved, so reload does not reroll outcomes.
- Autosave on a schedule and before disasters.

## Pitfalls

- **Opaque simulation** → players cannot diagnose. Surface causes and deltas.
- **Runaway feedback** → demand or land value explodes. Add caps and sinks.
- **Traffic collapse** → agents use one road. Multiple routes, public transit, lane logic.
- **UI wall of numbers** → no decisions. One question per screen, sparklines.
- **Sim speed changes outcomes** → tick-rate-dependent logic. Fixed tick, scale time.
- **Save bloat** → serializing every citizen with full history. Aggregate or prune.
- **Unrecoverable bankruptcy** → dead save. Loans, grants, or a restart path.
- **Disaster spam** → exhausting. Optional, telegraphed, counterable.
- **Buildings with no purpose** → cosmetic sprawl. Each service has a need and a cost.

## Composition

- **Economy:** `game-economy` for sinks/faucets, pricing, inflation.
- **UI:** `ui-architecture` + `game-ui-ux` for dashboards and overlays.
- **AI/pathing:** `game-ai` for agents and service routing.
- **Save:** `save-systems` for a versioned simulation snapshot.
- **Level design:** `level-design` for map layout and resource placement.

## References

- Read `references/simulation-economy-and-ui.md` for tick design, needs tables, budget math,
  save schema and a management-sim test checklist.
