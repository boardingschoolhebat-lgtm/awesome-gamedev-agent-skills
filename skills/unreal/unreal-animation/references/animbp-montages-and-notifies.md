# AnimBP, montages and notifies (UE 5.8)

Depth for `unreal-animation`: the AnimGraph, montage API, notify rules and networked playback.

## API used by the skill

| API | Header / form | Notes |
|-----|---------------|-------|
| `UAnimInstance` | `Animation/AnimInstance.h` | Base class for AnimBP; `NativeUpdateAnimation`. |
| `TryGetPawnOwner()` | `UAnimInstance` | Safe owner accessor. |
| `GetAnimInstance()` | `USkeletalMeshComponent` | The active AnimBP instance. |
| `UAnimMontage` | `Animation/AnimMontage.h` | One-shot asset with slots/sections. |
| `Montage_Play(Montage, Rate, ReturnType, StartAt, bStopAll)` | `UAnimInstance` | Returns length; 0 on failure. |
| `Montage_Stop(BlendOut, Montage)` | `UAnimInstance` | Cancel with blend out. |
| `Montage_JumpToSection(Name, Montage)` | `UAnimInstance` | Combo/phases. |
| `Montage_IsPlaying(Montage)` | `UAnimInstance` | Re-entry guard. |
| `Montage_SetEndDelegate(Delegate, Montage)` | `UAnimInstance` | Completion callback. |
| `PlayAnimMontage(Montage, Rate, Section)` | `ACharacter` | Convenience wrapper. |
| `FOnMontageEnded` | delegate | `(UAnimMontage*, bool bInterrupted)`. |
| `OnMontageEnded` / `OnMontageBlendingOut` | `UAnimInstance` delegates | Blueprint-assignable. |
| `AnimNotify` / `AnimNotifyState` | `Animation/AnimNotifies/...` | One-shot vs windowed events. |

## AnimGraph layout

```text
Output Pose
  └── State Machine (Locomotion)
        Entry -> Idle
        Idle <-> Walk/Run        (Speed)
        Any -> Jump/Fall         (bIsFalling)
        Jump/Fall -> Land        (grounded)
        Land -> Idle
  └── Slot 'DefaultSlot'         (montages blend here)
  └── Layered blend per bone     (upper-body aim/attack)
```

- Montages play into a named **Slot**; the AnimGraph must contain a Slot node with that name or
  the montage silently fails.
- Layered blends let an upper-body montage play over locomotion; set the slot's blend weight.
- State machines are subgraphs; keep transition rules small and readable.
- Use `Sync` groups and markers for walk/run phase matching.

## Blend spaces

| Type | Axes | Use |
|------|------|-----|
| 1D | one (speed) | walk/run/ sprint |
| 2D | two (speed, direction) | strafing, aim offsets |
| Aim Offset | pitch/yaw | look up/down/around |

- Sample animations at the speeds the character actually moves; mismatch causes foot sliding.
- Interpolate smoothly; avoid stepping axes with raw input.
- `Blend Space` assets are referenced from the AnimGraph.

## Montage sections and delegates

```cpp
Anim->Montage_Play(ComboMontage, 1.f);
Anim->Montage_JumpToSection(TEXT("Second"), ComboMontage);

FOnMontageEnded End;
End.BindUObject(this, &AMyCharacter::OnComboEnded);
Anim->Montage_SetEndDelegate(End, ComboMontage);
```

- Sections split a montage into combo steps; `JumpToSection` chains them.
- `bInterrupted` is true when another montage or `Montage_Stop` ended it; do not treat an
  interrupted attack as completed.
- `OnMontageBlendingOut` fires earlier than `OnMontageEnded`; use it for early cancellation
  windows.
- Bind delegates per play; stale bindings can fire for the wrong montage.

## Notifies

| Type | Fires | Use |
|------|-------|-----|
| `AnimNotify` | once at a point | footstep sound, spawn projectile, VFX |
| `AnimNotifyState` | Begin/Tick/End | hit window, trail, invulnerability |

- Notifies live on the sequence or montage; a notify on a section not played never fires.
- Gameplay notifies (damage window) belong on the server; cosmetic ones can run on clients.
- Notify names are assets: renaming breaks Blueprint handlers.
- Keep notifies idempotent; a montage can be interrupted mid-window, so handle the End.

## Root motion

- Enable root motion on the sequence/montage and in the character movement component.
- Root motion montages must be authoritative; clients predicting them desync.
- For attacks with lunges, root motion plus server validation avoids teleport corrections.
- If root motion is ignored, check the montage's `bEnableRootMotionTranslation/Rotation` and the
  movement mode.

## Networking

- Server plays montages for replicated characters; the montage state replicates to simulated
  proxies.
- Cosmetic one-shots can use `NetMulticast, Unreliable`.
- Never replicate poses or per-bone transforms; replicate the action/state.
- Late joiners: the replicated montage position lets clients resume mid-action; test with latency.
- Do not play gameplay-affecting montages only on the owning client.

## Test checklist

1. Idle/walk/run blend without pops or foot sliding.
2. Jump/fall/land transitions match movement state.
3. Attack montage plays, hits its notify window, and ends cleanly.
4. Interrupted montage does not grant completion rewards.
5. Combo sections chain and reset correctly.
6. Upper-body montage blends over locomotion without freezing legs.
7. Root motion moves the character on the server and clients agree.
8. Multiplayer: other clients see the attack; late joiner sees the current state.
9. Notifies fire once per play; no duplicate VFX/SFX.
10. Crowd test: skeletal mesh cost stays within budget (LODs/update rate).
