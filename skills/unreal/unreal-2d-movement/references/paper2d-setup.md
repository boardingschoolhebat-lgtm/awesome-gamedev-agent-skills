# Paper 2D setup for 2D characters (UE 5.8)

Reference material for `SKILL.md`. Targets **UE 5.8** with the Paper 2D plugin.

## Project setup

1. *Edit ▸ Plugins*, search `Paper 2D`, enable it, restart the editor.
2. Add the module to the game module's `*.Build.cs`:

```csharp
PublicDependencyModuleNames.AddRange(new string[]
{
	"Core", "CoreUObject", "Engine", "InputCore", "Paper2D"
});
```

3. Regenerate project files and rebuild. A missing module shows up as unresolved externals on
   `APaperCharacter` or `UPaperFlipbookComponent`.

## Paper 2D assets

| Asset | Role |
|-------|------|
| Sprite | One image with a pivot; the atom of 2D rendering |
| Flipbook | Ordered list of sprites with a frame rate; what the character plays |
| Tile Set / Tile Map | Grid levels built from sprites; separate from the character |
| Sprite Editor | Sets pivot, collision geometry and pixels-per-unit |

Sprite pivot choices that matter for characters:

- **Bottom-center** pivot plus a sprite Z offset of `-capsule half-height` puts the feet on the
  capsule bottom.
- **Center** pivot needs the offset computed from the sprite height, not from the capsule, or the
  character floats.
- Changing the pivot after animations are authored shifts every frame; fix it before building
  flipbooks.

Pixel scale comes from *Pixels Per Unreal Unit* on the sprite/texture settings. Keep it consistent
across all character sprites or run/idle frames change size.

## Plane constraint recipes

`UCharacterMovementComponent` inherits `UMovementComponent`, which owns the plane constraint:

```cpp
Move->SetPlaneConstraintEnabled(true);
Move->SetPlaneConstraintNormal(FVector(0.f, 1.f, 0.f));   // lock Y
// or
Move->SetPlaneConstraintAxisSetting(EPlaneConstraintAxisSetting::Y);
```

| Setting | Effect |
|---------|--------|
| `SetPlaneConstraintNormal` | Constrains movement to the plane whose normal is given |
| `SetPlaneConstraintAxisSetting` | Convenience for world X/Y/Z locking |
| `SetPlaneConstraintFromVectors(Forward, Up)` | Derives the plane from a custom basis |
| `SetPlaneConstraintOrigin` | Moves the constrained plane away from the actor origin |

Plane constraint blocks translation, not rotation. Pair it with the rotation settings:

- Side-scroller: `bUseControllerRotationYaw = false`, `bOrientRotationToMovement = false`; flip
  the sprite for facing.
- Top-down: `bOrientRotationToMovement = true` with `RotationRate` set; the capsule turns toward
  movement and the sprite follows.

## Movement values that need 2D tuning

| Property | Why |
|----------|-----|
| `MaxWalkSpeed` | Defaults assume a 3D character; 2D sprites read faster at lower speeds |
| `JumpZVelocity` | Jump height in cm/s; match the sprite's pixel height |
| `GravityScale` | 0 for top-down, 1+ for side-scrollers |
| `AirControl` | How much steering is allowed mid-jump |
| `BrakingDecelerationWalking` | Stop distance; too high looks snappy, too low slides |
| `GroundFriction` | Grip when no input is held |

`IsMovingOnGround()` on the movement component is the grounded check for animation state.

## Collision

- The capsule owns collision; the flipbook component does not collide.
- Size the capsule to the character's body, not the sprite's transparent bounds.
- Set the capsule's collision profile (Pawn) and object type (Pawn) as usual; Paper 2D sprites
  should not enable collision themselves.
- For one-way platforms, use collision channels and `CanJump`/line traces rather than plane tricks.

## Enhanced Input wiring

1. Create `IA_Move` (Axis2D) and `IA_Jump` (Digital) Input Actions.
2. Add them to `IMC_Player` with modifiers for WASD/gamepad.
3. In `SetupPlayerInputComponent`, bind `IA_Move` to `Move` and `IA_Jump` to `JumpPressed` /
   `JumpReleased` (triggered / completed).
4. Add the mapping context in `PawnClientRestart` or `BeginPlay` through the local player's
   subsystem.

See `unreal-enhanced-input` for the asset-side details and rebinding.

## PIE checklist

1. Orthographic camera looking along the locked axis; sprite faces the camera.
2. Move along the allowed axis only — the character does not drift off-plane.
3. Feet stay on the floor at idle, run and landing; no sinking or floating.
4. Facing flips cleanly at direction changes, without a one-frame pop.
5. Jump: rise, apex, fall and land all select the right flipbook.
6. Top-down: no gravity pull, rotation follows movement, sprite does not spin on its own.
7. Collision: capsule (not sprite) blocks against level geometry.
8. Frame rate: flipbook playback speed is authored in the asset, not multiplied by tick rate.
