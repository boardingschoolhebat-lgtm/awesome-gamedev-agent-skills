---
name: unity-networking
description: >
  Add server-authoritative multiplayer to Unity 6.3 with Netcode for GameObjects: NetworkManager
  and prefab registration, NetworkObject spawning and ownership, NetworkVariable permissions,
  ServerRpc/ClientRpc, NetworkTransform, latency handling and cheat-resistant validation. Use
  when a Unity game needs co-op or competitive multiplayer, networked state, RPCs, or fixes for
  desyncs, rejected RPCs and client-authority exploits. Targets Unity 6.3 LTS (6000.3) with
  Netcode for GameObjects 2.x.
---

# Unity networking (Netcode for GameObjects)

Make the server the only authority, replicate the minimum state, and send intent from clients
through RPCs the server validates. Targets **Unity 6.3 LTS (6000.3)** with **Netcode for
GameObjects 2.x**.

## When to use

- Use when adding co-op/competitive multiplayer, networked health, scores, items or movement.
- Use when a client cannot spawn objects, RPCs are rejected, NetworkVariables do not change, or
  players can cheat by moving their own character.

**When *not* to use:** single-player input → `unity-input-system`; physics tuning →
`unity-physics`; UI for a lobby → `unity-ui`; offline saves → `unity-save`; transport selection
and relay/lobby services are separate packages.

## Architecture first

```text
Client (owner)                    Server (host or dedicated)               Other clients
input ──ServerRpc──────────────▶ validate + apply state
                                  NetworkVariable ───────────────────────▶ replicate
                                  ClientRpc ─────────────────────────────▶ effects
```

- **Server authority:** the server owns health, score, inventory and spawns. Clients send
  *requests*, never results.
- **Ownership:** the server assigns a `NetworkObject` to a client (player objects). `IsOwner` is
  true on that client; `IsServer` is true on the host and on a dedicated server.
- **Replicate state, not events:** health is a `NetworkVariable`, a hit spark is a `ClientRpc`.
- **Predict locally, correct from the server:** client-side prediction is an optimisation on top
  of server truth, not a replacement for it.

## Core workflow

1. **Install and configure.** Add Netcode for GameObjects (and a transport), create a
   `NetworkManager` in the scene, assign the transport and the `NetworkPrefabsList`.
2. **Make networked objects.** Every networked GameObject needs a `NetworkObject` and at least
   one `NetworkBehaviour`; put the `NetworkObject` on the prefab root and register the prefab in
   the prefabs list.
3. **Spawn on the server.** `Instantiate(prefab)` then `GetComponent<NetworkObject>().Spawn()`,
   or `NetworkManager.SpawnManager.InstantiateAndSpawn(prefab, ownerClientId)`. Never spawn
   authoritative objects on a client.
4. **Replicate state with `NetworkVariable<T>`.** Declare the read/write permissions, initialize
   in `OnNetworkSpawn`, and subscribe to `OnValueChanged` for UI/effects.
5. **Send intent with RPCs.** `[ServerRpc]` for requests (damage, interact, buy), `[ClientRpc]`
   for cosmetic results. Name methods with the `ServerRpc`/`ClientRpc` suffix; the attribute
   requires it.
6. **Validate on the server.** Check ownership, range, cooldowns and game rules before applying
   anything; a client can call any RPC it can reach.
7. **Smooth movement separately.** Use `NetworkTransform` (or a custom `NetworkBehaviour`) with
   interpolation; do not replicate a `Transform` every frame by hand.
8. **Test with a host and at least two clients**, including late joins, disconnect/reconnect and
   simulated latency.

## Patterns

### 1. Networked health with server-only writes

```csharp
using Unity.Netcode;
using UnityEngine;

public sealed class PlayerHealth : NetworkBehaviour
{
    // Server writes, everyone reads. Clients cannot set this value.
    private readonly NetworkVariable<int> _health = new(
        100,
        NetworkVariableReadPermission.Everyone,
        NetworkVariableWritePermission.Server);

    public int Health => _health.Value;

    public override void OnNetworkSpawn()
    {
        _health.OnValueChanged += OnHealthChanged;
        if (IsServer)
        {
            _health.Value = 100;               // safe: server owns the write
        }
        RefreshUi(_health.Value);
    }

    public override void OnNetworkDespawn()
    {
        _health.OnValueChanged -= OnHealthChanged;
    }

    private void OnHealthChanged(int previous, int current) => RefreshUi(current);

    // Called by the owning client; the server decides the result.
    [ServerRpc]
    public void RequestDamageServerRpc(int amount, ServerRpcParams rpcParams = default)
    {
        if (!IsServer || amount <= 0 || amount > 100)
        {
            return;                            // never trust the number
        }

        var attacker = rpcParams.Receive.SenderClientId;
        if (!ServerRules.CanDamage(attacker, OwnerClientId))
        {
            return;
        }

        _health.Value = Mathf.Max(0, _health.Value - amount);
        if (_health.Value == 0)
        {
            DieClientRpc();
        }
    }

    [ClientRpc]
    private void DieClientRpc() => PlayDeathEffect();
}
```

`NetworkVariableWritePermission.Server` is the default and the safe choice. A client writing a
server-owned variable throws or logs; the value never reaches other peers.

### 2. Spawn a networked projectile on the server

```csharp
[SerializeField] private NetworkObject projectilePrefab;

[ServerRpc]
private void FireServerRpc(Vector3 origin, Vector3 direction)
{
    if (!IsServer || !ServerRules.CanFire(OwnerClientId, origin, direction))
    {
        return;
    }

    var instance = Instantiate(projectilePrefab, origin, Quaternion.LookRotation(direction));
    instance.GetComponent<NetworkObject>().Spawn();
    // Optional: give the shooter ownership for client-side visuals only.
}
```

- The prefab must be in the `NetworkPrefabsList`; an unregistered prefab spawns on the server but
  fails to instantiate on clients.
- `Spawn()` is server-only. `SpawnWithOwnership(clientId)` assigns an owner when the object needs
  one.
- The server validates `origin`/`direction` against the player's known position; a client can send
  anything.

### 3. ClientRpc for effects, not state

```csharp
[ClientRpc]
private void HitEffectClientRpc(Vector3 point, ClientRpcParams rpcParams = default)
{
    // Cosmetic only: no gameplay value is derived from this call.
    Instantiate(hitSpark, point, Quaternion.identity);
}

// Send to one client:
var onlyOwner = new ClientRpcParams
{
    Send = new ClientRpcSendParams { TargetClientIds = new[] { OwnerClientId } }
};
HitEffectClientRpc(point, onlyOwner);
```

`ClientRpc` runs on every client by default. Use `ClientRpcParams` to target the owner or a list
of clients for private information (inventory contents, secret roles).

### 4. Ownership checks

```csharp
public override void OnNetworkSpawn()
{
    if (!IsOwner)
    {
        // Disable input and camera for remote players.
        GetComponent<PlayerInput>().enabled = false;
        GetComponent<AudioListener>().enabled = false;
    }
}
```

`IsOwner` is the local client that owns this object; on the server, `IsOwner` is false for a
client-owned object unless it is the host. `IsServer` is true on the host, so a host player is both
`IsServer` and `IsOwner`.

### 5. Movement

- Add `NetworkTransform` for simple objects (positions/rotation at a send rate). Enable
  interpolation so remote objects move smoothly.
- For characters, replicate input/velocity in a `NetworkBehaviour` and let the server drive the
  authoritative `CharacterController`/`Rigidbody`; do not let clients write the transform.
- Do not sync `Rigidbody` and `NetworkTransform` on the same object unless the project has
  explicitly designed the ownership; two systems fighting produces jitter.
- Test with artificial latency (`NetworkSimulator` or the transport's simulator) and packet loss.

### 6. Session lifecycle

```csharp
public async void StartHost()
{
    if (NetworkManager.Singleton.StartHost())
    {
        await SceneManager.LoadSceneAsync("Game", LoadSceneMode.Additive);
        NetworkManager.Singleton.SceneManager.LoadScene("Game", LoadSceneMode.Additive);
    }
}
```

Use `NetworkManager.SceneManager` for synchronized scene loads, not plain `SceneManager`. Clients
must have the scene in build settings. Disconnect handling (`OnClientDisconnectCallback`) should
clean up player objects and return to the lobby, not leave a half-spawned world.

## Pitfalls

- **RPC is not invoked** → the method name does not end with `ServerRpc`/`ClientRpc`, the object is
  not spawned, or the caller does not own it. Server RPCs require an owning client unless
  `RequireOwnership = false`.
- **`NetworkVariable` change does not replicate** → the client wrote a server-owned variable, the
  object was not spawned yet, or the value was set before `OnNetworkSpawn`.
- **Prefab spawns on server but not clients** → it is missing from the `NetworkPrefabsList`, or
  the client build does not contain the same prefab hash.
- **NullReference in `OnNetworkSpawn`** → ordering: for dynamically spawned objects
  `OnNetworkSpawn` runs before `Start`; cache references in `Awake`, use them in spawn callbacks.
- **Two NetworkObjects in one prefab** → only one at the root is supported; nested ones break
  spawning.
- **Host behaves differently from a dedicated server** → host code that assumes `IsOwner` or a
  local camera. Gate client-only code on `IsOwner`, server-only code on `IsServer`.
- **Players can cheat** → any gameplay value derived from client input was trusted. Validate
  ranges, ownership, cooldowns and line of sight on the server.
- **Jitter on remote characters** → conflicting transform writers (physics + NetworkTransform),
  no interpolation, or a send rate too low for the movement speed.
- **Late joiner sees wrong state** → state that only lives in a `ClientRpc` or a local variable.
  Initial state belongs in `NetworkVariable`s or a spawn payload.
- **Scene load desyncs** → plain `SceneManager.LoadScene` on one peer. Use
  `NetworkManager.SceneManager` and identical build settings.

## References

- Read `references/authority-rpcs-and-testing.md` for the NGO API table, permission matrix,
  ownership rules, spawn/despawn flow, latency simulation and a multiplayer test checklist.

## Related skills

- `unity-input-system` — local input that feeds RPCs.
- `unity-physics` — authoritative collision and movement.
- `unity-ui` — lobby, scoreboard and connection UI.
- `godot-multiplayer` / `roblox-networking` — other engines' authoritative models.
- `save-systems` — what should and should not be stored server-side.
