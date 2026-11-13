# Authority, RPCs and testing (NGO 2.x, Unity 6.3)

Depth for `unity-networking`: the permission rules, the spawn flow, and the tests that expose
desyncs before players do.

## API used by the skill

| API | Form | Notes |
|-----|------|-------|
| `NetworkManager.Singleton` | property | One per game; owns transport, prefabs, scenes. |
| `NetworkManager.StartHost/StartServer/StartClient` | `bool` | Start the chosen role. |
| `NetworkObject.Spawn` | `()` / `SpawnWithOwnership(ulong)` | Server-only. |
| `NetworkManager.SpawnManager.InstantiateAndSpawn` | `(prefab, ownerClientId)` | Instantiate + spawn in one call. |
| `NetworkBehaviour.IsServer` | property | True on host and dedicated server. |
| `NetworkBehaviour.IsOwner` | property | True on the owning client (and host-owner). |
| `NetworkBehaviour.OwnerClientId` | property | Client id of the owner. |
| `NetworkVariable<T>` | `new(value, readPerm, writePerm)` | Replicated field with permissions. |
| `NetworkVariable.OnValueChanged` | `(T previous, T current)` | Subscribe in `OnNetworkSpawn`. |
| `[ServerRpc]` | method attribute | Name must end `ServerRpc`; runs on the server. |
| `[ClientRpc]` | method attribute | Runs on clients (all by default). |
| `ServerRpcParams` / `ClientRpcParams` | structs | Sender id / target client ids. |
| `NetworkTransform` | component | Replicates transform with interpolation. |
| `NetworkManager.SceneManager` | property | Synchronized scene loading. |

## Permissions

`NetworkVariableReadPermission`:

| Value | Who can read |
|-------|--------------|
| `Everyone` | all clients (default) |
| `Owner` | only the owning client |
| `Server` | only the server |

`NetworkVariableWritePermission`:

| Value | Who can write |
|-------|---------------|
| `Server` | server only (default; use this for gameplay state) |
| `Owner` | owner can write (use only for cosmetic/owner-owned state) |

Secret data (roles, hidden inventory) uses `ReadPermission.Owner`, not a `ClientRpc` broadcast.

## Ownership matrix

| Context | `IsServer` | `IsOwner` | `HasAuthority` (client-server) |
|---------|-----------|-----------|-------------------------------|
| Host, own player | true | true | true |
| Host, remote player | true | false | true |
| Client, own player | false | true | false |
| Client, remote player | false | false | false |
| Dedicated server, any | true | false | true |

Gate input/camera on `IsOwner`; gate authoritative changes on `IsServer`.

## Spawn flow

1. Server instantiates the prefab (registered in the prefabs list).
2. `NetworkObject.Spawn()` assigns a `NetworkObjectId` and replicates a spawn message.
3. Clients instantiate the same prefab and run `OnNetworkSpawn` on each `NetworkBehaviour`.
4. Initial `NetworkVariable` values are included in the spawn payload.
5. On despawn, `OnNetworkDespawn` runs; destroy the object on the server, clients follow.

Ordering notes:

- Dynamically spawned objects: `Awake` → `OnNetworkSpawn` → `Start`.
- In-scene placed objects: `Awake` → `Start` on the server, `OnNetworkSpawn` after the client
  synchronizes.
- `OnNetworkSpawn` runs again after a scene reload; subscribe/unsubscribe symmetrically in
  spawn/despawn callbacks.

## RPC rules

- Name: `DoThingServerRpc`, `DoThingClientRpc`; the suffix is mandatory.
- Server RPCs are sent by the owner by default (`RequireOwnership = true`). Set
  `RequireOwnership = false` only when any client may legitimately call it, and validate the
  sender with `ServerRpcParams.Receive.SenderClientId`.
- Client RPCs are server→clients. A client calling one is ignored or errors.
- RPC parameters must be serializable: primitives, `Vector3`, `NetworkObjectReference`,
  `INetworkSerializable` structs, fixed-size arrays. No `GameObject` or arbitrary class references.
- RPCs are reliable and ordered by default; do not send per-frame data through them. Use
  `NetworkVariable` or a custom `NetworkBehaviour` for continuous state.
- Effects: `ClientRpc`. Gameplay results: `NetworkVariable` + server validation.

## Latency and smoothing

- `NetworkTransform` sends at its configured rate; interpolation hides the gaps between updates.
- A character controller should replicate velocity/input and resolve movement on the server;
  client prediction needs reconciliation against the server's last acknowledged state.
- Use the transport's simulator (or `NetworkSimulator`) with 100–200 ms latency and 2–5 % loss;
  most desyncs are invisible on a LAN.
- The network tick rate (`NetworkManager.NetworkConfig.TickRate`) trades bandwidth for
  responsiveness; test at the shipping value.

## Security checklist

- Server validates every RPC: ownership, value range, cooldown, distance, line of sight, game
  phase.
- Never send the server's authoritative position and accept it back from a client.
- Do not put secrets in `NetworkVariable`s with `Everyone` read permission.
- Rate-limit RPCs per client; a spammed RPC is a denial-of-service vector.
- Client-side UI can lie; the server recomputes costs, damage and rewards.

## Test checklist

1. Host + one client: both see each other spawn, move, take damage and die.
2. Late join mid-match: full state (health, score, inventory) arrives correctly.
3. Disconnect the owner: the server cleans up its objects; other clients see them removed.
4. Latency 150 ms + 3 % loss: movement smooth, no rubber-banding beyond expected correction.
5. Spam a ServerRpc: the server rate-limits/ignores; no crash or duplicated effect.
6. Client moves its own transform directly: server rejects or corrects it.
7. Scene load: both peers load the same scene and spawns continue.
8. Build (not editor) with two machines: prefab hashes match, no missing prefab errors.
