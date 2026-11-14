---
name: quest-design
description: >
  Design data-driven quests: objective types, state machines, prerequisites, tracking events,
  journal UI, rewards, branching and failure, persistence, and anti-softlock rules. Use for
  quest/mission systems, objective tracking, or quests that break on reload.
---

# Quest design

A quest is a small state machine plus a set of world conditions. Data-driven quests survive
content growth; hard-coded quest scripts do not. This is a **compositional** skill: pair it with
`dialogue-systems`, `save-systems` and the engine UI skill.

## When to use

- Use when building a quest/mission system, objective tracking, or a journal.
- Use when quests duplicate rewards, softlock, or lose progress on reload.

**When *not* to use:** a linear level with a single goal → level scripting; dialogue-only story
without objectives → `dialogue-systems`; daily login rewards → `game-economy`.

## Data model

```json
{
  "id": "q_smith_01",
  "title_key": "quest.smith.title",
  "giver": "npc_smith",
  "prerequisites": ["q_intro_done"],
  "objectives": [
    { "id": "ore", "type": "collect", "target": "iron_ore", "count": 5 },
    { "id": "return", "type": "talk", "target": "npc_smith" }
  ],
  "rewards": { "gold": 100, "items": ["pickaxe_iron"], "xp": 250 },
  "turn_in": "npc_smith"
}
```

- Objectives are ordered or parallel — state which, explicitly.
- Every player-facing string is a localization key.
- Rewards are data, granted once, server-side where multiplayer.

## State machine

```text
unavailable --prereqs met--> available
available --accept--> active
active --all objectives--> ready_to_turn_in
ready_to_turn_in --turn in--> completed
active --fail condition--> failed
completed --claimed--> turned_in   (reward granted exactly once)
```

- Persist `state`, per-objective counters, and `reward_claimed`.
- Reloading must not re-grant rewards or reset counters.
- Failure should be recoverable (retry) unless the design says otherwise.

## Objective types

| Type | Event source | Notes |
|------|--------------|-------|
| kill | enemy death (id, count) | count only quest-relevant kills |
| collect | inventory change | do not consume on turn-in unless designed |
| talk | dialogue start/end | require the specific NPC |
| reach | trigger volume | one-shot flag |
| escort | NPC alive + zone | fail on NPC death |
| timed | timer | pause-aware |
| interact | object used | idempotent |

## Tracking patterns

### 1. Event-driven counters

```text
on_enemy_killed(enemy_id):
    for q in active_quests:
        for o in q.objectives where o.type == kill and o.target == enemy_id:
            o.progress = min(o.count, o.progress + 1)
    refresh_quest_states()
```

- One event bus; quests subscribe, not the combat code.
- Clamp progress to `count`; ignore events after completion.
- Batch UI updates; do not rebuild the journal per kill.

### 2. Collect objectives from inventory

- Query inventory on change and on load; do not rely on pickup events alone.
- Decide whether items are consumed at turn-in; show it in the UI.
- Quest items should be non-sellable/non-droppable, or re-obtainable.

### 3. Turn-in and rewards

```text
if state == ready_to_turn_in and dialogue_with(turn_in):
    grant(rewards)
    state = turned_in
    reward_claimed = true
```

- Guard with `reward_claimed` to prevent double grants on reconnect/reload.
- Grant atomically with the state change (same save write / server transaction).

## UI

- Journal: active/completed tabs, tracked quest, objective checklist with counts.
- World markers: giver `!`, turn-in `?`, tracked objective waypoint.
- Toast on objective progress; do not interrupt combat with modal dialogs.
- Show prerequisites as locked entries ("requires level 5") instead of hiding them.

## Branching and failure

- Branch on quest flags, not on item possession alone (items can be lost).
- Mutually exclusive quests need explicit locks so both cannot complete.
- Timed quests: pause with the game; show remaining time.
- Escort: leash distance, teleport catch-up, fail only on death.

## Anti-softlock rules

1. Quest NPCs essential or respawnable.
2. Quest items re-obtainable (respawn, vendor, recovery chest).
3. No objective that depends on a one-time world event without a fallback.
4. Failure states always offer retry/abandon.
5. Abandoning returns the quest to `available`, not a dead end.

## Persistence

- Save quest state by stable `id`, never by array index.
- Version migrations: unknown quest ids are ignored, missing ones re-added as available.
- Store counters as integers; avoid floats for progress.
- Test save/load mid-objective, after turn-in, and after abandoning.

## Pitfalls

- **Objectives complete out of order** → no ordering rule; define parallel vs sequential.
- **Kill counted twice** → event fired on both server and client, or on reload.
- **Reward duplication** → no `reward_claimed` guard; reconnect re-triggers turn-in.
- **Quest item sold** → not flagged as quest item; add recovery path.
- **Dead giver** → NPC can be killed; make essential or move turn-in.
- **Invisible prerequisites** → player cannot tell why the quest is unavailable.
- **Journal spam** → rebuild on every event; update incrementally.
- **Localization breakage** → concatenated strings; use full keys with placeholders.
- **Save corruption on content update** → quest removed/renamed; migrate by id.

## Composition

- **Dialogue:** `dialogue-systems` for accept/turn-in conversations and conditions.
- **Save:** `save-systems` for quest state, counters, migrations.
- **UI:** `game-ui-ux` + engine UI skill for journal, markers, toasts.
- **World:** `level-design` for objective placement and waypoints.
- **Economy:** `game-economy` for reward values and inflation.
- **Multiplayer:** `multiplayer-netcode` for server-owned quest state.

## References

- Read `references/quest-data-and-state.md` for a full schema, event bus pseudocode, save
  migration rules and a quest test checklist.
