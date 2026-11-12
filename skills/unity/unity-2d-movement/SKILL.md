---
name: unity-2d-movement
description: >
  Build 2D character controllers in Unity 6.3 LTS with Rigidbody2D: platformer
  run and jump with gravity, coyote time, jump buffering and variable jump height,
  top-down 8-direction movement, layer-masked ground checks with Physics2D overlap
  queries, and kinematic movers with MovePosition. Use when scripting a 2D player or
  enemy, fixing a Rigidbody2D that slides, sticks to walls or tunnels through floors,
  or moving code from velocity/drag to Unity 6's linearVelocity/linearDamping.
---

# Unity 2D Movement (Rigidbody2D)

Make 2D characters move and feel right with Unity 6.3 LTS's built-in 2D physics.
Targets **Unity 6.3 LTS (6000.3)**.

> **Unity 6 renames:** `Rigidbody2D.velocity` → **`linearVelocity`**, `drag` →
> **`linearDamping`**, `angularDrag` → **`angularDamping`**. The old names still compile
> but are obsolete, and the API Updater offers the rename. Write the new names.
> Unity 6 also adds single-axis `linearVelocityX` / `linearVelocityY`.

## When to use

- Use when writing a 2D player or enemy that moves and collides: platformer (gravity +
  jump), top-down 8-direction, side-scroller with slopes, or a kinematic mover.
- Use when a `Rigidbody2D` character slides on its own, sticks to walls, sinks through
  the floor, tunnels at high speed, or ignores jump input.

**When *not* to use:** forces, joints, effectors, collision layers, or non-character
bodies → `unity-physics`; action maps and rebinding → `unity-input-system`; full
platformer structure (levels, hazards, goals) → the `platformer` genre skill;
engine-agnostic timestep/CCD tuning → `physics-tuning`.

The snippets read the legacy Input Manager (`Input.GetAxisRaw`) so they run without
extra packages. With the Input System package, read the same values from an
`InputAction` and keep the same `Update` → `FixedUpdate` split.

## Core workflow

1. **Configure the `Rigidbody2D`.** Body Type **Dynamic** for physics-driven movement,
   `gravityScale = 1` for platformers (0 for top-down), **Freeze Rotation Z**,
   **Interpolation** on for visual smoothness, and **Collision Detection** `Continuous`
   for fast falls.
2. **Split input from physics.** Read input in `Update`, store intent, and apply it in
   `FixedUpdate` so movement is frame-rate independent.
3. **Pick one movement mode.** Write `linearVelocity` for velocity-driven characters,
   or call `MovePosition` on a kinematic body for elevators and moving platforms. Never
   mix both on the same body.
4. **Ground-check with a query, not a guess.** Overlap a small box or circle at the feet
   against a dedicated ground `LayerMask`; the player's own collider must not be in it.
5. **Add forgiveness.** Coyote time, a jump buffer, and variable jump height are what
   make a platformer feel responsive; all three are timers around the same jump.
6. **Verify in context.** Watch the ground-check gizmo, the Physics 2D debugger, and
   `linearVelocity` in the Inspector while playing; a missing layer bit looks exactly
   like "jump does nothing".

## Patterns

### 1. Platformer controller: coyote time, jump buffer, variable jump height

```csharp
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D))]
public sealed class PlatformerController2D : MonoBehaviour
{
    [Header("Movement")]
    [SerializeField] private float moveSpeed = 7f;
    [SerializeField] private float acceleration = 60f;
    [SerializeField] private float jumpVelocity = 12f;

    [Header("Forgiveness")]
    [SerializeField] private float coyoteTime = 0.1f;
    [SerializeField] private float jumpBufferTime = 0.12f;
    [Range(0f, 1f)] [SerializeField] private float jumpCutMultiplier = 0.45f;

    [Header("Ground check")]
    [SerializeField] private Transform groundCheck;
    [SerializeField] private Vector2 groundCheckSize = new(0.46f, 0.1f);
    [SerializeField] private LayerMask groundMask;

    private Rigidbody2D _rb;
    private float _moveX;
    private float _coyoteTimer;
    private float _bufferTimer;
    private bool _jumpCutQueued;

    private void Awake()
    {
        _rb = GetComponent<Rigidbody2D>();
        _rb.constraints = RigidbodyConstraints2D.FreezeRotation;
        _rb.interpolation = RigidbodyInterpolation2D.Interpolate;
        _rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
    }

    private void Update()
    {
        // Latch per frame: FixedUpdate may run zero or several times per frame.
        _moveX = Input.GetAxisRaw("Horizontal");
        if (Input.GetButtonDown("Jump")) _bufferTimer = jumpBufferTime;
        if (Input.GetButtonUp("Jump")) _jumpCutQueued = true;
    }

    private void FixedUpdate()
    {
        float dt = Time.fixedDeltaTime;
        bool grounded =
            Physics2D.OverlapBox(groundCheck.position, groundCheckSize, 0f, groundMask) != null;

        _coyoteTimer = grounded ? coyoteTime : Mathf.Max(0f, _coyoteTimer - dt);
        _bufferTimer = Mathf.Max(0f, _bufferTimer - dt);

        Vector2 velocity = _rb.linearVelocity;
        velocity.x = Mathf.MoveTowards(velocity.x, _moveX * moveSpeed, acceleration * dt);

        if (_bufferTimer > 0f && _coyoteTimer > 0f)
        {
            velocity.y = jumpVelocity;   // full jump
            _bufferTimer = 0f;
            _coyoteTimer = 0f;
        }
        else if (_jumpCutQueued && velocity.y > 0f)
        {
            velocity.y *= jumpCutMultiplier;   // button released early: shorter hop
        }

        _jumpCutQueued = false;
        _rb.linearVelocity = velocity;
    }

    private void OnDrawGizmosSelected()
    {
        if (groundCheck == null) return;
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireCube(groundCheck.position, groundCheckSize);
    }
}
```

Keep `linearDamping` at 0 and control deceleration with `acceleration`; damping fights
your jump arc and makes it mushy.

### 2. Ground check variants

```csharp
// Round feet read better with a circle; a box matches a rectangular collider.
private bool IsGrounded() =>
    Physics2D.OverlapCircle(groundCheck.position, 0.12f, groundMask) != null;
```

`Rigidbody2D.IsTouchingLayers(groundMask)` is not a substitute: it reports *any*
contact, so a character hugging a wall or bumping a ceiling counts as grounded.

### 3. Top-down 8-direction movement

```csharp
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D))]
public sealed class TopDownMover2D : MonoBehaviour
{
    [SerializeField] private float moveSpeed = 5f;

    private Rigidbody2D _rb;
    private Vector2 _input;

    private void Awake()
    {
        _rb = GetComponent<Rigidbody2D>();
        _rb.gravityScale = 0f;
        _rb.constraints = RigidbodyConstraints2D.FreezeRotation;
    }

    private void Update() =>
        _input = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));

    private void FixedUpdate() =>
        _rb.linearVelocity = _input.normalized * moveSpeed;   // diagonals are not faster
}
```

### 4. Kinematic mover with MovePosition

```csharp
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D))]
public sealed class KinematicMover2D : MonoBehaviour
{
    [SerializeField] private Vector2 velocity = new(3f, 0f);

    private Rigidbody2D _rb;

    private void Awake() => _rb = GetComponent<Rigidbody2D>();

    // Set Body Type to Kinematic in the Inspector.
    private void FixedUpdate() =>
        _rb.MovePosition(_rb.position + velocity * Time.fixedDeltaTime);
}
```

`MovePosition` interpolates the body between physics steps and still pushes dynamic
bodies out of the way, unlike writing `transform.position`.

## Pitfalls

- **Moving with `transform.position`** teleports a dynamic body, skips collision
  resolution and breaks interpolation. Use `linearVelocity`, `AddForce`, or
  `MovePosition`.
- **Writing velocity in `Update`** makes movement frame-rate dependent and jittery.
  Physics belongs in `FixedUpdate`.
- **`GetButtonDown` polled in `FixedUpdate`** can miss a press (or read it twice)
  because it may run zero or several times per frame. Latch input in `Update`.
- **Obsolete `velocity` / `drag` / `angularDrag` warnings** are the Unity 6 renames;
  use `linearVelocity`, `linearDamping`, `angularDamping`.
- **Character sticks to walls** when the collider has friction. Assign a
  `PhysicsMaterial2D` with friction 0 to the player collider; use friction only where
  you want it (ice, conveyor belts).
- **Ground check that never triggers** is usually a layer-mask mismatch or a gizmo
  that sits inside the player's own collider. Exclude the player layer and draw the
  check in the Scene view.
- **`IsTouchingLayers` says grounded while climbing a wall.** Prefer an overlap query
  placed at the feet.
- **Fast falls tunnel through floors.** Set Collision Detection to `Continuous`
  (it sweeps against static colliders); for fast-vs-fast pairs, cast ahead with
  `Physics2D.BoxCast` before moving.
- **Mixing `MovePosition` and `linearVelocity`** makes the body fight itself. Choose
  kinematic or dynamic per body.
- **Reading `transform.position` for gameplay** lags one physics step when
  interpolation is on. Read `Rigidbody2D.position` instead.
- **Rotating the sprite by setting `transform.rotation`** bypasses the physics body.
  Rotate with `Rigidbody2D.MoveRotation` when the collider should follow.
- **`gravityScale` left at 1 in a top-down game** makes everything drift downward;
  set it to 0 and move with `linearVelocity`.

## References

- For moving platforms, one-way platforms, slopes, ladders, dashes and animation hooks,
  read `references/controller-recipes.md`.

## Related skills

- `unity-physics` — Rigidbody semantics, colliders, joints, layers, raycasts.
- `unity-input-system` — action maps, rebinding, and reading movement as a `Vector2`.
- `unity-tilemap-2d` — building the tile levels this character walks on.
- `unity-animation` — driving Animator states from speed and grounded flags.
- `physics-tuning` / `game-feel` — cross-engine timestep, jitter and juice.
- `platformer` — genre structure: levels, hazards, goals and camera.
