---
name: pixijs-ui
description: >
  Build UI in PixiJS v8: menu and HUD Containers, Graphics panels, Text and BitmapText,
  eventMode and pointer events, hitArea and cursor, buttons with hover/press states, manual
  layout and anchor math, resolution and crisp text, modal input blocking and z-order. Use when
  a PixiJS game needs menus, HUD, buttons, tooltips or dialogs. Targets PixiJS v8.22.
---

# PixiJS UI

PixiJS is a renderer, not a UI framework: menus and HUDs are `Container` trees drawn in the same
scene graph as gameplay. This skill covers the event model, layout math, text crispness and input
blocking. Targets **PixiJS v8.22**.

## When to use

- Use when a PixiJS game needs a menu, HUD, pause screen, dialog, tooltip or clickable button.
- Use when buttons do not respond, text is blurry, layout breaks on resize, or clicks pass
  through a modal.

**When *not* to use:** sprites, textures and the render loop → `pixijs-rendering`; HUD/UX design →
`game-ui-ux`; DOM overlays instead of canvas UI → `threejs-ui` (same idea); accessibility →
`accessibility`.

## Core workflow

1. **One UI root Container** added to `app.stage` last, so it draws above gameplay.
2. **Build panels from `Graphics`** (`roundRect().fill().stroke()` in v8) and text from `Text` or
   `BitmapText`.
3. **Set `eventMode` explicitly.** v8 default is `passive`; only `static`/`dynamic` receive events.
4. **Use `pointertap`** for buttons (tap = press+release on the object), `pointerover`/`pointerout`
   for hover, and `cursor = "pointer"`.
5. **Lay out from `app.screen`** and re-run layout on resize; PixiJS has no flexbox.
6. **Block input behind modals** with a full-screen scrim that has `eventMode = "static"`.
7. **Keep UI text crisp**: `resolution` on text, integer positions, and `autoDensity` on the app.

## Patterns

### 1. UI root and a panel

```js
import { Application, Container, Graphics, Text } from "pixi.js";

const app = new Application();
await app.init({ background: "#101820", resizeTo: window, autoDensity: true, resolution: window.devicePixelRatio });
document.body.appendChild(app.canvas);

const ui = new Container();
ui.eventMode = "static";          // container itself can receive events
app.stage.addChild(ui);           // add last: draws on top

const panel = new Graphics()
  .roundRect(0, 0, 420, 260, 16)
  .fill({ color: 0x1b2733, alpha: 0.96 })
  .stroke({ width: 2, color: 0x3d5166 });
ui.addChild(panel);
```

v8 Graphics is a builder: create the shape, then `.fill()`/`.stroke()`. `beginFill`/`drawRect` are
v7 APIs.

### 2. Buttons that actually work

```js
function makeButton(label, onClick) {
  const button = new Container();
  button.eventMode = "static";
  button.cursor = "pointer";

  const bg = new Graphics()
    .roundRect(0, 0, 240, 56, 10)
    .fill(0x2a6fdb);
  const text = new Text({
    text: label,
    style: { fill: "#ffffff", fontSize: 22, fontFamily: "system-ui, sans-serif" },
  });
  text.anchor.set(0.5);
  text.position.set(120, 28);

  button.addChild(bg, text);
  button.on("pointerover", () => bg.tint = 0x9ecbff);
  button.on("pointerout", () => bg.tint = 0xffffff);
  button.on("pointerdown", () => button.scale.set(0.98));
  button.on("pointerup", () => button.scale.set(1));
  button.on("pointerupoutside", () => button.scale.set(1));
  button.on("pointertap", onClick);
  return button;
}
```

- `pointertap` fires only if press and release happen on the same object; `pointerupoutside`
  resets state when the pointer leaves.
- `tint` works on a `Graphics` fill; it multiplies the drawn colors.
- Disabled buttons: `eventMode = "none"`, `alpha = 0.5`, and skip the handler — do not rely on
  alpha alone.
- Give the container a `hitArea` when the visual bounds are not the clickable area:
  `button.hitArea = new Rectangle(0, 0, 240, 56)`.

### 3. Text and crisp rendering

```js
const title = new Text({
  text: "Paused",
  style: { fontFamily: "system-ui, sans-serif", fontSize: 48, fontWeight: "700", fill: "#ffffff" },
});
title.resolution = 2;             // render text at 2x, scale down for HiDPI
title.anchor.set(0.5);
title.position.set(app.screen.width / 2, 80);
ui.addChild(title);
```

- `Text` rasterizes to a texture; changing `text` often re-rasterizes. For frequently updating
  numbers use `BitmapText` with a bitmap font, or update sparingly.
- `resolution` on text or the app keeps glyphs sharp on HiDPI.
- Round positions for text (`Math.round`) to avoid half-pixel blur.
- `BitmapText` requires a loaded bitmap font (`Assets.load`); its `style.fontName` must match.
- Very long text: set `style.wordWrap = true` and `style.wordWrapWidth`.

### 4. Layout without a layout engine

```js
function layoutMenu() {
  const { width, height } = app.screen;
  panel.position.set((width - 420) / 2, (height - 260) / 2);
  title.position.set(width / 2, height / 2 - 80);
  buttons.forEach((b, i) => b.position.set((width - 240) / 2, height / 2 - 10 + i * 68));
}
app.renderer.on("resize", layoutMenu);
layoutMenu();
```

- `app.screen` is the logical size; use it rather than `window.innerWidth` so CSS scaling works.
- Anchor the layout to the screen or a safe area; store normalized positions for odd aspect
  ratios.
- For real flow layout (rows, wrapping, padding), add a layout library or compute boxes yourself;
  PixiJS does not reflow.
- Keep a `uiScale` factor on the UI root for an accessibility/UI-size option, and re-layout after
  changing it.

### 5. Modal input blocking and z-order

```js
const scrim = new Graphics()
  .rect(0, 0, app.screen.width, app.screen.height)
  .fill({ color: 0x000000, alpha: 0.6 });
scrim.eventMode = "static";       // eats clicks aimed at gameplay underneath
scrim.hitArea = app.screen;       // Rectangle covering the whole screen
modal.addChild(scrim);

ui.sortableChildren = true;       // respect zIndex within the UI root
modal.zIndex = 100;
```

- A modal must have a full-screen interactive scrim; otherwise clicks reach the game.
- `eventMode = "none"` on a container skips it **and its children** — use `passive` for containers
  that only group interactive children.
- Set `interactiveChildren = false` on a container when only the container itself needs hits.
- `sortableChildren` costs sorting per frame; enable it on UI roots, not on every container.

### 6. HUD updates

```js
const healthBar = new Graphics();
function setHealth(ratio) {
  healthBar.clear()
    .roundRect(0, 0, 200, 16, 8)
    .fill(0x332222)
    .roundRect(0, 0, 200 * Math.max(0, Math.min(1, ratio)), 16, 8)
    .fill(0x35c46a);
}
```

Redraw on change, not every frame; a `Graphics` rebuild per frame is wasted geometry. For animated
bars, scale a filled sprite instead.

## Pitfalls

- **Nothing is clickable** → `eventMode` left at `passive` (v8 default). Set `static` on buttons
  and on their parent containers as needed.
- **Clicks fall through a menu** → no full-screen interactive scrim; add one.
- **Clicks hit hidden buttons** → `visible = false` does not stop hit testing by itself in every
  case; also set `eventMode = "none"` or remove the child.
- **Blurry text** → low text resolution, fractional positions, or a scaled container. Set
  `resolution`, round positions, avoid scaling text containers.
- **Layout breaks on resize** → absolute pixel positions with no resize hook. Lay out from
  `app.screen` and listen to `renderer.on("resize")`.
- **v7 code copied** → `beginFill`/`drawRect`/`interactive`/`buttonMode` are gone. Use
  `rect().fill()`, `eventMode`, `cursor`.
- **Hover state stuck after touch** → handle `pointerupoutside` and `pointercancel`.
- **UI under gameplay** → the UI root was added before the world container. Add it last or raise
  `zIndex` with `sortableChildren`.
- **Per-frame Graphics rebuild** → jank on low-end devices. Redraw only on value change.
- **Text re-rasterized every frame** → updating `text` with a timer value each tick. Throttle or
  use `BitmapText`.

## References

- Read `references/events-layout-and-text.md` for the v8 event-mode table, pointer event list,
  hit-testing rules, layout/anchor math, text options and a UI test checklist.

## Related skills

- `pixijs-rendering` — Application, sprites, textures and the ticker this UI sits on.
- `game-ui-ux` — hierarchy, feedback and readability.
- `accessibility` — remapping, contrast and scalable UI.
- `phaser-ui` — equivalent HUD/menu work in Phaser.
- `threejs-ui` — DOM-overlay UI for a WebGL scene.
