---
name: animation-systems
description: >
  Cross-engine character animation architecture: clips and parameters, state machines, blend
  trees/spaces, layers and masks, transitions, root motion, event markers and IK. Use for
  locomotion blends, attack/combo states, or when animations pop, slide, or fight physics.
---

# Animation systems

Animation is a state machine driven by gameplay parameters, not a bag of `play()` calls. This
skill covers the architecture that survives content growth: parameters, states, blends, layers,
root motion and events. It is **compositional**: pair it with an engine animation skill for the
concrete API.

## When to use

- Use when designing locomotion/combat animation state machines, blend trees, or layers.
- Use when animations pop, feet slide, attacks cancel wrong, or root motion fights the controller.

**When *not* to use:** a single looping idle/sprite flipbook → engine sprite skill
(`godot-animation`, `unity-animation`, `phaser-animation`, `pixijs-animation`); pure UI tweens →
`game-feel`; facial/lipsync pipelines → out of scope.

## The model

```text
gameplay params (speed, grounded, aim, stance)
        │
        ▼
state machine (idle / run / jump / attack / hit)
        │
        ▼
blend tree / blend space (1D speed, 2D directional)
        │
        ▼
layers + avatar masks (base body, upper-body aim, additive breathing)
        │
        ▼
final pose → skinning → render
```

- **Parameters** are the only bridge from code to animation. Keep them few and normalized.
- **States** own transitions; code requests states (`travel`, `CrossFade`), not clips.
- **Blend trees** interpolate clips by parameters; **blend spaces** by 1D/2D coordinates.
- **Layers** let upper-body actions (aim, reload) play over locomotion.
- **Events/notifies** fire gameplay at exact frames (hitbox on, footstep, combo window).

## Engine bindings

### Unity (Animator)

```csharp
static readonly int Speed = Animator.StringToHash("Speed");
static readonly int Attack = Animator.StringToHash("Attack");

void Update() {
    animator.SetFloat(Speed, velocity.magnitude, 0.1f, Time.deltaTime); // damped
    if (Input.GetButtonDown("Fire1")) animator.SetTrigger(Attack);
}

// Direct state control when the graph is in the way:
animator.CrossFade("Base Layer.Attack", 0.08f, 0, 0f);
```

- Parameter names include the layer for `CrossFade` (`"Base Layer.Run"`); precompute hashes.
- `SetTrigger` auto-resets when consumed — but a trigger set twice before consumption is lost;
  `ResetTrigger` when cancelling.
- Layers: set weight and mask in code for aim/upper-body overrides.
- `StateMachineBehaviour.OnStateEnter/Exit` for state-scoped logic; avoid gameplay logic buried in
  dozens of transitions.

### Godot (AnimationTree)

```gdscript
@onready var tree: AnimationTree = $AnimationTree
@onready var state: AnimationNodeStateMachinePlayback = tree["parameters/playback"]

func _physics_process(_delta: float) -> void:
    tree.set("parameters/locomotion/blend_position", velocity.length())
    if Input.is_action_just_pressed("attack"):
        state.travel("Attack")

func _on_attack_finished() -> void:
    state.travel("Locomotion")
```

- `AnimationTree` + `AnimationNodeStateMachine`; `travel()` walks the shortest path via A*.
- Blend spaces expose `blend_position`; 2D uses `Vector2`.
- `AnimationPlayer` alone is fine for simple props; `AnimationTree` for characters.
- Start the state machine (connect Start / call `start()`), or `travel()` does nothing.

### Unreal (Animation Blueprint)

- AnimBP with a state machine in the AnimGraph; Blend Spaces for locomotion.
- `Montage_Play` for one-shots; `Anim Notifies` for hit windows and footstep events.
- `Save/Persistent` variables on the AnimBP for state; use `Property Access` for performance.
- Upper-body slots + layered blend per bone for aim/reload.

## Patterns

### 1. Locomotion blend by speed (1D)

```text
blend_position = horizontal_speed / max_speed   # 0..1
Idle(0) ─ Walk(0.5) ─ Run(1.0)
```

- Normalize by the *actual* max speed; otherwise run clips never reach full playback.
- Damp the parameter (`SetFloat` with dampTime) so direction changes do not snap.
- Sync clip phases for walk/run to avoid foot sliding at blend midpoints.

### 2. Strafe blend space (2D)

```text
x = dot(velocity, right)
y = dot(velocity, forward)
```

- Use for lock-on/aim modes; forward-only blend for free running.
- Clamp magnitude to 1; the blend space samples the nearest clips.

### 3. Attack state with cancel windows

```text
Idle -> Attack (trigger)
Attack: startup -> active (hitbox on) -> recovery
  cancel into Combo only during [cancel_start, cancel_end] and only if has_hit
  cancel into Dodge during recovery
Attack -> Idle on clip end
```

- Put hitbox enable/disable on animation events, not timers, so they stay in sync.
- A `has_hit` flag prevents one swing hitting twice.
- Interrupt rules belong in code (or a small state machine), not in a web of AnyState
  transitions.

### 4. Root motion vs code-driven movement

- **Root motion**: clip moves the character; good for attacks, climbs, precise traversal.
- **Code-driven**: controller moves; good for responsive locomotion.
- Mixing both without a plan causes sliding and double movement.
- In Unity, `OnAnimatorMove` + `applyRootMotion`; in Godot, `root_motion_track`; in Unreal,
  `Root Motion Mode`.
- If using root motion for attacks, disable controller movement for that state.

### 5. Event markers

```text
frame 12: hitbox_on
frame 18: hitbox_off
frame 22: combo_window_open
frame 30: combo_window_close
frame 40: clip_end
```

- Keep markers in the clip, expose them as named events, and handle them in one listener.
- Idempotent handlers: re-entering a state can re-fire events; guard with state identity.
- For networked games, drive hit windows from the server tick, not local animation events.

### 6. Retargeting and scale

- Keep a shared skeleton/rig for humanoids; retarget clips rather than duplicating.
- Verify foot placement after retarget; IK foot lock fixes slope/stair sliding.
- Two-bone IK for hands on weapons; look-at for heads; enable only when needed (cost).

## Pitfalls

- **Transition explosion** → dozens of AnyState edges. Prefer code-driven `CrossFade`/`travel`
  with explicit rules.
- **Trigger eaten** → two `SetTrigger` calls before consumption; one is lost. Use a bool/counter
  or reset deliberately.
- **Feet slide** → blend parameter not normalized to actual speed, or clips out of phase.
- **Attack hits twice** → hitbox enabled by timer overlapping; use events + `has_hit`.
- **Animation cancels physics** → root motion and controller both move. Choose one owner.
- **Layer mask wrong** → upper-body action moves legs; verify avatar mask and layer weight.
- **State machine never starts** (Godot) → no Start connection; `travel()` silently does nothing.
- **Events fire on blend** → both source and target states fire; gate by state/weight.
- **Parameter drift** → code writes raw values while the graph also transitions on them; keep a
  single writer.
- **Everything in Update** → animation parameter writes in `LateUpdate`/after physics to match the
  final transform.

## Composition

- **Engine API:** `godot-animation`, `unity-animation`, `unreal-animation`, `roblox-animation`;
  sprite equivalents `phaser-animation`, `pixijs-animation`.
- **Movement:** `godot-2d-movement`/`unity-2d-movement`/`godot-3d-essentials` for the controller
  that owns velocity.
- **Feel:** `game-feel` for hit-stop and impact; do not freeze animation and physics differently.
- **Combat:** `fighting-game` for frame data; animation events must match the frame table.
- **Networking:** `multiplayer-netcode` — remote characters interpolate, so events cannot be
  purely local.

## References

- Read `references/state-machines-blending-and-root-motion.md` for graph design, blend math,
  root-motion ownership, event/IK checklists and debugging steps.
