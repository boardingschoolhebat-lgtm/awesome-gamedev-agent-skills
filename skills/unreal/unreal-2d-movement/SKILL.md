---
name: unreal-2d-movement
description: >
  Build 2D characters in Unreal Engine 5.8 with Paper2D: APaperCharacter setup, capsule and sprite
  alignment, plane-constrained CharacterMovement, side-scroller and top-down movement, jump and
  gravity, flipbook state switching, facing flips and orthographic cameras. Use when a project has
  Paper 2D assets or the request mentions a 2D character in Unreal, PaperCharacter, PaperFlipbook,
  plane constraint, or a sprite-controlled platformer.
---

# Unreal 2D movement (Paper2D)

Move a 2D character in Unreal Engine 5.8 using the **Paper 2D** plugin. Targets **UE 5.8**.

`APaperCharacter` is an `ACharacter` whose visual is a `UPaperFlipbookComponent` instead of a
skeletal mesh. `ACharacter`'s `Mesh` is **not** set up on it — use `GetSprite()`.

## When to use

- Use when a 2D character must move, jump, face a direction or switch flipbooks in Unreal.
- Use when a project uses Paper 2D Sprites and Flipbooks, or when a character slides off its
  movement plane, sinks into the floor, or faces the wrong way.

**When *not* to use:** Blueprint-only graph work → `unreal-blueprints`; reflection macros, class
setup and Build.cs basics → `unreal-cpp-gameplay`; input assets and mapping contexts →
`unreal-enhanced-input`; 3D character movement → `unreal-cpp-gameplay`; camera design as a
concept → `camera-systems`.

## Core workflow

1. **Enable the plugin.** *Edit ▸ Plugins ▸ 2D ▸ Paper 2D*, restart, and add `"Paper2D"` to
   `PublicDependencyModuleNames` in the module's `*.Build.cs` — otherwise `PaperCharacter.h` and
   the Paper2D types do not link.
2. **Subclass `APaperCharacter`.** Set the capsule size, offset the sprite so the feet meet the
   capsule bottom, and constrain movement to one plane in the constructor.
3. **Assign flipbooks.** Create Sprite and Flipbook assets, then set the default flipbook and
   animation assets as `UPROPERTY(EditDefaultsOnly)` so designers can swap them.
4. **Bind input.** Map an Axis2D action through Enhanced Input and call `AddMovementInput` along
   the world axes the plane allows; bind jump to `Jump()` / `StopJumping()`.
5. **Drive the flipbook from velocity.** In `Tick`, choose idle/run/jump/fall from velocity and
   grounded state, call `SetFlipbook` only on change, then `Play()`.
6. **Verify in PIE with an orthographic camera.** Check plane lock, capsule alignment, facing and
   jump arcs; Paper 2D renders nothing useful from an arbitrary 3D camera angle.

## Patterns

### 1. Constructor: capsule, sprite offset, plane lock

```cpp
#include "PaperCharacter.h"
#include "PaperFlipbookComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AMyPaperChar::AMyPaperChar()
{
	GetCapsuleComponent()->InitCapsuleSize(18.f, 36.f);       // radius, half-height
	GetSprite()->SetRelativeLocation(FVector(0.f, 0.f, -36.f)); // feet on the capsule bottom

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->SetPlaneConstraintEnabled(true);
	Move->SetPlaneConstraintNormal(FVector(0.f, 1.f, 0.f));   // side view: lock world Y
	Move->bOrientRotationToMovement = false;
	bUseControllerRotationYaw = false;
}
```

The half-height must match the sprite's visible body, and the sprite offset must equal
`-half-height` when the sprite pivot is at the feet. A mismatch shows up as floating or sinking.

### 2. Plane recipes

| Game view | Plane normal | Gravity | Camera |
|-----------|--------------|---------|--------|
| Side-scroller | `FVector(0, 1, 0)` (lock Y) | `GravityScale = 1` | Orthographic, looking along -Y |
| Top-down | `FVector(0, 0, 1)` (lock Z) | `GravityScale = 0` | Orthographic, looking down -Z |

```cpp
// top-down variant
Move->SetPlaneConstraintNormal(FVector(0.f, 0.f, 1.f));
Move->GravityScale = 0.f;
Move->bOrientRotationToMovement = true;   // face the movement direction
```

`SetPlaneConstraintAxisSetting(EPlaneConstraintAxisSetting::Y)` is the axis-based equivalent;
keep to one style per project.

### 3. Movement input (Enhanced Input Axis2D)

```cpp
void AMyPaperChar::Move(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	AddMovementInput(FVector::ForwardVector, Axis.X);          // world +X, always allowed
	if (bTopDown)
	{
		AddMovementInput(FVector::RightVector, Axis.Y);        // world +Y, top-down only
	}
}

void AMyPaperChar::JumpPressed()  { Jump(); }
void AMyPaperChar::JumpReleased() { StopJumping(); }
```

Bind these in `SetupPlayerInputComponent` with the project's Input Mapping Context; the asset
side lives in `unreal-enhanced-input`. Never add a Y component in a side-scroller: the plane
constraint drops it, but the input feels unresponsive if the axis is mapped wrong.

### 4. Flipbook state from velocity

```cpp
void AMyPaperChar::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	UPaperFlipbookComponent* SpriteComp = GetSprite();
	const float SpeedX = FMath::Abs(GetVelocity().X);
	UPaperFlipbook* Desired = SpeedX > 1.f ? RunFlipbook : IdleFlipbook;

	if (Desired && SpriteComp->GetFlipbook() != Desired)
	{
		SpriteComp->SetFlipbook(Desired);   // resets play time on a new flipbook
		SpriteComp->Play();
	}

	if (SpeedX > 1.f)
	{
		const float Dir = GetVelocity().X < 0.f ? -1.f : 1.f;
		SpriteComp->SetRelativeScale3D(FVector(Dir, 1.f, 1.f));
	}
}
```

`SetFlipbook` returns false if the asset is null and does not start playback by itself — call
`Play()` after the swap. Compare against `GetFlipbook()` so the state change happens once.

### 5. Air state without a second animation graph

```cpp
const bool bGrounded = GetCharacterMovement()->IsMovingOnGround();
UPaperFlipbook* Desired = !bGrounded ? (GetVelocity().Z > 0.f ? JumpFlipbook : FallFlipbook)
                                     : (SpeedX > 1.f ? RunFlipbook : IdleFlipbook);
```

Paper 2D has no skeletal animation blueprint; state selection is ordinary gameplay code. Keep
the choice in one function so jump, fall and run cannot disagree.

## Pitfalls

- **`PaperCharacter.h` not found or unresolved externals** — the Paper 2D plugin is disabled or
  `"Paper2D"` is missing from `*.Build.cs`. Both are required.
- **`GetMesh()` is null** — `APaperCharacter` uses `GetSprite()`; `Mesh` is deliberately not set up.
- **Character drifts off the play plane** — plane constraint disabled, wrong normal, or movement
  input adds an axis the plane locks. Check the normal matches the view.
- **Character sinks or floats** — capsule half-height and sprite Z offset disagree, or the sprite
  pivot is centered instead of at the feet.
- **Sprite is invisible** — the camera looks at the back face of the sprite plane, the flipbook is
  null, or the scale X became `0` from a sign calculation on a zero velocity.
- **Character rotates with the camera** — `bUseControllerRotationYaw` is true, or
  `bOrientRotationToMovement` is on in a side-scroller.
- **Facing flip also flips lighting** — negative scale mirrors normals; for lit materials use a
  mirrored flipbook or rotate the sprite 180° around Z instead.
- **Top-down character slowly falls** — gravity is still on while the plane locks Z; set
  `GravityScale = 0`.
- **Animation restarts every frame** — `SetFlipbook` is called unconditionally; guard with
  `GetFlipbook() != Desired`.
- **Jump feels floaty** — tune `JumpZVelocity`, `GravityScale` and `AirControl` on the movement
  component; the default values are tuned for a 3D character scale.
- **Camera shows perspective distortion** — an orthographic camera needs *Projection Mode:
  Orthographic* and a sensible *Ortho Width*; perspective cameras make 2D sprites skew.

## References

- Read `references/paper2d-setup.md` for plugin and Build.cs setup, plane-constraint recipes,
  Paper 2D asset roles, collision channels and a PIE checklist.

## Related skills

- `unreal-cpp-gameplay` — reflection macros, class setup, Build.cs and the Gameplay Framework.
- `unreal-enhanced-input` — Input Actions, Mapping Contexts and rebinding.
- `unreal-blueprints` — data-only Blueprint children that assign flipbooks and tuning values.
- `platformer` — jump arcs, coyote time and level rules for side-scrollers.
- `camera-systems` — orthographic framing, follow and deadzones.
- `game-feel` — hit pause, squash and animation timing.
