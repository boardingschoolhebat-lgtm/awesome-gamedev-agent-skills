# Quest data and state

Depth for `quest-design`: schema, events, save rules and tests.

## Schema

```json
{
  "id": "q_smith_01",
  "title_key": "quest.smith.title",
  "desc_key": "quest.smith.desc",
  "giver": "npc_smith",
  "turn_in": "npc_smith",
  "prerequisites": ["q_intro_done"],
  "parallel_objectives": true,
  "objectives": [
    {"id": "ore", "type": "collect", "target": "iron_ore", "count": 5,
     "desc_key": "quest.smith.ore"},
    {"id": "return", "type": "talk", "target": "npc_smith", "count": 1}
  ],
  "rewards": {"gold": 100, "xp": 250, "items": ["pickaxe_iron"]},
  "fail": {"type": "npc_death", "target": "npc_smith"}
}
```

## Runtime state

```json
{
  "id": "q_smith_01",
  "state": "active",
  "progress": {"ore": 3, "return": 0},
  "reward_claimed": false,
  "accepted_at": 1710000000,
  "tracked": true
}
```

- Stable ids only; never array indices.
- `progress` keys must match objective ids.
- Unknown objectives in old saves are dropped; missing ones default to 0.

## Event bus

```text
emit("enemy_killed", {id, count})
emit("item_added", {id, count})
emit("dialogue_finished", {npc})
emit("zone_entered", {zone})
emit("object_used", {id})
```

```text
for quest in active:
    for objective in quest.objectives:
        if matches(objective, event):
            objective.progress = clamp(progress + event.count, 0, objective.count)
    update_state(quest)   # active -> ready_to_turn_in when all complete
```

- Match on type + target; ignore events for completed quests.
- One emission per gameplay event; debounce duplicates from load/replication.

## Rewards

- Grant inside the same transaction as `state = turned_in`.
- Idempotency key: quest id + character id.
- Never grant from the client in multiplayer; server validates completion.
- Show a reward summary before claiming so the player knows what they get.

## Save migration

```text
load(save):
    for entry in save.quests:
        defn = quest_db.get(entry.id)
        if not defn: drop(entry)                 # content removed
        else: merge(defaults(defn), entry)       # new objectives default 0
    for defn in quest_db where not in save:      # new content
        if defn.auto_start: add available
```

- Keep a schema version; migrate step by step.
- Never rewind `turned_in` quests to `active`.
- Back up the save before migration in development builds.

## Test checklist

1. Accept, progress, complete, turn in — reward once.
2. Save/load mid-objective keeps counters.
3. Reload at turn-in does not duplicate rewards.
4. Two kill events in one frame count correctly.
5. Collect objective updates from inventory on load.
6. Abandon returns to available and clears progress.
7. Failure path is recoverable.
8. Quest item loss has a recovery route.
9. Journal shows locked quests with a reason.
10. Removed/renamed quests do not corrupt the save.
