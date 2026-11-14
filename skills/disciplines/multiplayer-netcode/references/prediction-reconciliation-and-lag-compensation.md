# Prediction, reconciliation and lag compensation

Depth for `multiplayer-netcode`: protocol, replay loop, rewind math and tests.

## Command/snapshot protocol

```text
Command:  { seq, tick, input_bitmask, aim, dt }
Snapshot: { server_tick, ack_seq, entities: [id, pos, vel, state, anim] }
Event:    { id, type, payload }   // reliable
```

- Client sends commands at its tick rate, with the last 3 commands repeated.
- Server buffers commands, simulates in tick order, acks the last applied `seq`.
- Snapshot rate can be lower than the tick rate (e.g. 20 Hz snapshots, 60 Hz simulation).
- Clients must tolerate duplicate and out-of-order commands (dedupe by `seq`).

## Reconciliation pseudocode

```text
on_snapshot(s):
    if s.ack_seq <= last_ack: return          # stale
    last_ack = s.ack_seq
    state = s.state
    for cmd in pending where cmd.seq > s.ack_seq:
        state = simulate(state, cmd)
    predicted = state
    error = predicted.pos - rendered.pos
    if |error| > snap_threshold: rendered.pos = predicted.pos
    else: smooth rendered.pos toward predicted.pos over 150 ms
    drop pending where seq <= s.ack_seq
```

- `simulate` must be the same function on client and server.
- Never resimulate acknowledged commands; that doubles movement.
- Keep `pending` bounded (e.g. 1 s); drop oldest on overflow.

## Rewind math

```text
latency        = (server_recv_time - client_send_time)   # per command, smoothed
interp_delay   = client's render delay (e.g. 100 ms)
rewind_to      = server_now - latency - interp_delay
```

- Store hitbox transforms each tick in a ring buffer (1 s at 60 Hz = 60 entries).
- Rewind only players, not the world; clamp `rewind_to` to max 250 ms.
- Restore transforms after the trace.
- Validate line of sight at the rewound positions, not current ones.

## Interpolation buffer

```text
buffer snapshots sorted by server_tick
render_tick = newest_tick - interp_ticks
find a,b bracketing render_tick
alpha = (render_tick - a.tick) / (b.tick - a.tick)
pos = lerp(a.pos, b.pos, alpha)
```

- If the buffer underruns, hold the last pose briefly; do not extrapolate far.
- If it overruns (lag spike), drop old snapshots and snap.

## Test matrix

| Scenario | Expected |
|----------|----------|
| 0 ms, 0 % loss | no visible correction |
| 100 ms RTT | prediction hides own lag; remotes smooth |
| 200 ms RTT + 5 % loss | no rubber-banding; hits validate |
| 10 % packet loss | redundant commands cover gaps |
| Jitter 50 ms | interpolation absorbs; no stutter |
| Client hitch 500 ms | clamp dt, catch up without teleporting others |
| Reconnect | full state restore, no duplicate inventory |
| Two clients shoot same tick | deterministic winner or trade |

## Security checks

- Reject commands with impossible `dt`, speed, or fire rate.
- Server computes damage and loot; client predicts only visuals.
- Rate-limit RPCs per second per peer.
- Never accept client-provided currency, item IDs, or prices.
