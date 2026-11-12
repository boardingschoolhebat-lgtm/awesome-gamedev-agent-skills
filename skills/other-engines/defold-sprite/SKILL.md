---
name: defold-sprite
description: >
  Animate sprites in Defold 1.14.0: atlas and tile-source flipbooks, playback modes, pivot and trim,
  sprite.play_flipbook, completion callbacks and animation chains, facing flips, playback rate and
  runtime atlas swaps. Use when a project has .sprite or .atlas files, or the request mentions a
  Defold sprite, flipbook animation, animation_done, sprite.play_flipbook, set_hflip, or a sprite
  that is offset from its collision object.
---

# Defold sprites and flipbooks

Render and animate sprite components in Defold 1.14.0. Targets **Defold 1.14.0**.

A sprite component draws one image or plays a flipbook from an **atlas** or a **tile source**.
Animation data (frame list, fps, flips) is authored in the atlas; the script only names the
animation and controls playback.

## When to use

- Use when adding or fixing sprite rendering, flipbook animation, facing direction, animation
  chaining, or a sprite whose art does not line up with its collision shape.
- Use when a project contains `.sprite` or `.atlas` files, or when an animation must react to
  gameplay state (idle → run → jump → attack).

**When *not* to use:** HUD and menus → `defold-ui`; tile grids → `defold-tilemap`; collision
shapes and physics messages → `defold-collision`; juice and feedback timing → `game-feel`;
atlas packing and draw-call budgets → `performance-optimization`; core structure and messages →
`defold-core`.

## Core workflow

1. **Author the atlas.** Add images, group frames into an animation, then set its `Id`, `Fps`,
   `Playback` and flip flags. Frames are 1-based indices and may repeat, reorder or skip
   geometries (a run cycle can reuse one leg image).
2. **Set the pivot per image.** Pivot is in normalized units: `(0, 0)` top-left, `(1, 1)`
   bottom-right. The pivot is the point the sprite centers on, so it decides whether the art sits
   on the collision shape or beside it.
3. **Configure the component.** Choose the atlas or tile source as `Image`, set `Default
   Animation`, `Material`, `Blend Mode` and `Size Mode` (automatic unless you resize in code).
4. **Play by name.** Call `sprite.play_flipbook("#sprite", "run")`; the animation must exist in
   the assigned atlas. Chain animations through the completion callback, not by counting frames.
5. **Flip for facing.** Use `sprite.set_hflip` / `set_vflip` on top of the atlas flips; flipping
   twice cancels the atlas flip.
6. **Verify visually.** The headless engine draws nothing, so check animation timing, pivot and
   blending in the editor or a desktop bundle.

## Patterns

### 1. Play once and chain on completion

```lua
local function on_attack_done(self, message_id, message, sender)
	if message_id == hash("animation_done") and message.id == hash("attack") then
		sprite.play_flipbook("#sprite", "idle")
	end
end

function attack(self)
	sprite.play_flipbook("#sprite", hash("attack"), on_attack_done)
end
```

The callback signature is `(self, message_id, message, sender)`, where `message.id` is the
finished animation and `message.current_tile` its last frame. If you pass no callback, the same
information arrives as an `animation_done` message instead.

### 2. Face the direction of travel

```lua
function update(self, dt)
	local velocity = go.get("#co", "linear_velocity")
	if velocity.x ~= 0 then
		sprite.set_hflip("#sprite", velocity.x < 0)
	end
end
```

Only flip when the sign changes if you also use the atlas flip flags; setting the same value is
harmless, but mixing code flips with atlas flips makes the art look mirrored twice.

### 3. Playback rate and starting offset

```lua
sprite.play_flipbook("#sprite", "walk", nil, {
	playback_rate = 1.5,   -- must be positive
	offset = 0.5,          -- normalized start position in the animation
})
```

Use `playback_rate` to scale speed with movement, and `offset` to start an action mid-cycle (for
example, continuing a run cycle after an attack). There is no pause value: playback rate must be
positive, so pause by switching to a single-frame animation.

### 4. Query size for effects and UI anchoring

```lua
local size = go.get("#sprite", "size")     -- pixels, before game object scaling
```

`size` and `slice` are only meaningful, and only settable, when the sprite's `Size Mode` is
manual. With automatic size the editor derives them from the image.

### 5. Swap the atlas at runtime

```lua
go.property("skin", resource.atlas("/assets/player_alt.atlas"))

function set_skin(self)
	go.set("#sprite", "image", self.skin)
	sprite.play_flipbook("#sprite", "idle")   -- replay against the new atlas
end
```

Animation frame data comes from the driving texture, so replay the animation after the swap.
Assets that must line up (frame counts, pivots) should match the original atlas.

## Pitfalls

- **Completion callback never runs** — callbacks fire only when an animation plays to its end;
  looping animations never complete. Chain loops by hand or use a finite animation.
- **`animation_done` never arrives** — you passed a callback, so the message is not sent. Pick
  one mechanism per play call.
- **Ping-pong stops on frame two** — `Once Ping Pong` plays to the last frame, reverses, and stops
  on the second frame, not the first. Author a return frame if the loop must close seamlessly.
- **Sprite art is offset from its collision object** — the image pivot is not centered. Fix the
  pivot in the atlas rather than compensating with a child game object.
- **`Size Mode auto` blocks size changes** — `size` and `slice` cannot be set on automatic
  sprites. Switch the component to manual first.
- **Flip looks wrong on some frames** — the atlas animation already has a flip flag; code flips
  stack on top of it.
- **Slice-9 looks stretched or broken** — sprite trim mode and slice-9 are incompatible. Turn
  trim off for nine-sliced panels.
- **Animation name not found** — the id is hashed per atlas; check spelling and that the sprite
  uses the atlas that defines it.
- **Swapped atlas keeps old timing** — animation data (fps, frame list) comes from the first
  texture ("driving animation"); replay after swapping and keep frame counts aligned.
- **Sprite invisible but the object exists** — no default animation set, playback set to `None`,
  the material is additive/alpha and the color is transparent, or the z-order puts it behind a
  tilemap.
- **No animation appears in a headless test** — headless renders nothing. Verify visuals in the
  editor or a desktop bundle and assert on state, not pixels.

## References

- Read `references/atlas-and-playback.md` for atlas animation properties, playback modes, pivot
  and trim rules, runtime sprite properties and a visual QA checklist.

## Related skills

- `defold-core` — game objects, components, messages and script lifecycle.
- `defold-collision` — shapes and physics messages that drive animation state.
- `defold-tilemap` — tile-based levels behind the sprite.
- `defold-ui` — HUD and menus drawn with GUI nodes instead of sprites.
- `game-feel` — hit pause, squash and timing that make flipbooks read well.
- `performance-optimization` — atlas packing, draw calls and texture budgets.
