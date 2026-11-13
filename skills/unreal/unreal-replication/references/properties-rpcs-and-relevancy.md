# Properties, RPCs and relevancy (UE 5.8)

Depth for `unreal-replication`: the exact specifiers, how conditions and relevancy decide what a
client receives, and the tests that catch authority mistakes.

## API used by the skill

| API / specifier | Form | Notes |
|-----------------|------|-------|
| `bReplicates` | actor property | Opt the actor into replication. |
| `SetReplicateMovement` | `(bool)` | Replicate movement for engine-driven actors. |
| `SetIsReplicatedByDefault` | component method | Components replicate only when enabled. |
| `UPROPERTY(Replicated)` | property specifier | Replicate the value to clients. |
| `UPROPERTY(ReplicatedUsing = OnRep_X)` | property specifier | RepNotify on arrival. |
| `GetLifetimeReplicatedProps` | `(TArray<FLifetimeProperty>&) const` | Always call `Super` and register properties. |
| `DOREPLIFETIME` | `(Class, Property)` | No conditions. |
| `DOREPLIFETIME_CONDITION` | `(Class, Property, COND_*)` | Conditional replication. |
| `UFUNCTION(Server, Reliable, WithValidation)` | RPC specifier | Client → server; `_Implementation`/`_Validate`. |
| `UFUNCTION(Client, Reliable)` | RPC specifier | Server → owning client. |
| `UFUNCTION(NetMulticast, Unreliable)` | RPC specifier | Server → all relevant clients. |
| `HasAuthority()` | actor method | Server-side check. |
| `GetLocalRole()` | actor method | Authority/simulated/autonomous role. |
| `NetUpdateFrequency` | actor property | Property update rate. |
| `NetCullDistanceSquared` | actor property | Relevancy distance, squared. |
| `bAlwaysRelevant` | actor property | Replicate regardless of distance. |

## Replication conditions

| Condition | Who receives |
|-----------|--------------|
| `COND_None` | all relevant clients (default) |
| `COND_OwnerOnly` | the owning connection only |
| `COND_SkipOwner` | everyone except the owner |
| `COND_SimulatedOnly` | simulated proxies only (not the autonomous owner) |
| `COND_AutonomousOnly` | the autonomous proxy only |
| `COND_InitialOnly` | only in the initial bunch (spawn payload) |

Conditions apply per property; a property that is `COND_OwnerOnly` is still sent to a new owner
when ownership changes, and to late joiners if they are the owner.

## RPC rules

- Server RPCs require the caller to own the actor (its `PlayerController` connection). A Server RPC
  on a non-owned actor is dropped.
- `Reliable` RPCs are retried and ordered; `Unreliable` may be dropped. Use reliable for gameplay
  requests, unreliable for cosmetic bursts.
- `WithValidation` adds a `_Validate` function; return `false` to reject. Validation runs before
  `_Implementation`; keep it cheap.
- Multicast RPCs run on the server and all relevant clients; a client cannot initiate one.
- RPC parameters must be replicated types: primitives, `FVector`, `FRotator`, `FName`, `UObject*`
  (replicated reference), structs with `USTRUCT`, fixed arrays. Avoid large payloads.
- Do not use RPCs for continuous state; replicate a property instead. A per-tick RPC is a
  bandwidth and reliability problem.

## Spawn and relevancy

- The server spawns replicated actors; clients receive them if the class is replicated and the
  actor is relevant.
- Relevancy is driven by `NetCullDistanceSquared`, `bAlwaysRelevant`, `bOnlyRelevantToOwner`,
  owner/instigator relationships and `IsNetRelevantFor`.
- `NetUpdateFrequency` controls how often properties are considered; `MinNetUpdateFrequency`
  bounds the adaptive rate.
- Dormancy (`NetDormancy`) stops updates for static actors until explicitly flushed.
- `GameMode` is server-only. `GameState` and `PlayerState` are the replicated places for match and
  per-player data.

## RepNotify details

```cpp
UFUNCTION()
void OnRep_Health(float PreviousHealth);       // with previous value
UFUNCTION()
void OnRep_Health();                           // no parameter
UFUNCTION()
void OnRep_Health(const float& PreviousHealth); // const reference
```

- The server does **not** call RepNotify when it changes the value; call it manually if the server
  needs the same side effect.
- RepNotify runs when the value arrives from the server, including on the listen server's local
  client if it is replicated to it.
- Do not put gameplay-authoritative logic in RepNotify only; the server must also run it (damage,
  death, rewards).

## Bandwidth tuning

| Knob | Effect |
|------|--------|
| `NetUpdateFrequency` | how often properties are sent; lower for ambient actors |
| `MinNetUpdateFrequency` | floor for adaptive updates |
| `NetCullDistanceSquared` | relevancy radius (squared); smaller = less bandwidth |
| `bAlwaysRelevant` | never culled; use only for match-critical actors |
| `bOnlyRelevantToOwner` | private actors (inventory, UI) |
| `NetDormancy` | stop updates for static actors |
| Conditions | send a property only to who needs it |

Measure with `stat net`, the Network Profiler and `net.NetShowCorrections` where relevant.

## Test checklist

1. Two clients + dedicated server: replicated values match on all peers.
2. Late join: current health/score/ammo correct, no replayed effects.
3. Server RPC from the owner works; from a non-owner does nothing.
4. `_Validate` rejects malformed input without crashing.
5. Client edits a replicated property: the server value wins on the next update.
6. Multicast effect appears on all clients once, including the listen server.
7. Distance culling: leave the relevancy radius and confirm updates stop, return and resync.
8. Ownership change: `COND_OwnerOnly` data follows the new owner.
9. Bandwidth: `stat net` within budget at the target player count.
10. Packaged dedicated server: `GameMode` logic runs, `GameState` replicates, no client-only
    assumptions.
