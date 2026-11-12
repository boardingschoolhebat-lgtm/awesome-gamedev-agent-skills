---
name: unity-3d-essentials
description: >
  Build first-person and third-person 3D character controllers in Unity 6.3 LTS: CharacterController
  vs Rigidbody movement, gravity and jump arcs, mouse-look with pitch clamping, ground checks with
  SphereCast, slope and stair handling, orbit cameras with collision, and Unity 6 physics renames.
  Use when a project needs a 3D player controller, FPS or TPS camera, mouse look, or a character
  that clips through slopes, floats, or cannot jump.
---

# Unity 3D essentials

Build a playable 3D character and camera in Unity 6.3 LTS (6000.3). Targets **Unity 6.3 LTS**.

Two controller styles dominate: a `CharacterController` moved by code (no rigidbody physics) and a
`Rigidbody` moved in `FixedUpdate`. Pick one deliberately — mixing them is the usual source of
double gravity and jitter.

## When to use

- Use when adding a first-person or third-person player, mouse look, jump/gravity, ground checks,
  slope or stair handling, or a follow camera that must not clip through walls.
- Use when a 3D character floats, sticks to walls, cannot jump, or the camera punches through
  geometry.

**When *not* to use:** 2D movement → `unity-2d-movement`; physics tuning and collision layers →
`unity-physics` / `physics-tuning`; animator controllers → `unity-animation`; input asset setup and
rebinding → `unity-input-system`; camera design as a concept → `camera-systems`; UI → `game-ui-ux`.

## Core workflow

1. **Choose the body.** `CharacterController` for crisp, animation-driven movement; `Rigidbody`
   when forces, moving platforms or ragdolls matter. Do not add both to one player.
2. **Build the rig.** Player root (yaw) → camera pivot (pitch) → camera for first person, or player
   root → orbit pivot → camera for third person. The controller and the visual are siblings, not
   parents of each other.
3. **Wire the Input System.** Move (Vector2), Look (Vector2), Jump (Button); bind them in
   `SetupPlayerInputComponent` or through `InputActionReference` fields. See `unity-input-system`.
4. **Move with gravity in code.** `CharacterController` does not apply gravity: accumulate vertical
   velocity yourself, reset it when grounded, and call `Move` once per frame for horizontal and
   once for vertical motion.
5. **Look with clamped pitch.** Yaw rotates the player root, pitch rotates the camera pivot, and
   pitch is clamped so the camera cannot flip over.
6. **Third-person camera with collision.** SphereCast from the pivot toward the desired camera
   position, pull the camera in on a hit, and smooth with a frame-rate-independent factor.
7. **Verify on real geometry.** Ramps near `slopeLimit`, steps near `stepOffset`, wall corners, and
   the camera against walls and ceilings.

## Patterns

### 1. First-person `CharacterController` with gravity and jump

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(CharacterController))]
public class FirstPersonController : MonoBehaviour
{
	[SerializeField] InputActionReference moveAction, lookAction, jumpAction;
	[SerializeField] Transform cameraPivot;
	[SerializeField] float moveSpeed = 6f, jumpHeight = 1.2f, gravity = -24f, mouseSensitivity = 0.12f;

	CharacterController controller;
	Vector3 verticalVelocity;
	float yaw, pitch;

	void Awake() => controller = GetComponent<CharacterController>();

	void Update()
	{
		Look();
		Move();
	}

	void Look()
	{
		Vector2 delta = lookAction.action.ReadValue<Vector2>() * mouseSensitivity;
		yaw += delta.x;
		pitch = Mathf.Clamp(pitch - delta.y, -89f, 89f);
		transform.rotation = Quaternion.Euler(0f, yaw, 0f);
		cameraPivot.localRotation = Quaternion.Euler(pitch, 0f, 0f);
	}

	void Move()
	{
		if (controller.isGrounded && verticalVelocity.y < 0f)
			verticalVelocity.y = -2f;                  // keep the capsule glued to the floor

		Vector2 input = moveAction.action.ReadValue<Vector2>();
		Vector3 move = transform.right * input.x + transform.forward * input.y;
		controller.Move(move * (moveSpeed * Time.deltaTime));

		if (jumpAction.action.WasPressedThisFrame() && controller.isGrounded)
			verticalVelocity.y = Mathf.Sqrt(jumpHeight * -2f * gravity);

		verticalVelocity.y += gravity * Time.deltaTime;
		controller.Move(verticalVelocity * Time.deltaTime);
	}
}
```

`isGrounded` is updated by `Move`, so check it after the horizontal move. Mouse delta is already a
per-frame value — multiply by sensitivity only, never by `Time.deltaTime` as well.

### 2. Ground check that also gives the slope normal

```csharp
[SerializeField] LayerMask groundMask = ~0;
[SerializeField] float groundProbe = 0.2f;

bool TryGround(out RaycastHit hit)
{
	Vector3 origin = transform.position + Vector3.up * 0.1f;
	float radius = controller.radius * 0.95f;
	return Physics.SphereCast(origin, radius, Vector3.down, out hit,
		groundProbe, groundMask, QueryTriggerInteraction.Ignore);
}
```

`isGrounded` is cheap but tells you nothing about the surface. A SphereCast supplies the normal for
slope limits and slide direction. Exclude the player's own layer from `groundMask`.

### 3. Slide off slopes steeper than the limit

```csharp
if (TryGround(out RaycastHit ground))
{
	float angle = Vector3.Angle(ground.normal, Vector3.up);
	if (angle > controller.slopeLimit)
	{
		Vector3 downhill = Vector3.ProjectOnPlane(Vector3.down, ground.normal).normalized;
		controller.Move(downhill * (5f * Time.deltaTime));
	}
}
```

`slopeLimit` blocks climbing steeper surfaces; it does not make the character slide. Project the
down vector onto the slope plane to get the downhill direction.

### 4. Third-person orbit camera with wall collision

```csharp
using UnityEngine;

public class OrbitCamera : MonoBehaviour
{
	[SerializeField] Transform pivot;
	[SerializeField] float distance = 4f, followSharpness = 12f, collisionRadius = 0.25f;
	[SerializeField] LayerMask collisionMask;

	void LateUpdate()
	{
		Vector3 origin = pivot.position;
		Vector3 direction = -pivot.forward;
		float targetDistance = distance;

		if (Physics.SphereCast(origin, collisionRadius, direction, out RaycastHit hit,
			distance, collisionMask, QueryTriggerInteraction.Ignore))
			targetDistance = Mathf.Max(0.2f, hit.distance - 0.05f);

		Vector3 desired = origin + direction * targetDistance;
		float t = 1f - Mathf.Exp(-followSharpness * Time.deltaTime);
		transform.position = Vector3.Lerp(transform.position, desired, t);
		transform.rotation = Quaternion.LookRotation(origin - transform.position, Vector3.up);
	}
}
```

`1 - exp(-k * dt)` is frame-rate independent; a raw `Lerp(a, b, k * dt)` changes feel with frame
rate. Pull the camera to `hit.distance` minus a small margin so the near plane does not clip.

### 5. Rigidbody variant

```csharp
void FixedUpdate()
{
	Vector2 input = moveAction.action.ReadValue<Vector2>();
	Vector3 dir = (transform.right * input.x + transform.forward * input.y).normalized;
	Vector3 velocity = rb.linearVelocity;              // Unity 6: velocity was renamed
	velocity.x = dir.x * moveSpeed;
	velocity.z = dir.z * moveSpeed;

	if (jumpQueued && TryGround(out _))
		velocity.y = Mathf.Sqrt(jumpHeight * -2f * gravity);

	rb.linearVelocity = velocity;
	jumpQueued = false;
}
```

Rigidbody code belongs in `FixedUpdate`; read input there and latch button presses in `Update`.
Use `MovePosition`/`MoveRotation` for kinematic bodies instead of writing `linearVelocity`.

## Pitfalls

- **`isGrounded` is false right after a jump** — it reflects the last `Move`; reset downward velocity
  only when grounded and do not re-check the jump in the same frame.
- **Double gravity** — a `CharacterController` applies no gravity, a `Rigidbody` does. Adding both
  makes jumps die instantly.
- **Mouse look feels sluggish at low FPS** — mouse delta is already frame-relative. Multiplying by
  `Time.deltaTime` scales it twice.
- **Camera flips at the poles** — pitch is unclamped. Clamp to roughly ±89°.
- **Camera clips through walls** — no SphereCast, or the cast starts inside the wall. Start at the
  pivot, add a small radius, and subtract a margin from the hit distance.
- **Character cannot climb stairs** — `stepOffset` is below the step height, or the step colliders
  are too thin for the capsule to resolve.
- **Character climbs walls** — `slopeLimit` is above the wall/ramp angle; lower it and add the slide
  above.
- **Moving platforms leave the player behind** — `CharacterController` is not carried by physics.
  Parent the player to the platform or add the platform's frame delta to `Move`.
- **`Rigidbody.velocity` does not compile** — Unity 6 renamed it to `linearVelocity` (and `drag` to
  `linearDamping`).
- **Ground check hits the player** — the SphereCast starts inside the player's own collider; use a
  ground layer mask and ignore the player layer.
- **Camera stutters** — the camera follows in `Update` while the body moves in `FixedUpdate`.
  Follow in `LateUpdate`, and optionally interpolate the Rigidbody.
- **Physics queries miss triggers** — pass `QueryTriggerInteraction.Collide` when triggers should
  count; the default ignores them.

## References

- Read `references/controllers-and-camera.md` for controller comparison, CharacterController
  tuning, ground-check options, camera rigs, layer setup and a playtest checklist.

## Related skills

- `unity-input-system` — actions, mapping contexts and rebinding for move/look/jump.
- `unity-physics` — colliders, layers, joints and physics settings.
- `physics-tuning` — timestep, interpolation and collision tuning in engine-neutral terms.
- `unity-2d-movement` — the 2D counterpart with `Rigidbody2D`.
- `unity-animation` — driving an Animator from the controller's speed and grounded state.
- `camera-systems` — follow, deadzone and shake design beyond this baseline.
- `platformer` / `fps-shooter` — genre rules layered on top of the controller.
