# Defold GUI: layouts, adjust modes and input

Reference material for `SKILL.md`. Targets **Defold 1.14.0**.

## How a node is positioned

A GUI node's position is relative to its parent, and the scene's logical resolution comes
from `game.project` (`[display] width` / `height`). When the real window differs, Defold
adjusts the scene and then each node according to its anchors and adjust mode.

| Setting | Effect | Use for |
|---------|--------|---------|
| X/Y anchor `None` | Position stays measured from the parent's origin | Centered dialogs, sprites pinned to the middle |
| X anchor `Left` / `Right` | Keeps the distance from that edge | Corner HUD elements (score, lives, minimap) |
| Y anchor `Top` / `Bottom` | Keeps the distance from that edge | Top bars, bottom action buttons |
| Adjust `Fit` | Whole node stays visible, aspect kept | Text, icons, anything that must not distort |
| Adjust `Stretch` | Node stretches with the scene | Solid backgrounds, full-screen dimmers |
| Adjust `Zoom` | Node fills the scene, cropping the overflow | Background art that may bleed off-screen |

The GUI scene itself has an **Adjust Reference**: `Per Node` applies each node's adjust
mode against the resized parent, `Disable` freezes every node at its authored size. Most
projects want `Per Node`; `Disable` is for pixel-exact overlays.

## Layouts

Layouts let one `.gui` carry different compositions for different screen shapes. Each
layout stores its own node positions and sizes; at runtime Defold selects the layout that
matches the current resolution most closely, so there is no manual switching code.

Practical rules:

- Author the base layout at the project's logical resolution, then add a layout only when
  the composition must change (tall phone, ultra-wide), not for small size differences.
- Keep node ids identical across layouts; scripts look nodes up by id and must work in
  every layout.
- Test at 16:9, 4:3, 21:9 and a tall phone aspect. Toggle the layout preview in the editor
  instead of resizing the game window blindly.
- Anchors and adjust modes still apply inside a layout — a node anchored to the right edge
  stays there when the scene grows.

## Input in a GUI script

```lua
function init(self)
	msg.post(".", "acquire_input_focus")
end

function on_input(self, action_id, action)
	if action_id == hash("touch") then
		if action.pressed then
			-- action.x / action.y are screen coordinates
			local local_pos = gui.screen_to_local(gui.get_node("root"), vmath.vector3(action.x, action.y, 0))
			print("pressed at", local_pos)
		end
		if action.released then
			-- finish drags here
		end
	end
end
```

Fields worth knowing on `action`:

- `x`, `y` — pointer position in screen space; `dx`, `dy` — movement since the last sample.
- `pressed` / `released` — this sample started or ended a press.
- `repeated` — key auto-repeat; ignore it for buttons.
- `touch` — per-touch data for multi-touch actions; iterate it instead of assuming one finger.

Focus rules:

- `acquire_input_focus` pushes the component onto the input stack; the most recent
  acquirer receives input first.
- Returning `true` from `on_input` consumes the event. A modal menu should consume clicks
  so gameplay behind it never sees them.
- Always `release_input_focus` in `final()`; a destroyed screen that keeps focus can leave
  the stack pointing at a dead component.
- GUI input and game-object input use the same action ids from the project's input
  bindings, so a `"touch"` binding is visible to both. Choose one owner per action.

## Text, fonts and images

- `gui.set_text(node, text)` re-runs text layout. Updating score text every frame is fine
  for a HUD; rebuilding a 100-row list every frame is not — batch updates on change.
- Fonts are resources referenced by the node; switching styles at runtime means
  `gui.set_font(node, "font_name")`, not changing the text size.
- Texture nodes play flipbooks (`gui.play_flipbook`) and can be tinted with `gui.set_color`.
- Keep UI art in its own atlas and watch the scene's node budget in the editor; every clone
  counts against it.

## Resolution QA checklist

1. Open the `.gui` and preview every layout at the project resolution, 4:3, 16:9 and a
   tall phone aspect.
2. Check that corner HUD elements keep their margins and centered dialogs stay centered.
3. Click every button at the smallest and largest tested size; confirm the hit box matches
   the visible art, including scaled nodes.
4. Open a modal and confirm clicks do not reach gameplay behind it (input stack consumed).
5. Close and reopen the screen several times: node count should return to the baseline.
6. Run a desktop build for real pointer input; the headless engine has no pointer device,
   so a headless smoke test can verify startup but not clicking.
