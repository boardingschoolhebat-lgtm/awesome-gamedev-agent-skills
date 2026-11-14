---
name: multiplayer-netcode
description: >
  Cross-engine multiplayer netcode: authority models, tick and snapshot loops, client-side
  prediction and reconciliation, entity interpolation, lag compensation, relevance, reliability
  channels, and anti-cheat. Use for online co-op/PvP, desyncs, rubber-banding, or hit validation.
---

# Multiplayer netcode

Netcode is a time-travel problem: the server owns the truth, clients act now, and everyone must
agree on what happened. This skill is the cross-engine model; engine skills provide transport and
RPC APIs. It is **compositional**: pair with `godot-multiplayer`, `unity-networking`,
`unreal-replication` or `roblox-networking`.

## When to use

- Use when adding online play, fixing desync/rubber-banding, or validating hits server-side.
- Use when choosing between client prediction, interpolation delay, or rollback.

**When *not* to use:** local split-screen (no network); turn-based async play (simple
request/response is enough); pure leaderboard uploads → backend HTTP.

## Pick the model first

| Model | Authority | Good for | Cost |
|-------|-----------|----------|------|
| Relay / lockstep | deterministic peers | RTS, fighting (with rollback) | determinism, cheating |
| Server-authoritative | server | shooters, MMO, co-op | prediction needed |
| Client-authoritative | client | casual co-op, sandbox | trivially cheatable |
| Hybrid | server for currency/hits, client for movement | most indie games | complexity |

Default: **server-authoritative for anything competitive or economic**, client-side prediction for
responsiveness.

## The loop

```text
client tick:
  sample input -> command(seq++) -> send (unreliable, redundant last N)
  apply command locally (prediction)
  store command + resulting state

server tick:
  receive commands -> simulate authoritative state -> snapshot(ack_seq)
  broadcast snapshot (unreliable) + reliable events

client on snapshot:
  drop commands <= ack_seq
  set state = snapshot.state
  replay stored unapplied commands (reconciliation)
  smooth visual error over a few frames
```

- Input commands carry a **sequence number**; snapshots carry the last processed sequence.
- Redundancy (send last 3 commands) hides packet loss without TCP head-of-line blocking.
- State updates go unreliable/fast; spawns, chat, purchases go reliable.

## Interpolation (remote entities)

```text
render_time = now - interpolation_delay   (typically 100 ms, 2 snapshots)
pose = lerp(prev_snapshot, next_snapshot, (render_time - prev_time) / interval)
```

- Interpolate *between* received snapshots; extrapolate only briefly (and carefully).
- A larger delay hides jitter but adds input-to-visual lag for others.
- Interpolate position, rotation; snap for teleports.

## Lag compensation (hitscan)

```text
command_time = server_now - packet_latency - client_interpolation_delay
rewind other players to command_time (history ~1 s)
test the shot against those positions
```

- Keep ~1 s of hitbox history; rewind only what the shooter could see.
- Cap rewind (e.g. 200–250 ms) to limit "shot behind cover" exploits.
- Projectiles: server-simulated, not rewound.

## Prediction and reconciliation details

- Simulation must be deterministic enough to replay: same inputs → same state.
- Keep the state small and serializable: position, velocity, timers, cooldowns.
- On mismatch, replay unacknowledged commands; never re-apply acknowledged ones.
- Smooth the correction: if the error is large, snap; if small, blend over 100–200 ms.
- Cooldowns/ammo are server-authoritative; predict visually but confirm.

## Relevance and bandwidth

- Interest management: send only entities near the player (grid/cell or radius).
- Delta compression: send changed fields against a baseline the client acknowledges.
- Quantize: positions in cm, angles in 16-bit; do not send floats you do not need.
- Budget: measure bytes/s per player at target player count; snapshot rate is a dial.
- Prioritize: nearby, visible, and recently-changed entities first.

## Reliability and ordering

- Unreliable: snapshots, inputs, voice.
- Reliable ordered: spawn/despawn, inventory, purchases.
- Reliable unordered: chat, analytics.
- Never mix: a lost reliable packet must not stall movement updates — separate channels.

## Anti-cheat baseline

- Never trust client position, damage, currency, or cooldowns.
- Validate rate of fire, movement speed, and line of sight server-side.
- Server owns loot rolls and economy writes (see `game-economy`).
- Log anomalies; rate-limit RPCs; kick on impossible states.
- Client prediction is a UX feature, not a security boundary.

## Engine bindings

**Godot** — `multiplayer_peer`, `@rpc("any_peer", "call_local", "reliable")`, authority checks:

```gdscript
@rpc("any_peer", "call_local", "unreliable")
func submit_input(seq: int, move: Vector2) -> void:
    if not multiplayer.is_server(): return
    if peer_id != multiplayer.get_remote_sender_id(): return
    ...
```

- `set_multiplayer_authority()` per node; server validates.
- Use `MultiplayerSynchronizer` for state, but do not rely on it for competitive hit validation.

**Unity (Netcode for GameObjects)** — `NetworkBehaviour`, `ServerRpc`, `NetworkVariable<T>`,
`NetworkTransform`; server checks `IsServer`/`IsOwner`.

**Unreal** — replicated properties with `RepNotify`, `Server` RPCs with `WithValidation`,
`NetMulticast` for cosmetics; `NetUpdateFrequency` and relevancy.

**Roblox** — RemoteEvents to server, server-owned values; `RemoteFunction` sparingly.

## Testing

- Simulate 100–200 ms RTT, 2–5 % loss, jitter; play a full match.
- Two clients + server locally; verify both see the same hits, deaths, scores.
- Kill/restart the client mid-match; reconnect restores state.
- Packet capture: check bytes/s and that reliable traffic is not blocking snapshots.
- Bot load test at target player count.

## Pitfalls

- **Rubber-banding** → reconciling too aggressively or replaying acknowledged inputs.
- **Input lag** → no prediction; every action waits a round trip.
- **Desync** → non-deterministic simulation (engine physics, random, frame delta).
- **Teleporting enemies** → no interpolation, or extrapolation past a cap.
- **"Shot behind cover"** → no lag compensation; or rewind too far.
- **Cheaters** → client-authoritative health/currency.
- **Bandwidth spikes** → full snapshots to everyone; add relevance and delta.
- **Reliable channel stalls** → chat on the same channel as movement.
- **Double actions** → input applied locally and again from server without sequence checks.
- **Clock trust** → using client timestamps for authority; use server time.

## Composition

- **Transport/engine:** `godot-multiplayer`, `unity-networking`, `unreal-replication`,
  `roblox-networking`.
- **Determinism:** `physics-tuning` (fixed step), `fighting-game` (rollback).
- **Economy security:** `game-economy`, `roblox-datastores`.
- **UI:** latency/ping display, reconnect flow.

## References

- Read `references/prediction-reconciliation-and-lag-compensation.md` for the command/snapshot
  protocol, reconciliation pseudocode, rewind math and a netcode test matrix.
