# Boundaries, events and tests

Depth for `game-architecture`: contracts and checks.

## Layer contract

```text
core/        no engine imports; rules, state, schema
adapters/    input, render, audio, storage, clock
presentation/ scenes, views, UI; reads state, sends intents
```

- A dependency from core to adapters is a bug; enforce with a lint/import check.
- Core exposes commands (`Move`, `Attack`) and queries (`CanAttack`), not engine nodes.

## Update-order contract

```text
1. poll input -> intents
2. apply intents (validate)
3. fixed simulation ticks
4. resolve events/deaths/spawns
5. update views (interpolate)
6. render
7. UI (reads state)
```

- Write this in the README and test it with a scripted sequence.
- Structural changes happen at step 4, never mid-iteration.

## Event rules

```text
name: past tense ("unit_died")
payload: ids + minimal data
immutable, no return value
subscribers unsubscribe on destroy
```

- Events notify; commands decide. Do not implement core flow as an event chain.
- Log events in debug builds to trace cause and effect.

## Data schema example

```json
{
  "id": "unit_archer",
  "hp": 60,
  "damage": 12,
  "range": 4,
  "cost": { "gold": 40, "wood": 20 },
  "tags": ["ranged", "human"]
}
```

- Validate: required fields, positive numbers, known tags, unique ids.
- Fail at load with file + field; never silently default gameplay values.

## Headless test checklist

1. Core builds and runs without the engine.
2. Damage/economy/progression have unit tests.
3. 1,000 scripted ticks produce the same state twice (determinism).
4. Save/load round-trips; old schema migrates.
5. Content schema rejects bad data with a clear error.
6. Update order is covered by an integration test.
7. Events unsubscribe on destroy (no ghost listeners).
8. One adapter smoke test per platform path.
9. Profile shows no per-tick allocations in hot paths.
10. Import check forbids core → engine dependencies.
