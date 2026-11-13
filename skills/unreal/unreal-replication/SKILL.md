---
name: unreal-replication
description: >
  Replicate gameplay in Unreal Engine 5.8 C++: authority and roles, UPROPERTY(Replicated) with
  GetLifetimeReplicatedProps and DOREPLIFETIME, RepNotify, Server/Client/NetMulticast RPCs with
  validation, relevancy and net update frequency, and cheat-resistant server checks. Use when an
  Unreal project needs multiplayer state, RPCs, or fixes for values that do not replicate, RPCs
  that never run, and client-authority exploits. Targets UE 5.8.
---

# Unreal replication

Unreal's server owns the world; clients receive replicated properties and send RPCs the server
validates. Targets **Unreal Engine 5.8**.

## When to use

- Use when adding multiplayer state, RPCs, networked actors, or debugging values that stay
  default on clients.
- Use when a Server RPC never fires, a RepNotify does not run, or clients can change authoritative
  state.

**When *not* to use:** single-player gameplay → `unreal-cpp-gameplay`; input mapping →
`unreal-enhanced-input`; UI → `unreal-ui`; AI → `unreal-behavior-trees`; dedicated-server
infrastructure and sessions are separate services.

## Authority first

| Concept | Meaning |
|---------|---------|
| `HasAuthority()` | true on the server for this actor |
| `GetLocalRole()` | `ROLE_Authority` on the server, `ROLE_SimulatedProxy`/`ROLE_AutonomousProxy` on clients |
| `GetRemoteRole()` | the role the other side has |
| `bReplicates` | the actor participates in replication; default false for most actors |
| `bOnlyRelevantToOwner` | only the owner receives this actor |

Rule: gameplay state changes on the **server**; clients send input/intent through Server RPCs.
Anything a client computes is a request until the server accepts it.

## Core workflow

1. **Enable replication on the actor.** `bReplicates = true;` in the constructor (and
   `SetReplicateMovement(true)` if movement is engine-driven).
2. **Mark properties.** `UPROPERTY(Replicated)` or `UPROPERTY(ReplicatedUsing = OnRep_Health)`.
3. **Register them.** Override `GetLifetimeReplicatedProps` and call
   `DOREPLIFETIME(AMyActor, Health);` (or `DOREPLIFETIME_CONDITION` for a condition).
4. **Use RepNotify for reactions.** `OnRep_Health` updates UI/effects on clients; the server does
   not call it automatically when it changes the value.
5. **Send intent with Server RPCs.** `UFUNCTION(Server, Reliable, WithValidation)`; implement
   `_Implementation` and `_Validate`.
6. **Broadcast cosmetics with `NetMulticast`.** Effects, sounds, animations; never authoritative
   state.
7. **Spawn on the server only.** `SpawnActor` on the server replicates to clients when the class
   is replicated and relevant.
8. **Tune relevancy and frequency** before shipping: `NetUpdateFrequency`,
   `NetCullDistanceSquared`, `bAlwaysRelevant`.

## Patterns

### 1. Replicated health with RepNotify

```cpp
// HealthComponent.h
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "HealthComponent.generated.h"

UCLASS(ClassGroup = (Gameplay), meta = (BlueprintSpawnableComponent))
class MYGAME_API UHealthComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UHealthComponent();

    UFUNCTION(BlueprintPure, Category = "Health")
    float GetHealth() const { return Health; }

    /** Server-only: applies damage and replicates the result. */
    void ApplyDamage(float Amount, AController* InstigatorController);

protected:
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(ReplicatedUsing = OnRep_Health, BlueprintReadOnly, Category = "Health")
    float Health = 100.f;

    UPROPERTY(EditDefaultsOnly, Category = "Health")
    float MaxHealth = 100.f;

    UFUNCTION()
    void OnRep_Health(float PreviousHealth);
};
```

```cpp
// HealthComponent.cpp
#include "HealthComponent.h"
#include "Net/UnrealNetwork.h"

UHealthComponent::UHealthComponent()
{
    SetIsReplicatedByDefault(true);      // component participates in replication
}

void UHealthComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UHealthComponent, Health);
}

void UHealthComponent::ApplyDamage(float Amount, AController* InstigatorController)
{
    if (!GetOwner()->HasAuthority() || Amount <= 0.f)
    {
        return;                           // server authority only
    }

    Health = FMath::Clamp(Health - Amount, 0.f, MaxHealth);
    OnRep_Health(Health + Amount);       // server does not get the RepNotify call
    if (Health <= 0.f)
    {
        // Death handling on the server; replicate the state, not the event.
    }
}

void UHealthComponent::OnRep_Health(float PreviousHealth)
{
    // Clients: update the HUD, play hit reactions, etc.
    OnHealthChanged.Broadcast(Health, PreviousHealth);
}
```

The server must call the RepNotify itself when it needs the same side effects; Unreal only invokes
it on clients when a replicated value arrives.

### 2. Server RPC with validation

```cpp
// In the character header:
UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = "Combat")
void Server_Fire(FVector Origin, FVector Direction);

// Implementation:
bool AMyCharacter::Server_Fire_Validate(FVector Origin, FVector Direction)
{
    // Cheap sanity checks only; return false to reject and optionally kick/ignore.
    return Origin.IsNearlyZero() == false
        && Direction.IsNormalized()
        && FVector::DistSquared(Origin, GetActorLocation()) < FMath::Square(300.f);
}

void AMyCharacter::Server_Fire_Implementation(FVector Origin, FVector Direction)
{
    if (!HasAuthority() || !IsAlive())
    {
        return;
    }
    // Server-side trace, ammo check, cooldown, then apply damage.
}
```

- `WithValidation` generates `_Validate`; returning false drops the call and logs a warning.
- Validation is for malformed/hostile input, not for full gameplay rules; re-check ammo, cooldown
  and line of sight in the implementation.
- Server RPCs must be called on an actor the client **owns** (its connection). Calling one on a
  non-owned actor does nothing.

### 3. Multicast for effects only

```cpp
UFUNCTION(NetMulticast, Unreliable)
void Multicast_PlayHitEffect(FVector Location, FRotator Rotation);

void AMyCharacter::Multicast_PlayHitEffect_Implementation(FVector Location, FRotator Rotation)
{
    if (HitEffect)                     // cosmetic: no gameplay state derived here
    {
        UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, HitEffect, Location, Rotation);
    }
}

// Called on the server after the authoritative hit:
Multicast_PlayHitEffect(HitLocation, HitRotation);
```

`NetMulticast` from the server runs on the server and all relevant clients. A client calling a
multicast RPC is ignored. Use `Reliable` for gameplay-critical messages and keep those in
replicated state instead of RPCs.

### 4. Replication conditions

```cpp
void AMyCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    // Only the owning client needs the exact ammo count.
    DOREPLIFETIME_CONDITION(AMyCharacter, Ammo, COND_OwnerOnly);

    // Everyone except the owner (the owner predicts its own movement).
    DOREPLIFETIME_CONDITION(AMyCharacter, ReplicatedVelocity, COND_SkipOwner);
}
```

Conditions reduce bandwidth and accidental information leaks. A late joiner still receives the
current value of every property; `COND_OwnerOnly` follows ownership if it changes.

### 5. Actor and component setup

- `bReplicates = true` on the actor; components that replicate call
  `SetIsReplicatedByDefault(true)`.
- Replicate the actor's **state** through properties; let `CharacterMovement` replicate movement
  rather than syncing transforms by hand.
- `GameMode` exists only on the server; store shared match state in `GameState`/`PlayerState`,
  which replicate.
- Spawned actors must be relevant to a client to replicate: check `NetCullDistanceSquared`,
  `bAlwaysRelevant`, and `bOnlyRelevantToOwner`.
- `NetUpdateFrequency` (default 100 Hz for characters) drives property updates; lower it for
  ambient actors, raise it only where responsiveness matters.

## Pitfalls

- **Property stays default on clients** → missing `bReplicates`, missing `DOREPLIFETIME` (or the
  property is not a `UPROPERTY`), or the actor is not relevant to that client.
- **RepNotify does not run on the server** → expected. Unreal calls RepNotify on clients; call the
  function manually on the server when it needs the same result.
- **Server RPC never fires** → the client does not own the actor, the function lacks `Server`, or
  the actor is not replicated. Check `GetLocalRole()` on the caller.
- **`_Validate` is missing** → a `WithValidation` RPC without a `_Validate` implementation fails
  to link; add both functions.
- **Client changes a replicated value** → it is overwritten by the next server update, and any
  local logic based on it desyncs. Change state on the server.
- **Multicast runs twice on the listen server** → expected: multicast includes the server. Guard
  server-side effects with `HasAuthority()` if they must happen once.
- **Late joiner misses an event** → events are not replayed. Keep durable state in replicated
  properties; use RPCs for transient effects.
- **GameMode is null on clients** → `AGameModeBase` is server-only. Use `AGameStateBase`/
  `APlayerState` for replicated match data.
- **Bandwidth spikes** → replicating large arrays/strings or high `NetUpdateFrequency` on many
  actors. Replicate ids/deltas and tune relevancy.
- **Movement jitter** → custom movement code writing the transform alongside `CharacterMovement`.
  Choose one owner and use `ServerMove`/root motion sources for custom locomotion.

## References

- Read `references/properties-rpcs-and-relevancy.md` for the replication API table, property
  conditions, RPC rules, relevancy/frequency tuning and a multiplayer test checklist.

## Related skills

- `unreal-cpp-gameplay` — actors, game mode, player controller and pawns.
- `unreal-enhanced-input` — input that feeds Server RPCs.
- `unreal-ui` — HUD and scoreboard driven by replicated state.
- `unreal-behavior-trees` — AI that runs on the server.
- `godot-multiplayer` / `roblox-networking` / `unity-networking` — other engines' models.
