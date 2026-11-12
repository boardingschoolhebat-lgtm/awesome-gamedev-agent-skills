---
name: defold-ui
description: >
  Build HUDs, menus and dialogs in Defold 1.14.0 with GUI scenes and gui scripts: box,
  text and texture nodes, health bars, cloned list rows, gui.animate tweens, input focus
  with gui.pick_node, anchors, adjust modes and per-resolution layouts. Use when a
  project has .gui or .gui_script files, or the request mentions a Defold HUD, menu,
  inventory screen, health bar, button, gui.new_text_node, gui.animate, gui.pick_node,
  or UI that must survive different screen sizes.
---

# Defold UI (GUI scenes)

Build screen-space UI in Defold 1.14.0 with `.gui` scenes driven by `.gui_script` files.
Targets **Defold 1.14.0**.

GUI is its own world: nodes live in a `.gui` scene, not in game objects, and a GUI script
sees the `gui` namespace — `go` functions such as `go.get_position` are not available.

## When to use

- Use when building or fixing a HUD, pause/settings menu, inventory screen, dialog, health
  bar, button, floating label or any layout that must scale across resolutions.
- Use when a project contains `.gui` files or `.gui_script` files, or when input clicks
  reach the game but never the UI.

**When *not* to use:** game objects, components, message routing or factories →
`defold-core`; the design of the HUD itself (hierarchy, focus order, safe areas) →
`game-ui-ux`; input rebinding → `input-systems`; animated sprites inside the world →
`defold-core` plus the sprite manuals.

## Core workflow

1. **Create the scene.** Add a `.gui` file, place its nodes in the editor, and give every
   node that the script touches a unique id. Attach a `.gui_script` and add the GUI as a
   component on a game object in the collection.
2. **Design for resolution.** Set X/Y anchors for edge-anchored HUD parts, and an adjust
   mode for nodes whose content must keep its aspect ratio. Add layouts when the screen
   shape changes the composition, not just the size.
3. **Acquire input once.** Call `msg.post(".", "acquire_input_focus")` in `init()`, handle
   `on_input(self, action_id, action)`, and release focus in `final()` when the screen closes.
4. **Hit-test before acting.** `gui.pick_node(node, action.x, action.y)` uses the node's
   bounds and respects pivot, scale and visibility; only then run the button action.
5. **Push state in, do not poll.** Let gameplay send messages (`msg.post("#hud", "set_health",
   { ratio = 0.4 })`) and update nodes in the GUI script's `on_message`.
6. **Animate with `gui.animate`.** Animate properties (`"position.y"`, `"color.w"`, vectors)
   with an easing and duration; the engine does the tween and calls your completion function.
7. **Verify in context.** Preview the `.gui` at several resolutions in the editor, then run a
   desktop build — the headless engine has no pointer, so input paths need a real window.

## Patterns

### 1. Lifecycle, input focus and a button

```lua
-- hud.gui_script
function init(self)
	msg.post(".", "acquire_input_focus")     -- without focus, on_input is never called
	self.play_button = gui.get_node("play_button")
end

function on_input(self, action_id, action)
	if action_id == hash("touch") and action.pressed then
		if gui.pick_node(self.play_button, action.x, action.y) then
			msg.post("#controller", "play_pressed")   -- component on the same game object
			return true                               -- consume: lower listeners skip it
		end
	end
	return false
end

function final(self)
	msg.post(".", "release_input_focus")
end
```

Input arrives only while the component holds focus; returning `true` stops the event from
reaching listeners lower on the input stack, which is how a modal menu blocks gameplay.

### 2. Message-driven HUD update

```lua
-- hud.gui_script
function init(self)
	self.bar = gui.get_node("health_fill")
	self.score = gui.get_node("score_value")
	self.bar_full_width = gui.get_size(self.bar).x   -- capture once, not per message
end

function on_message(self, message_id, message, sender)
	if message_id == hash("set_health") then
		local ratio = math.max(0, math.min(1, message.ratio))
		local height = gui.get_size(self.bar).y
		gui.set_size(self.bar, vmath.vector3(self.bar_full_width * ratio, height, 0))
	elseif message_id == hash("set_score") then
		gui.set_text(self.score, tostring(message.value))
	end
end
```

Resize a bar against a stored maximum width; asking for the current size every time
compounds rounding and shrinks the bar permanently.

### 3. Animate a panel with a completion callback

```lua
function open(self)
	local panel = gui.get_node("panel")
	gui.set_position(panel, vmath.vector3(480, -320, 0))   -- start below the screen
	gui.animate(panel, "position.y", 320, gui.EASING_OUTBACK, 0.35, 0, function()
		msg.post("#controller", "menu_opened")
	end)
end

function close(self)
	local panel = gui.get_node("panel")
	gui.animate(panel, "position.y", -320, gui.EASING_INBACK, 0.25)
end
```

`gui.animate` replaces an animation already running on that property; cancel explicitly
with `gui.cancel_animations(node, "position.y")` when state changes mid-tween.

### 4. Dynamic list rows from a template

```lua
function init(self)
	self.row_template = gui.get_node("row_template")   -- keep it off-screen in the .gui
	self.rows = {}
end

function set_items(self, items)
	for _, row in ipairs(self.rows) do
		gui.delete_node(row)
	end
	self.rows = {}

	for index, item in ipairs(items) do
		local row = gui.clone(self.row_template)
		gui.set_position(row, vmath.vector3(0, -48 * (index - 1), 0))
		gui.set_text(row, item.label)
		self.rows[#self.rows + 1] = row
	end
end
```

Keep the reference returned by `gui.clone`; dynamically created nodes have no stable id to
look up later. Delete the previous rows or the scene leaks nodes on every refresh.

## Pitfalls

- **`on_input` never fires** — the script never posted `acquire_input_focus` to `"."`, or
  another component higher on the input stack consumed the event. Acquire in `init()` and
  check the stack when a menu opens.
- **Clicks only work sometimes** — the hit box comes from the node's size, pivot and scale.
  A text node sized automatically is only as wide as its text; set Size Mode to Manual for
  buttons.
- **Hidden nodes still take clicks** — pickable state follows the node's visible/enabled
  property. Close the screen (or disable the node) rather than moving it far away.
- **Coordinates look wrong** — `action.x` / `action.y` are screen coordinates. Convert with
  `gui.screen_to_local(node, vmath.vector3(action.x, action.y, 0))` before using them as
  node positions.
- **`attempt to call field 'get_position' (a nil value)`** — GUI scripts have no `go`
  namespace. Read node transforms with `gui.get_position` / `gui.get_size` / `gui.get_scale`.
- **Text is blurry or clipped** — the font size and the node's size mode disagree. Fix the
  font, or scale the node and accept the filtering; do not stretch a text node's size.
- **Bar shrinks every update** — reading the current size and multiplying it. Store the
  maximum once in `init()`.
- **Nodes drift off-screen on phones** — anchors and adjust modes were never set, so the
  layout assumes one resolution. Preview 16:9, 4:3 and a tall phone layout in the editor.
- **`gui.clone` rows pile up** — deleting the game object does not delete GUI nodes. Delete
  rows explicitly when the screen closes or refreshes.
- **Messages to `"."` do nothing** — in a GUI script `"."` is the GUI component, not the
  game object holding it. Address the game object's other components by `"#id"` or by path.
- **Animating the same property twice per frame** — the second `gui.animate` cancels the
  first. Drive one animation per property, and read the completion callback before starting
  the next step.

## References

- For anchors, adjust modes, layout selection, the input action fields, fonts and a QA
  checklist across resolutions, read `references/layouts-and-input.md`.

## Related skills

- `game-ui-ux` — HUD/menu hierarchy, focus order, safe areas and readability.
- `defold-core` — game objects, scripts, messages, factories and Bob builds.
- `input-systems` — bindings, gamepad and rebinding that feed GUI actions.
- `game-feel` — juice for menus and HUD feedback; pair with `gui.animate`.
- `localization`-style text growth is not covered here: keep labels short and test the
  longest translation manually.
