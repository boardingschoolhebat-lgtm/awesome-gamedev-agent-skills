# Events, layout and text (PixiJS v8.22)

Depth for `pixijs-ui`: the federated event model, hit testing, layout math and text rendering.

## Event modes

| `eventMode` | Emits events | Hit tested | Use for |
|-------------|--------------|------------|---------|
| `none` | no | no (children skipped) | pure visuals, hidden UI |
| `passive` (default) | no | no (interactive children still work) | grouping containers |
| `auto` | no | only if parent is interactive | v7 `interactive = false` equivalent |
| `static` | yes | yes | buttons, panels, drag targets |
| `dynamic` | yes | yes, plus synthetic updates each tick | moving objects under a stationary cursor |

Rules:

- A listener never fires unless the object's `eventMode` is `static` or `dynamic`.
- `none` skips the whole subtree; use it to disable a menu wholesale.
- `interactiveChildren = false` skips children hit testing but keeps the container testable.
- `isInteractive()` returns true only for `static`/`dynamic`.
- `hitArea` overrides bounds-based hit testing.

## Pointer events

| Event | When |
|-------|------|
| `pointerdown` | press on the object |
| `pointerup` | release over the object |
| `pointerupoutside` | release outside the object that got `pointerdown` |
| `pointermove` | pointer moves while over the object |
| `pointerover` / `pointerout` | enter/leave, do not bubble |
| `pointertap` | quick press+release on the same object |
| `pointercancel` | interaction cancelled (touch lost) |
| `globalpointermove` | every move, hit or not (v8 replacement for old canvas-wide moves) |

v8 breaking change: `pointermove`/`mousemove` fire only when the pointer is over a display object.
Use `globalpointermove` for drag that continues outside the object.

`event.stopPropagation()` prevents the event reaching objects below; `event.target` is the
top-most hit object.

## Hit testing order

1. Top-most child first (reverse render order, respecting `zIndex` when `sortableChildren`).
2. `eventMode = "none"` skips the subtree.
3. `interactiveChildren = false` skips children of that container.
4. `hitArea` replaces bounds if present.
5. Bounds come from the object's local geometry transformed to world space.

Performance:

- Use `none` for decorative elements.
- Prefer `hitArea` rectangles/circles/polygons over complex bounds.
- Set `interactiveChildren = false` on panels where only the panel handles clicks.
- Avoid `dynamic` unless the object moves while the pointer is still.

## Cursors

```js
button.cursor = "pointer";
draggable.cursor = "grab";
```

`buttonMode` was removed in v8. Use `cursor`; custom CSS cursors are accepted too.

## Layout and anchors

- `Container` has no layout; position children manually.
- `Sprite`/`Text` anchors are normalized (0–1); `anchor.set(0.5)` centers on the position.
- `Graphics` has no anchor; draw from `(0,0)` and position the container.
- `app.screen` is the logical render size; `app.canvas` is the DOM element.
- `resizeTo: window` plus `autoDensity: true` keeps CSS size and backing store in sync.
- `renderer.on("resize", fn)` re-layouts on window changes.
- For scaling UI, put everything under one root and set `root.scale.set(uiScale)`, then re-layout
  using `app.screen.width / uiScale`.
- `zIndex` only sorts when `sortableChildren = true` on the parent; enable it on the UI root.

Safe area:

```js
const margin = 24;
const safe = {
  x: margin,
  y: margin,
  width: app.screen.width - margin * 2,
  height: app.screen.height - margin * 2,
};
```

## Text options

| Option | Effect |
|--------|--------|
| `fontFamily`, `fontSize`, `fontWeight` | web font stack; load fonts before measuring |
| `fill` | color, gradient or pattern |
| `wordWrap`, `wordWrapWidth` | line breaking |
| `align` | `left`/`center`/`right` for wrapped lines |
| `lineHeight`, `letterSpacing` | spacing control |
| `stroke` | outline for text over busy scenes |
| `dropShadow` | shadow/glow |
| `resolution` | rasterization density (crispness) |
| `padding` | avoid clipped glyphs/outlines |

- `Text` re-rasterizes when `text` changes; update numbers at a lower rate.
- `BitmapText` uses a pre-generated font atlas: fastest for scores/timers, but fixed sizes and
  limited styling.
- Measure with `text.width`/`text.height` after setting content, before positioning.
- Load custom fonts before creating text, or the first frame uses a fallback and mis-measures.

## UI test checklist

1. Every button responds to mouse and touch; hover/press states reset on `pointerupoutside`.
2. Modal blocks gameplay clicks (click through the scrim does nothing).
3. Hidden/disabled buttons do not fire; disabled state is visually distinct.
4. Resize and device rotation: layout recomputes, nothing clips off-screen.
5. UI scale option: text and hit areas scale together.
6. HiDPI: text sharp at 1x/2x; no half-pixel positions.
7. Keyboard/gamepad path (if implemented): focus ring and activation, not pointer-only.
8. Long localized strings: wrap or truncate without overlapping buttons (`localization`).
9. z-order: HUD above world, modal above HUD, tooltip above modal.
10. Performance: no per-frame `Graphics` rebuild or text re-rasterization in the HUD.
