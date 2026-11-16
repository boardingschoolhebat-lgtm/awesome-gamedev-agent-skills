---
name: game-architecture
description: >
  Structure game code: engine-agnostic core, composition over inheritance, state/scene boundaries,
  event bus, ECS vs OOP, data-driven content, update order, save boundaries, determinism and tests.
  Use when a game codebase is tangled, untestable, or hard to extend.
---

# Game architecture

Game code fails in familiar ways: one god object, update order by accident, content hardcoded,
and no way to test anything without launching the game. Architecture is about **boundaries**:
what owns state, who may mutate it, and what can run headless. This is a **compositional** skill:
pair with `save-systems`, `performance-optimization` and the engine skill.

## When to use

- Use when starting a game that will grow beyond a prototype, or refactoring a tangled one.
- Use when logic is untestable, content requires code changes, or update order causes bugs.

**When *not* to use:** a 48-hour jam prototype → `prototype-fast`; a tiny script → no extra
layers; performance-only work → `performance-optimization`.

## Layers

```text
engine/platform  ->  adapters  ->  game core (rules, state)  ->  presentation (views, UI)
```

- **Core** has no engine imports: rules, entities, stats, economy, save schema.
- **Adapters** translate input, rendering, audio, storage and time.
- **Presentation** reads state and sends intents; it does not own game rules.
- Dependencies point inward; the core knows nothing about the engine.
- This makes the core testable headless and portable across engines.

## Composition and ownership

- Prefer composition (components/behaviours) over deep inheritance trees.
- One owner per piece of state; everyone else reads or sends commands.
- Avoid singletons for game state; pass services explicitly or via a narrow context.
- Separate **data** (definitions) from **instances** (runtime state).
- Keep constructors cheap; do initialization in an explicit `init`/`onLoad`.

## Update order

```text
input -> intents -> simulation (fixed) -> events -> view interpolation -> render -> UI
```

- Fix the simulation step; render interpolation is presentation only.
- Document the order; accidental order is a bug factory (physics before input, UI before state).
- Use a single simulation tick for determinism; avoid `deltaTime` in rules.
- Defer structural changes (spawn/despawn) to a safe point in the tick.

## Events

- Use an event bus for **notifications** (damage, death, quest progress), not for core flow.
- Events are past tense, immutable and small; no return values.
- Avoid event chains that are hard to trace; critical flow stays explicit calls.
- Unsubscribe on destroy; leaked listeners are a common source of ghost behavior.
- For networked games, events that change state must be authoritative.

## ECS vs OOP

| Approach | Use when |
|----------|----------|
| OOP objects | small/medium games, clear hierarchies |
| Components | behaviours compose, many variants |
| ECS | thousands of entities, data-oriented performance |

- ECS is an implementation detail, not a requirement; do not rewrite a working game for it.
- If using ECS, keep data in arrays/structs and systems pure where possible.
- Mixed approaches are fine if ownership is clear.

## Data-driven content

- Definitions (units, items, levels) live in data files with a schema and validation.
- IDs are stable; content references IDs, not code symbols.
- Load and validate at build/startup; fail loudly with the file and field.
- Hot reload in development, immutable data in release.
- Version content and saves together.

## Save boundaries

- Save **state**, not objects or engine handles.
- One save schema module; version it and migrate on load.
- Separate persistent meta (unlocks) from run state.
- Test round-trip and old-version migration headless.

## Determinism

- Fixed tick, seeded RNG, stable iteration order, no wall-clock or frame-rate dependence.
- Avoid floating-point divergence across platforms if you need cross-play/replays.
- Log inputs/commands for replay; verify a checksum of state.
- Determinism makes bugs reproducible and tests meaningful.

## Testing

- Unit-test the core: damage, economy, progression, save migration.
- Headless simulation tests: run N ticks with scripted input, assert state.
- Golden tests for content validation and generated maps.
- A few integration tests per engine adapter; do not test rendering pixel-by-pixel.

## Performance boundaries

- Profile before architecture changes; measure the frame budget.
- Keep allocations out of the tick; pool frequently spawned objects.
- Separate hot data (positions) from cold data (names, descriptions).
- Do not optimize across a boundary you will need for clarity.

## Pitfalls

- **God object** → one class owns everything. Split by domain and ownership.
- **Engine in the core** → untestable, unportable. Add adapters.
- **Event spaghetti** → flow impossible to trace. Use events for notification only.
- **Accidental update order** → intermittent bugs. Document and test the order.
- **Hardcoded content** → designers need programmers. Move to data + schema.
- **Save the world** → serializing live objects. Save a schema.
- **Premature ECS** → complexity without need. Start with composition.
- **No headless tests** → every bug needs a launch. Test the core.
- **Mutable shared state** → action at a distance. Single ownership.
- **Delta-time rules** → non-deterministic outcomes. Fixed tick for simulation.

## Composition

- **Save:** `save-systems` for schema, migration and atomic writes.
- **Performance:** `performance-optimization` for profiling and data layout.
- **Netcode:** `multiplayer-netcode` for authority and determinism.
- **Editor tools:** `editor-tooling` for data validation and inspectors.
- **Engine skills:** keep APIs at the adapter edge.

## References

- Read `references/boundaries-events-and-tests.md` for a layer diagram, update-order contract,
  event rules, data schema and a headless test checklist.
