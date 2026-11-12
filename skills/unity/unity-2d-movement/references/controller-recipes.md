# 2D controller recipes

Deeper variations on the `Rigidbody2D` controller in `SKILL.md`. Every snippet targets
**Unity 6.3 LTS (6000.3)** and the `linearVelocity` / `linearDamping` names.

## Moving platforms that carry the player

A platform with a **Kinematic** `Rigidbody2D` moved by `MovePosition` pushes the player
and carries it through friction. A player standing on it keeps its own horizontal
velocity, so it slides off an accelerating platform. Two fixes:

```csharp
// On the player: add the platform's delta while standing on it.
private Vector2 _lastPlatformPosition;

private void OnCollisionEnter2D(Collision2D collision)
{
    if (collision.collider.TryGetComponent(out MovingPlatform2D platform))
        _lastPlatformPosition = platform.Rb.position;
}

private void OnCollisionExit2D(Collision2D collision) => _lastPlatformPosition = default;
```

```csharp
// Simpler alternative: parent the player while it stands still on the platform,
// then unparent on jump. Parenting a physics body is only safe when the platform
// does not rotate and the player is not moving relative to it.
private void OnCollisionEnter2D(Collision2D collision)
{
    if (collision.collider.CompareTag("MovingPlatform"))
        transform.SetParent(collision.transform, worldPositionStays: true);
}

private void OnCollisionExit2D(Collision2D collision)
{
    if (collision.collider.CompareTag("MovingPlatform"))
        transform.SetParent(null, worldPositionStays: true);
}
```

Do not move the platform with `transform.position`: a kinematic body moved that way
does not push riders reliably.

## One-way platforms

Put a `PlatformEffector2D` on the platform and enable **Use One Way**. Each collider
that should be one-way needs **Used By Effector** checked.

```csharp
// Drop through: ignore the platform collider briefly instead of disabling it.
private void DropThrough(Collider2D platformCollider)
{
    Physics2D.IgnoreCollision(_playerCollider, platformCollider, true);
    StartCoroutine(RestoreAfter(0.35f, platformCollider));
}

private IEnumerator RestoreAfter(float seconds, Collider2D platformCollider)
{
    yield return new WaitForSeconds(seconds);
    Physics2D.IgnoreCollision(_playerCollider, platformCollider, false);
}
```

Disabling the platform collider is tempting, but it also removes the platform for every
other actor and can leave riders falling through at the wrong moment.

## Slopes

Give the player a frictionless `PhysicsMaterial2D`, then keep the body attached on
downhills and remove the uphill speed that would launch it:

```csharp
private bool TryGetGround(out RaycastHit2D hit) =>
    hit = Physics2D.Raycast(groundCheck.position, Vector2.down, 0.15f, groundMask);

private void ApplySlopeStick()
{
    if (!TryGetGround(out RaycastHit2D hit)) return;

    // Project horizontal velocity onto the slope so speed is constant on the surface.
    Vector2 along = Vector2.Perpendicular(hit.normal) * Mathf.Sign(_rb.linearVelocity.x);
    Vector2 velocity = _rb.linearVelocity;
    velocity = along * Vector2.Dot(velocity, along);
    velocity.y -= 2f;   // small downward bias keeps contact on the way down
    _rb.linearVelocity = velocity;
}
```

Steep slopes need a separate rule: above a maximum angle, let the character slide back
down (or block the movement) rather than climbing at full speed.

## Ladders and climbing

```csharp
private void EnterLadder()
{
    _onLadder = true;
    _rb.gravityScale = 0f;
}

private void TickLadder()
{
    Vector2 velocity = _rb.linearVelocity;
    velocity.y = Input.GetAxisRaw("Vertical") * climbSpeed;
    _rb.linearVelocity = velocity;
    if (Input.GetButtonDown("Jump")) ExitLadder(jumpVelocity);
}

private void ExitLadder(float jumpVelocity) 
{
    _onLadder = false;
    _rb.gravityScale = 1f;
    _rb.linearVelocity = new Vector2(_rb.linearVelocity.x, jumpVelocity);
}
```

Turn gravity off while climbing instead of zeroing velocity every frame; that keeps
horizontal control usable and avoids fighting the physics step.

## Dash with a timer, not accumulated forces

```csharp
private IEnumerator Dash(Vector2 direction)
{
    float originalGravity = _rb.gravityScale;
    _rb.gravityScale = 0f;

    float elapsed = 0f;
    while (elapsed < dashTime)
    {
        _rb.linearVelocity = direction * dashSpeed;
        elapsed += Time.fixedDeltaTime;
        yield return new WaitForFixedUpdate();   // stay in step with physics
    }

    _rb.gravityScale = originalGravity;
    _rb.linearVelocity *= dashEndSpeedMultiplier;
}
```

`WaitForFixedUpdate` keeps the dash length in physics steps, so it behaves the same at
any framerate.

## Animation and feedback hooks

```csharp
private static readonly int SpeedHash = Animator.StringToHash("Speed");
private static readonly int GroundedHash = Animator.StringToHash("Grounded");
private static readonly int VerticalHash = Animator.StringToHash("VerticalVelocity");

private void LateUpdate()
{
    _animator.SetFloat(SpeedHash, Mathf.Abs(_rb.linearVelocity.x));
    _animator.SetBool(GroundedHash, _grounded);
    _animator.SetFloat(VerticalHash, _rb.linearVelocity.y);
}
```

Publish physics results to the Animator in `LateUpdate`, after the step has settled, and
prefer cached property hashes over strings. Squash/stretch and landing dust belong in
`game-feel`, not in the movement controller.

## Ceiling and ledge tests

```csharp
// Ceiling check before a full jump so the character does not clip its head.
private bool HasHeadroom(float distance) =>
    Physics2D.Raycast(headCheck.position, Vector2.up, distance, groundMask) == false;

// Ledge grab: probe just past the feet, then check the space above it.
private bool CanGrabLedge()
{
    Vector2 ahead = (Vector2)transform.position + new Vector2(_facing * 0.4f, 0f);
    bool wall = Physics2D.Raycast(ahead, Vector2.right * _facing, 0.1f, groundMask);
    bool free = Physics2D.Raycast(ahead + Vector2.up * 0.6f, Vector2.right * _facing, 0.1f, groundMask) == false;
    return wall && free;
}
```

Both probes use the same ground mask, so the level geometry must be on that layer for
ledge detection to work. Keep the masks in sync when you add layers.
