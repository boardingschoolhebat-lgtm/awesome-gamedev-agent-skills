---
name: phaser-ui
description: >
  Build HUDs and menus in Phaser 4.2: in-canvas Containers with Text, NineSlice and Graphics,
  scrollFactor 0 and a separate UI camera, pointer events, Scale Manager resize handling, and
  DOM overlay elements for forms and rich text. Use when a Phaser game needs a HUD, menu, health
  bar, inventory, settings screen, or UI that stays fixed while the camera scrolls. Targets
  Phaser 4.2.
---

# Phaser UI

Phaser draws UI as game objects, or as HTML through DOM Elements. Pick one route per screen and
keep it independent of the scrolling world camera. Targets **Phaser 4.2**.

## When to use

- Use when adding a HUD, menu, pause overlay, health bar, inventory or settings screen.
- Use when UI scrolls with the world, is blurry at other sizes, or its buttons do not respond.

**When *not* to use:** UI design and hierarchy → `game-ui-ux`; scene lifecycle and loading →
`phaser-core`; collisions → `phaser-arcade-physics`; tile levels → `phaser-tilemap`.

## Choose the route first

| | In-canvas game objects | DOM Elements |
|-|------------------------|--------------|
| Best for | HUDs, health bars, counters, simple menus | forms, text inputs, rich HTML, accessibility |
| Styling | Phaser text/9-slice/graphics | CSS |
| Input | `setInteractive` + pointer events | native DOM events |
| Camera | fixed with `scrollFactor(0)` or a UI camera | respects scrollFactor but lives in an HTML overlay |
| Constraints | no text selection/inputs | one camera per scene with DOM; overlay alignment |

Do not mix both for the same widget; DOM elements sit above the canvas and can swallow clicks
meant for game objects.

## Core workflow (in-canvas)

1. **Pin UI to the camera.** `setScrollFactor(0)` on every UI object (or its Container), and put
   UI at a high `depth` so world objects never cover it.
2. **Group with a Container.** `this.add.container(x, y, children)` keeps a panel together for
   positioning, visibility and scroll factor; a Container's input hit area must be set
   explicitly.
3. **Use NineSlice for panels.** `this.add.nineslice(x, y, texture, frame, width, height,
   left, right, top, bottom)` stretches a bordered panel without distorting its corners.
4. **Text with a bitmap or web font.** `this.add.text(x, y, "HP", style).setOrigin(0, 0.5)`;
   set `resolution` or use a bitmap font when the canvas is scaled up.
5. **Handle resize.** Decide the scale mode (`FIT` letterboxes, `RESIZE` fills) and reposition
   UI from `this.scale.width/height` on the `resize` event.
6. **Wire input once.** `setInteractive({ useHandCursor: true })` then `pointerdown`/
   `pointerover`/`pointerout`; remove listeners when the panel is destroyed.
7. **Update through events.** Emit or listen to a game event (`this.game.events`,
   `this.registry.events`) instead of polling the player in `update()`.

## Patterns

### 1. A HUD Container that ignores the camera

```js
export default class HudScene extends Phaser.Scene {
  constructor() {
    super("hud");
  }

  create() {
    this.hpBar = this.add.rectangle(20, 20, 240, 18, 0x44cc66).setOrigin(0, 0.5);
    this.hpText = this.add.text(270, 20, "100", { fontFamily: "monospace", fontSize: "18px" })
      .setOrigin(0, 0.5);

    this.panel = this.add.container(16, 16, [this.hpBar, this.hpText]);
    this.panel.setScrollFactor(0).setDepth(1000);

    // Rebuild the bar on a game event instead of polling in update().
    this.registry.events.on("changedata-health", (_parent, value, previous) => {
      this.hpText.setText(String(value));
      this.hpBar.width = 240 * Phaser.Math.Clamp(value / 100, 0, 1);
    });
    this.events.once("shutdown", () => this.registry.events.off("changedata-health"));
  }
}
```

`setScrollFactor(0)` on the Container applies to its children, so the whole panel stays fixed
while the game camera moves. `depth` orders objects inside a scene; a separate UI scene is the
stronger isolation.

### 2. A separate UI camera

```js
create() {
  this.uiCamera = this.cameras.add(0, 0, this.scale.width, this.scale.height);
  this.uiCamera.setName("ui");

  // Tell each camera what it must not draw.
  this.mainCamera.ignore(this.uiLayer);
  this.uiCamera.ignore(this.worldLayer);
}
```

Two cameras need explicit ignore lists for every object: the main camera should not draw UI, and
the UI camera should not draw the world. With many objects, keep two `Phaser.GameObjects.Layer`s
and ignore whole layers. DOM Elements are only supported with a single camera per scene — use a
parallel UI scene instead of a second camera when mixing DOM and world.

### 3. Scale modes and resize

```js
const config = {
  type: Phaser.AUTO,
  parent: "game",
  scale: {
    mode: Phaser.Scale.FIT,          // letterbox and keep the design resolution
    autoCenter: Phaser.Scale.CENTER_BOTH,
    width: 1280,
    height: 720,
  },
  scene: [BootScene, GameScene, HudScene],
};

// Inside a scene: reposition from the actual size, not the design size.
this.scale.on("resize", (gameSize) => {
  this.panel.setPosition(16, gameSize.height - 80);
  this.uiCamera.setSize(gameSize.width, gameSize.height);
});
```

`FIT` keeps the aspect ratio and letterboxes; `RESIZE` matches the parent and requires every
layout to be computed from `scale.width/height`. Pick `FIT` for a fixed design resolution and
`RESIZE` for responsive layouts; do not assume `1920` from the config at runtime.

### 4. Buttons and menus

```js
const button = this.add.text(640, 360, "Play", {
  fontFamily: "monospace",
  fontSize: "32px",
  padding: { x: 24, y: 12 },
  backgroundColor: "#223344",
}).setOrigin(0.5).setScrollFactor(0).setInteractive({ useHandCursor: true });

button.on("pointerover", () => button.setStyle({ backgroundColor: "#335577" }));
button.on("pointerout", () => button.setStyle({ backgroundColor: "#223344" }));
button.on("pointerdown", () => this.scene.start("game"));
```

Phaser has no focus system: keyboard and gamepad navigation through a menu must be implemented
(cursor index + `keydown`/gamepad polling, a visible selection state). Mouse/touch input comes
free with `setInteractive`; make the hit area match the visible button, especially for Containers,
where it is not derived from children.

### 5. Pause overlay as its own scene

```js
// From the game scene:
this.scene.pause();
this.scene.launch("pause");

// PauseScene resumes it:
this.scene.resume("game");
this.scene.stop();
```

A separate scene gets its own camera, input and update loop, so the paused game does not keep
processing HUD input. Pass data through `scene.launch(key, data)` or the registry.

### 6. DOM overlay for forms and rich text

```js
const config = {
  type: Phaser.AUTO,
  parent: "game",
  dom: { createContainer: true },       // requires a parent element
  scale: { mode: Phaser.Scale.FIT, width: 1280, height: 720 },
};

// In a scene:
const form = this.add.dom(640, 360).createFromHTML(`
  <div class="settings">
    <label>Volume <input type="range" min="0" max="1" step="0.01" value="0.8"></label>
    <button id="close">Close</button>
  </div>
`);
form.setScrollFactor(0).setDepth(1000);
form.addListener("click");
form.on("click", (event) => {
  if (event.target.id === "close") this.closeSettings();
});
```

DOM elements live in an HTML div over the canvas, so CSS handles layout and native inputs work.
They respect `scrollFactor`, are clipped to the canvas, and need the `parent` config; without it
the DOM container is not created. Native DOM events do not bubble into Phaser input, so handle
them on the element or forward them explicitly.

## Pitfalls

- **HUD scrolls with the world** → missing `setScrollFactor(0)` on the object or its Container.
- **UI hidden behind sprites** → low `depth`, or drawn by the world camera. Raise `depth`, or use
  a UI camera/scene with ignore lists.
- **Buttons click through to the game** → overlapping interactive objects, or a DOM overlay
  covering the canvas. Check `depth`/input order and the DOM container's pointer-events.
- **DOM elements do not appear** → no `dom: { createContainer: true }` or no `parent` in the game
  config; both are required.
- **DOM + second camera misbehaves** → DOM Elements support one camera per scene. Use a parallel
  UI scene.
- **UI drifts after resize** → positions computed from the design resolution instead of
  `scale.width/height`, or no resize listener with `RESIZE` mode.
- **Blurry text when scaled** → the canvas is scaled up. Increase text `resolution`, use a bitmap
  font, or render UI at the display size.
- **Container does not respond to clicks** → a Container needs an explicit hit area/size;
  `setInteractive()` alone does not derive it from children.
- **Listeners pile up after restarting the scene** → scene events survive if bound to a global
  emitter; remove them on `shutdown`/`destroy`.
- **NineSlice corners distorted** → border sizes do not match the texture's corners, or the
  panel is smaller than the borders.
- **Registry event fires for the wrong key** → `changedata-<key>` matches the exact registry key;
  typos silently never fire.

## References

- Read `references/hud-cameras-and-dom.md` for the game-object/API table, camera ignore rules,
  scale-mode comparison, DOM constraints and a resize/input test checklist.

## Related skills

- `phaser-core` — scene lifecycle, loader and cameras.
- `phaser-arcade-physics` — gameplay behind the HUD.
- `game-ui-ux` — hierarchy, feedback, readability and accessibility.
- `pixijs-rendering` — a lower-level renderer when the UI is not a Phaser game object.
