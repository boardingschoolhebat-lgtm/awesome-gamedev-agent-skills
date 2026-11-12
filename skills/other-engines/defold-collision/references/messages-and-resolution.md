# Defold collisions: types, groups, messages and resolution

Reference material for `SKILL.md`. Targets **Defold 1.14.0**.

## Collision object types

| Type | Moved by | Collides with | Use for |
|------|----------|---------------|---------|
| Dynamic | physics (gravity, forces, velocity) | dynamic, kinematic, static | Players, props, projectiles |
| Kinematic | `go.set_position` from code | dynamic, static (pushes dynamic) | Moving platforms, doors |
| Static | nothing | dynamic, kinematic | Level geometry |
| Trigger | nothing | objects whose masks match | Pickups, checkpoints, damage zones |

Shapes: box, sphere and capsule, embedded in the `.collisionobject` or a separate shape resource.
Static and trigger objects do not need mass; dynamic objects do.

## Groups and masks

Every collision object has a `Group` and a `Mask`. A collision or message happens only when each
object's mask contains the other object's group:

```text
player  group=player  mask=ground,enemy
enemy   group=enemy   mask=player
ground  group=ground  mask=player
```

- If the player masks `enemy` but the enemy does not mask `player`, no collision is reported.
- A trigger must be in the other object's mask and must itself mask the other group.
- Tilemaps take their groups from the tile source, not from the collision object component.
- Change groups at runtime with `physics.set_group` and `physics.set_maskbit`; read them with
  `physics.get_group` / `physics.get_maskbit`.

## Message fields

### collision_response

Sent when one object is dynamic, kinematic or static. Once per colliding pair per frame.

| Field | Type | Meaning |
|-------|------|---------|
| `other_id` | hash | Instance id of the other object |
| `other_position` | vector3 | World position of the other object |
| `other_group` | hash | Collision group of the other object |
| `own_group` | hash | Collision group of this object |

Use it for hit-once logic (bullet hits enemy, pickup collected).

### contact_point_response

Sent when one object is dynamic or kinematic and the other is dynamic, kinematic or static.
Several messages can arrive per pair per frame.

| Field | Type | Meaning |
|-------|------|---------|
| `position` | vector3 | World position of the contact point |
| `normal` | vector3 | Contact normal, pointing from the other object towards this one |
| `relative_velocity` | vector3 | Relative velocity as seen from the other object |
| `distance` | number | Penetration depth, non-negative |
| `applied_impulse` | number | Impulse the contact produced |
| `mass` / `other_mass` | number | Mass of this / the other object (kg) |
| `other_id` | hash | Instance id of the other object |
| `other_position` | vector3 | World position of the other object |
| `other_group` / `own_group` | hash | Groups of the other / this object |

`life_time` exists but is not currently used by the engine.

### trigger_response

Sent once when overlap starts and once when it ends.

| Field | Type | Meaning |
|-------|------|---------|
| `other_id` | hash | Instance id of the other object |
| `enter` | boolean | `true` on entry, `false` on exit |
| `other_group` / `own_group` | hash | Groups of the other / this object |

### Event filtering

Each collision object has *Generate Collision Events*, *Generate Contact Events* and *Generate
Trigger Events* flags, all enabled by default. With the default message handler, a component
receives a message if its own flag is set; disabling both sides suppresses the event. A custom
listener set with `physics.set_event_listener` replaces message delivery.

## Resolving contacts

```lua
local GROUND = hash("ground")

function fixed_update(self, dt)
	for _, contact in ipairs(self.contacts) do
		if contact.group == GROUND then
			local pos = go.get_position()
			go.set_position(pos + contact.normal * contact.distance)
		end
	end
	self.contacts = {}
end

function on_message(self, message_id, message, sender)
	if message_id == hash("contact_point_response") then
		self.contacts[#self.contacts + 1] = {
			normal = message.normal,
			distance = message.distance,
			group = message.other_group,
		}
	end
end
```

Rules that keep resolution stable:

- With `[physics] use_fixed_timestep = 1`, physics messages are dispatched before `fixed_update`;
  collect them and apply corrections there.
- Resolve every contact point, not just the first.
- Push out along `normal * distance` (or `-normal * distance` depending on which body you move).
- Do not use `go.set_position` on a dynamic body for regular movement — only for depenetration.
- Zero the velocity component into the surface when you want the object to slide instead of bounce.

## Raycasts

```lua
local hits = physics.raycast(from, to, { hash("ground"), hash("enemy") })
if hits and hits[1] then
	local hit = hits[1]
	-- hit.fraction  (0 at from, 1 at to)
	-- hit.position  (world position)
	-- hit.normal    (surface normal)
	-- hit.id        (instance id)
	-- hit.group     (hashed group)
end
```

- Kinematic, dynamic and static objects are tested; triggers are skipped.
- Objects containing the start point are ignored (Box2D limitation).
- `physics.raycast_async(from, to, groups, request_id)` answers later with `ray_cast_response`
  (`fraction`, `position`, `normal`, `id`, `group`, `request_id`) or `ray_cast_missed`
  (`request_id`).
- Use raycasts for hitscan weapons, line of sight and ground probes; use shapes for continuous
  overlap.

## Runtime helpers

| Call | Effect |
|------|--------|
| `physics.set_gravity(v)` / `physics.get_gravity()` | Collection gravity (z ignored in 2D) |
| `physics.set_group(url, group)` | Change an object's group |
| `physics.set_maskbit(url, group, enabled)` | Add or remove a group from the mask |
| `physics.set_hflip(url, flip)` / `set_vflip` | Flip shapes without flipping the sprite |
| `physics.update_mass(url)` | Recompute mass after changing shape scale (2D dynamic) |
| `physics.wakeup(url)` | Wake a sleeping body after teleporting it |

## Debug checklist

1. Physics debug on: every shape visible and aligned with its art.
2. Test each group pairing in both directions; confirm no message is silently masked out.
3. Trigger: enter, stay, exit, and two occupants at once.
4. Fast projectile vs thin wall: no tunneling.
5. Contact resolution: no jitter while standing still, no sinking into slopes.
6. Raycast from inside and outside a shape; confirm the documented start-point limitation.
7. Desktop bundle run: headless simulates physics but draws nothing, so shapes and input need a
   real window.
