---
name: unreal-animation
description: >
  Animation in Unreal Engine 5.8: Animation Blueprints and UAnimInstance, AnimGraph state
  machines and blend spaces, montages for one-shots (PlayAnimMontage, Montage_Play, sections,
  OnMontageEnded), AnimNotify events, root motion, and networked montage playback. Use when a
  character needs locomotion blending, attacks, hit reactions or animation events.
---

# Unreal animation

Unreal animation is asset-driven: Animation Sequences feed an Animation Blueprint (AnimGraph) that
produces the final pose, while Montages play one-shot actions on top. Gameplay code sets
variables, plays montages and listens for notifies. Targets **Unreal Engine 5.8**.

## When to use

- Use when setting up locomotion blending, state machines, montages, notifies or root motion.
- Use when animations do not play, montages are ignored, or they desync in multiplayer.

**When *not* to use:** character movement → `unreal-2d-movement` / `unreal-cpp-gameplay`;
replication fundamentals → `unreal-replication`; skeletal mesh import → the asset pipeline;
engine-neutral animation concepts → `game-feel`.

## Core workflow

1. **Create an Animation Blueprint** for the skeletal mesh; its parent is a `UAnimInstance`
   subclass when you need C++ variables.
2. **Expose gameplay state** as `UPROPERTY(BlueprintReadOnly)` variables updated in
   `NativeUpdateAnimation` (speed, grounded, aiming).
3. **Locomotion**: a state machine (idle/walk/run/jump/fall) driving a 1D/2D blend space on speed
   and direction.
4. **One-shots**: Animation Montages played from gameplay (`PlayAnimMontage` or
   `Montage_Play`), with sections for combos and `OnMontageEnded` for cleanup.
5. **Events**: AnimNotify/AnimNotifyState for footsteps, hit windows and trails; handle them in
   the AnimBP or via delegates.
6. **Network**: play montages where they must be authoritative; replicate the *event*, not the
   pose.
7. **Profile**: animation cost is per skeletal mesh; use LODs and update rates for crowds.

## Patterns

### 1. AnimInstance variables

```cpp
// MyCharacterAnimInstance.h
UCLASS()
class MYGAME_API UMyCharacterAnimInstance : public UAnimInstance
{
    GENERATED_BODY()

public:
    virtual void NativeUpdateAnimation(float DeltaSeconds) override;

    UPROPERTY(BlueprintReadOnly, Category = "Locomotion")
    float Speed = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "Locomotion")
    bool bIsFalling = false;
};
```

```cpp
void UMyCharacterAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeUpdateAnimation(DeltaSeconds);

    if (const APawn* Pawn = TryGetPawnOwner())
    {
        Speed = Pawn->GetVelocity().Size2D();
        if (const ACharacter* Character = Cast<ACharacter>(Pawn))
        {
            bIsFalling = Character->GetCharacterMovement()->IsFalling();
        }
    }
}
```

- `TryGetPawnOwner()` is the safe accessor in the AnimBP.
- Keep `NativeUpdateAnimation` cheap: read state, no traces or allocations.
- Property-only updates can move to the thread-safe update when the engine version supports it;
  otherwise keep game-thread work minimal.

### 2. Locomotion state machine and blend space

```text
AnimGraph: Output Pose <- State Machine
  Entry -> Idle
  Idle  -> Walk/Run   (Speed > 10)
  Walk/Run -> Idle    (Speed <= 10)
  Any   -> Jump/Fall  (bIsFalling)
  Jump/Fall -> Land   (grounded)
  Land  -> Idle
```

- Drive a 1D blend space on `Speed` for walk/run; a 2D blend space on speed + direction for
  strafing.
- Set the state machine's entry state deliberately; an empty entry pose is a common "T-pose" bug.
- Transition rules should use the same variables the gameplay code sets, not raw input.
- Use `Sync` groups for left/right foot phases so blends do not foot-slide.

### 3. Montages from gameplay

```cpp
// ACharacter subclass
void AMyCharacter::Attack()
{
    if (UAnimInstance* Anim = GetMesh()->GetAnimInstance())
    {
        if (UAnimMontage* Montage = AttackMontage)
        {
            Anim->Montage_Play(Montage, 1.0f);
        }
    }
}
```

- `ACharacter::PlayAnimMontage(Montage, Rate, StartSection)` is the convenience wrapper.
- `Montage_Play` returns the montage length (0 on failure) — useful for cooldowns.
- `Montage_JumpToSection(FName, Montage)` for combos/phases.
- `Montage_Stop(BlendOutTime, Montage)` to cancel.
- `Montage_IsPlaying(Montage)` guards re-entry.

### 4. OnMontageEnded

```cpp
void AMyCharacter::Attack()
{
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    if (!Anim || !AttackMontage || Anim->Montage_IsPlaying(AttackMontage)) return;

    FOnMontageEnded EndDelegate;
    EndDelegate.BindUObject(this, &AMyCharacter::OnAttackEnded);
    Anim->Montage_Play(AttackMontage);
    Anim->Montage_SetEndDelegate(EndDelegate, AttackMontage);
}

void AMyCharacter::OnAttackEnded(UAnimMontage* Montage, bool bInterrupted)
{
    bAttacking = false;
    // interrupted == true means another montage/stop cut it short
}
```

- `bInterrupted` distinguishes a finished action from a cancelled one; do not grant rewards on an
  interrupted attack.
- Bind the delegate before/at play, or you miss short montages.
- Clear state in one place; notifies and delegates can otherwise double-fire.

### 5. AnimNotify events

- `AnimNotify` fires once at a time; `AnimNotifyState` has Begin/Tick/End.
- Use notifies for footsteps, weapon traces, hit windows and VFX; keep them data-driven.
- In C++, override `Notify(USkeletalMeshComponent*, UAnimSequenceBase*, const FAnimNotifyEventReference&)`.
- In Blueprints, implement the notify event on the AnimBP.
- Notifies run on the machine playing the montage; in multiplayer, decide whether the effect is
  cosmetic (client) or gameplay (server).

### 6. Networked montages

```cpp
void AMyCharacter::PlayAttackMontage()
{
    if (HasAuthority())
    {
        MulticastPlayAttack();
    }
}

void AMyCharacter::MulticastPlayAttack_Implementation()
{
    PlayAnimMontage(AttackMontage);
}
```

- Server plays and replicates montage state for the character; for cosmetic one-shots a multicast
  is enough.
- Do not replicate every pose; replicate the action and let each client's AnimBP blend.
- Root motion montages must be authoritative; client-side root motion desyncs.
- Test with simulated latency: a late-joining client should still see the current montage state.

## Pitfalls

- **T-pose** → AnimBP has no output pose, the state machine entry is empty, or the mesh has no
  AnimBP assigned.
- **Animation not playing** → wrong mesh, montage slot not set up, or `Montage_Play` returned 0
  (slot/asset issue). Check the montage's slot name matches the AnimGraph slot.
- **Montage ignored** → another montage is already playing with a higher priority/slot; stop it or
  use a different slot.
- **Notify never fires** → notify placed on a montage section not reached, or the montage was
  interrupted.
- **Foot sliding** → blend space speed does not match `MaxWalkSpeed`; scale playback rate or tune
  the blend.
- **Animation pops** → no blend in/out, or state transitions with zero blend time.
- **Multiplayer desync** → playing gameplay montages only on clients, or replicating poses.
- **Root motion ignored** → montage/sequence root motion disabled, or the character movement mode
  blocks it.
- **Cost spikes** → many skeletal meshes updating every frame; use animation sharing/LODs/update
  rate optimization.

## References

- Read `references/animbp-montages-and-notifies.md` for the API table, AnimGraph setup, montage
  sections/delegates, notify rules, networking and an animation test checklist.

## Related skills

- `unreal-cpp-gameplay` — characters and components that own the AnimBP.
- `unreal-replication` — authority and multicast rules.
- `unreal-2d-movement` — Paper2D flipbooks (a different pipeline).
- `game-feel` — timing, anticipation and hit feedback.
- `unity-animation` — the equivalent Animator/state-machine workflow.
