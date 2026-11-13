# HUDs, cameras and DOM in Phaser 4.2

Depth for `phaser-ui`: the game objects that make a HUD, how cameras decide what they draw, and
the constraints of DOM overlays.

## API used by the skill

| API | Form | Notes |
|-----|------|-------|
| `this.add.container` | `(x, y, children?)` | Groups objects; set size for input. |
| `Container.setScrollFactor` | `(x, y?, updateChildren?)` | `0` pins to the camera. |
| `this.add.text` | `(x, y, text, style)` | Web fonts or bitmap text for pixel UI. |
| `this.add.rectangle` | `(x, y, width, height, color, alpha?)` | Bars and panels without a texture. |
| `this.add.nineslice` | `(x, y, texture, frame, width, height, left, right, top, bottom)` | Stretchable bordered panel. |
| `GameObject.setInteractive` | `(hitArea?, callback?, dropZone?)` | `{ useHandCursor: true }` is a common option. |
| `GameObject.setDepth` | `(value)` | Draw order within a scene. |
| `this.cameras.add` | `(x, y, width, height, makeMain?, name?)` | Extra camera for UI. |
| `Camera.ignore` | `(gameObject | array | layer)` | Exclude objects from a camera. |
| `this.scale.on` | `("resize", (gameSize, baseSize, displaySize, w, h) => {})` | Re-layout on size changes. |
| `this.add.dom` | `(x, y, element?)` | Requires `dom.createContainer` and `parent`. |
| `DOMElement.createFromHTML` | `(html)` | Builds the element from a string. |

## Camera strategies

| Strategy | Use when | Cost |
|----------|----------|------|
| One camera + `scrollFactor(0)` | small HUD, few elements | simplest; UI still in the world scene |
| Two cameras + layers | HUD over a scrolling world | explicit ignore lists, no DOM |
| Separate UI scene | menus, DOM, pause, independent input | one more scene and camera |

Rules:

- Every object must be ignored by the camera that should not draw it; a new object defaults to
  being drawn by every camera.
- Prefer two `Layer`s (world, ui) and `camera.ignore(layer)` over long object lists.
- DOM Elements: one camera per scene.
- A UI scene runs in parallel with `this.scene.launch("hud")`; pause the game scene without
  pausing the HUD.

## Scale modes

| Mode | Behaviour | Layout work |
|------|-----------|-------------|
| `Phaser.Scale.FIT` | fits the parent, keeps aspect, letterboxes | design at a fixed resolution |
| `Phaser.Scale.ENVELOP` | covers the parent, crops | anchor UI to safe margins |
| `Phaser.Scale.RESIZE` | matches parent size exactly | compute layout from `scale.width/height` |
| `Phaser.Scale.NONE` | fixed canvas | manual sizing |

`autoCenter: Phaser.Scale.CENTER_BOTH` centers the canvas in the parent. On resize, re-anchor
from the current game size; a HUD placed at `x = 1200` in a 1280-wide design will fall outside a
narrower `RESIZE` canvas.

## Nine-slice panels

```js
const panel = this.add.nineslice(640, 360, "ui", "panel", 480, 280, 24, 24, 24, 24);
panel.setScrollFactor(0);
```

The four border values are the corner sizes in pixels; the middle stretches. A panel smaller
than the borders cannot be drawn correctly, and an atlas frame with wrong borders shows seams.

## Input notes

- `setInteractive()` on a Container requires `container.setSize(w, h)` first; children's bounds
  are not used automatically.
- `pointerdown` fires for mouse and touch; add `pointerup`/`pointerout` for press states.
- Disable input on hidden screens: `container.disableInteractive()` or `visible = false` plus a
  guard, otherwise invisible buttons still catch clicks.
- Phaser has no built-in focus ring/navigation. For gamepad and keyboard menus, keep a selection
  index, draw the highlight, and handle `keydown-UP/DOWN/ENTER` (or poll the gamepad) yourself.
- DOM elements receive native events; Phaser's input system does not see them. Forward the
  actions you need into scene methods.

## Test checklist

1. Scroll the world: HUD stays fixed, no UI drifts or clips at the edges.
2. Resize the window (and rotate a phone): HUD re-anchors, text stays readable.
3. Click/tap every button at 1x and at a scaled canvas: hit areas match visuals.
4. Pause menu: game pauses, menu still receives input, resume restores gameplay input.
5. Restart the scene twice: no duplicate registry/input listeners or doubled score updates.
6. DOM form: appears over the canvas, inputs accept typing, close button works, canvas clicks
   still reach the game where expected.
7. Gamepad/keyboard: menu navigation is possible without a mouse.
8. Depth: UI above sprites, tooltips above panels, no flicker between equal-depth objects.
