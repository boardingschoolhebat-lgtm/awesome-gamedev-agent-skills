---
name: defold-collision
description: >
  Set up and debug collisions in Defold 1.14.0: collision object types (dynamic, kinematic, static,
  trigger), box/sphere/capsule shapes, collision groups and masks, collision_response,
  contact_point_response and trigger_response handling, contact resolution, forces and velocities,
  and physics.raycast probes. Use when a project has .collisionobject files, or the request mentions
  Defold collision, passing through walls, triggers, collision groups, raycasts, or physics messages.
---

# Defold collisions

Wire collision objects and react to them in Defold 1.14.0. Targets **Defold 1.14.0**.

Collision objects live as components on game objects; the physics world sends messages to the
owning script, and the API (`physics.*`) covers gravity, groups, raycasts, shapes and joints.

## When to use

- Use when setting up collision shapes, groups/masks, triggers or raycasts, or when objects fall
  through floors, jitter, or never report a hit.
- Use when a project contains `.collisionobject` files or scripts handling `collision_response`,
  `contact_point_response` or `trigger_response`.

**When *not* to use:** engine-neutral physics tuning (timestep, mass, CCD, layering strategy) →
`physics-tuning`; tile collisions and tile sources → `defold-tilemap`; core structure, messages
and factories → `defold-core`; movement feel and platformer rules → `platformer` / `game-feel`.

## Core workflow

1. **Inspect the physics setup.** Read `game.project` (`[physics] gravity`,
   `fixed_update_frequency`, `use_fixed_timestep`) and the existing `.collisionobject` components
   before adding new ones.
2. **Pick the body type.** *Dynamic* obeys forces and gravity; *kinematic* is moved by code but
   still pushes dynamic bodies; *static* never moves; *trigger* only reports overlaps.
3. **Add shapes and groups.** Attach box/sphere/capsule shapes, set `Group` and `Mask`, and make
   the masks mutual — if either side masks the other out, no message is sent.
4. **Choose the message.** `collision_response` for hit-once logic, `contact_point_response` when
   you must separate objects, `trigger_response` for zones that fire on enter and exit.
5. **Resolve in the fixed step.** With `use_fixed_timestep = 1`, physics messages arrive before
   `fixed_update`; move bodies there, not in a variable-rate `update`.
6. **Verify with physics debug.** Toggle *Debug ▸ Toggle Physics Debug*, confirm shapes line up
   with art, then test each group pairing and trigger entry/exit.

## Patterns

### 1. Trigger zone with enter/exit

```lua
local PLAYER = hash("player")

function init(self)
	self.inside = 0
end

function on_message(self, message_id, message, sender)
	if message_id == hash("trigger_response") and message.other_group == PLAYER then
		if message.enter then
			self.inside = self.inside + 1
		else
			self.inside = math.max(0, self.inside - 1)
		end
	end
end
```

`trigger_response` fires once on entry and once on exit. Count occupants instead of toggling a
boolean, or two players standing in the zone will switch it off when one leaves.

### 2. Separate a body from contact points

```lua
local GROUND = hash("ground")

function on_message(self, message_id, message, sender)
	if message_id == hash("contact_point_response") and message.other_group == GROUND then
		-- normal points from the other object towards this one
		local pos = go.get_position()
		go.set_position(pos + message.normal * message.distance)
	end
end
```

One collision pair can produce several contact points per frame. Resolve every point, and do it
in `fixed_update` when the fixed timestep is enabled so the correction matches the simulated step.

### 3. Drive a dynamic body

```lua
-- velocity: metres per second, read and written on the collision object
go.set("#co", "linear_velocity", vmath.vector3(200, 0, 0))

-- force: applied at a world position, in newtons, dynamic bodies only
msg.post("#co", "apply_force", {
	force = vmath.vector3(0, 800, 0),
	position = go.get_position(),
})
```

Never move a dynamic body with `go.set_position` for gameplay motion — it teleports the body and
skips collision response. Use velocity or `apply_force`; move kinematic bodies with
`go.set_position`.

### 4. Ground probe with a raycast

```lua
local SOLID = { hash("ground"), hash("platform") }

function is_grounded(self)
	local from = go.get_position()
	local to = from + vmath.vector3(0, -40, 0)
	local hits = physics.raycast(from, to, SOLID)
	return hits ~= nil and hits[1] ~= nil
end
```

`physics.raycast` hits dynamic, kinematic and static objects but skips triggers, and ignores any
object that contains the ray's start point (a Box2D limitation), so start the ray outside the
player's own shape. `physics.raycast_async` reports through `ray_cast_response` /
`ray_cast_missed` with a `request_id`.

### 5. Change groups at runtime

```lua
physics.set_group("#co", "enemy")
physics.set_maskbit("#co", "player", true)    -- add a group to this object's mask
```

Use this for phase changes (dead enemies stop colliding with bullets) instead of disabling the
collision object, which also stops its messages.

## Pitfalls

- **Nothing ever collides** — the masks are not mutual, the collision object has no shape, or the
  shape is on a different game object than the sprite. Check *Debug ▸ Toggle Physics Debug*.
- **Player falls through the floor at speed** — thin static shapes plus a fast dynamic body tunnel.
  Thicken the floor, slow the body, or enable continuous collision on the object.
- **Objects stick or jitter on contact** — resolving only one of several contact points per frame,
  or resolving in `update` while physics runs on a fixed step. Resolve all points in `fixed_update`.
- **`contact_point_response` normal pushes the wrong way** — the normal points from the other
  object towards the current one. Subtract `normal * distance` to push away instead of adding it.
- **Trigger never fires** — a trigger still needs a mask that includes the other group, and the
  other object's mask must include the trigger's group. Triggers do not produce contact points.
- **Raycast hits nothing** — the start point is inside the target's shape (ignored by Box2D), the
  group table is empty, or the target is a trigger.
- **`collision_response` arrives once but contact points flood** — that is expected: one collision
  response per pair per frame, several contact points depending on geometry.
- **Moving a kinematic body shakes the world** — kinematic bodies are moved by `go.set_position`
  and push dynamic bodies; do not also set their `linear_velocity`.
- **A bullet passes through enemies** — mass and speed ratio is extreme. Prefer a raycast for hitscan
  weapons, or continuous collision for fast projectiles.
- **Messages stop after re-enabling an object** — `disable`/`enable` on a collision object keeps its
  groups, but a script that assumed a single enter event may be out of sync; re-check zone counts.
- **Gravity seems wrong in one collection** — `physics.set_gravity` affects only the collection it is
  called from, and the z component is ignored in 2D.

## References

- Read `references/messages-and-resolution.md` for body types, group/mask rules, exact message
  fields, the resolution algorithm, raycast options and a debug checklist.

## Related skills

- `physics-tuning` — timestep, mass, drag, CCD and layering strategy in engine-neutral terms.
- `defold-core` — game objects, components, messages and the script lifecycle.
- `defold-tilemap` — tile collisions and tilesource collision groups.
- `platformer` — ground checks, coyote time and one-way platforms built on these messages.
- `game-ai` — line-of-sight raycasts and steering around obstacles.
