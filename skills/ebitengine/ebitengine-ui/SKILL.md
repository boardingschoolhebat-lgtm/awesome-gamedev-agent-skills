---
name: ebitengine-ui
description: >
  Build UI in Ebitengine (Go): immediate-mode menus and HUDs drawn with vector and text/v2,
  mouse/touch/keyboard hit testing, buttons with hover and press states, scaling and safe areas
  with Layout, crisp TrueType text, modal input blocking and focus navigation. Use when an
  Ebitengine game needs menus, HUD, buttons or dialogs. Targets Ebitengine v2.10.5.
---

# Ebitengine UI

Ebitengine has no widget toolkit: UI is drawn each frame into the screen image and hit-tested in
`Update`. This immediate-mode approach is small and fast if input is read once per tick and layout
is computed in logical coordinates. Targets **Ebitengine v2.10.5**.

## When to use

- Use when an Ebitengine game needs a menu, HUD, pause screen, button, dialog or tooltip.
- Use when clicks miss buttons, text is blurry, UI breaks on resize, or clicks pass through a
  modal.

**When *not* to use:** game loop, images and input basics → `ebitengine-core`; presentation
design → `game-ui-ux`; accessibility options → `accessibility`.

## Core workflow

1. **Pick a logical resolution** in `Layout` (e.g. 320×180 or 640×360) and draw UI in those
   coordinates; let Ebitengine scale to the window.
2. **Read input once per `Update`** with `inpututil` (`IsMouseButtonJustPressed`,
   `IsKeyJustPressed`, touch IDs) and store a UI input snapshot.
3. **Lay out** rects in logical space; keep them in one place so draw and hit test share numbers.
4. **Hit test** with `image.Rect(...).Contains(point)`; use `ebiten.CursorPositionF()` for
   sub-pixel/high-DPI consistency.
5. **Draw** panels with `vector.DrawFilledRect`/`StrokeRect` and text with `text/v2`.
6. **Block input** behind modals with a full-screen scrim rect that consumes clicks.
7. **Support keyboard/gamepad focus** so menus are not pointer-only.

## Patterns

### 1. Logical layout and input snapshot

```go
type Game struct {
    mouseX, mouseY float64
    clicked        bool
    keys           []ebiten.Key
}

func (g *Game) Layout(outsideWidth, outsideHeight int) (int, int) {
    return 640, 360          // logical screen; everything below uses these units
}

func (g *Game) Update() error {
    g.mouseX, g.mouseY = ebiten.CursorPositionF()
    g.clicked = inpututil.IsMouseButtonJustPressed(ebiten.MouseButtonLeft)
    g.keys = inpututil.AppendJustPressedKeys(g.keys[:0])
    return nil
}
```

`CursorPositionF` returns a logical position consistent with `Layout`; use it instead of the
integer `CursorPosition` when buttons are small or the window is scaled.

### 2. A button

```go
type Button struct {
    Rect  image.Rectangle
    Label string
    Hover bool
    Down  bool
}

func (b *Button) Update(mx, my float64, pressed, released bool) bool {
    inside := image.Pt(int(mx), int(my)).In(b.Rect)
    b.Hover = inside
    if inside && pressed {
        b.Down = true
    }
    if b.Down && released {
        b.Down = false
        return inside            // click only if released inside
    }
    return false
}

func (b *Button) Draw(screen *ebiten.Image, face text.Face) {
    bg := color.RGBA{0x2a, 0x6f, 0xdb, 0xff}
    if b.Hover {
        bg = color.RGBA{0x4a, 0x8f, 0xfb, 0xff}
    }
    vector.DrawFilledRect(screen, float32(b.Rect.Min.X), float32(b.Rect.Min.Y),
        float32(b.Rect.Dx()), float32(b.Rect.Dy()), bg, false)
    vector.StrokeRect(screen, float32(b.Rect.Min.X), float32(b.Rect.Min.Y),
        float32(b.Rect.Dx()), float32(b.Rect.Dy()), 1, color.White, false)

    op := &text.DrawOptions{}
    op.GeoM.Translate(float64(b.Rect.Min.X)+16, float64(b.Rect.Min.Y)+12)
    op.ColorScale.ScaleWithColor(color.White)
    text.Draw(screen, b.Label, face, op)
}
```

- Track pressed and released separately; a click is press+release inside.
- Hover is recomputed every tick, not stored from events.
- Draw and hit test share `b.Rect`; do not compute a second rectangle in `Draw`.

### 3. TrueType text with text/v2

```go
import "github.com/hajimehoshi/ebiten/v2/text/v2"

var face text.Face

func loadFont(path string) error {
    f, err := os.Open(path)
    if err != nil { return err }
    defer f.Close()
    src, err := text.NewGoTextFaceSource(f)
    if err != nil { return err }
    face = &text.GoTextFace{Source: src, Size: 24}
    return nil
}

func drawCentered(screen *ebiten.Image, s string, cx, cy float64) {
    w, h := text.Measure(s, face, 0)
    op := &text.DrawOptions{}
    op.GeoM.Translate(cx-w/2, cy-h/2)
    text.Draw(screen, s, face, op)
}
```

- `text/v2` is the current package; the old `text.Draw` with `font.Face` is deprecated.
- Load fonts and locales before the loop; `text.NewGoTextFaceSource` parses once.
- `text.Measure` accounts for line spacing; use it to size panels to content.
- Set `op.LineSpacing` for multi-line text; `op.PrimaryAlign`/`SecondaryAlign` are available for
  block alignment.
- Load a font with the glyphs you need (CJK, Arabic); the default Go font lacks many scripts.

### 4. Draw order and HUD

```go
func (g *Game) Draw(screen *ebiten.Image) {
    g.drawWorld(screen)
    g.drawHUD(screen)        // after the world
    if g.paused {
        g.drawPauseMenu(screen)
    }
}
```

- Draw order is the z-order; there is no depth buffer for UI.
- HUD text at small logical sizes can be unreadable when the window is scaled; either use a
  separate UI scale or draw HUD in a larger logical space.
- Use `ebiten.DrawImageOptions` with `GeoM.Scale` for pre-rendered panels/icons.
- Cache static UI (panels, icons) into an `ebiten.Image` and redraw only on change if profiling
  shows vector cost.

### 5. Modal blocking

```go
func (g *Game) drawPauseMenu(screen *ebiten.Image) {
    sw, sh := screen.Bounds().Dx(), screen.Bounds().Dy()
    vector.DrawFilledRect(screen, 0, 0, float32(sw), float32(sh),
        color.RGBA{0, 0, 0, 0xa0}, false)
    // ... buttons
}

func (g *Game) Update() error {
    if g.paused {
        g.updatePauseMenu()   // and return before gameplay input
        return nil
    }
    g.updateGameplay()
    return nil
}
```

With immediate mode, "blocking" means not running gameplay input updates while a modal is open,
plus drawing a scrim. Do not rely on the scrim's pixels.

### 6. Keyboard and gamepad focus

```go
if inpututil.IsKeyJustPressed(ebiten.KeyArrowDown) {
    g.focus = (g.focus + 1) % len(g.buttons)
}
if inpututil.IsKeyJustPressed(ebiten.KeyEnter) {
    g.activate(g.focus)
}
```

- Keep a focus index; draw a visible focus ring on the focused button.
- Support arrows/WASD, Enter/Space, Escape; map gamepad d-pad/face buttons to the same actions.
- Pointer hover can move focus, but do not let hover steal focus from keyboard.

## Pitfalls

- **Clicks miss buttons at scaled windows** → hit testing uses window pixels while drawing uses
  logical units. Use `CursorPositionF` and logical rects.
- **Click fires twice** → using `IsMouseButtonPressed` (held) instead of
  `IsMouseButtonJustPressed` (edge).
- **Button stays pressed** → no release handling or no cancel when the pointer leaves.
- **Blurry text** → scaling a small text image, or drawing text at fractional sizes. Draw at the
  logical size and let the final scale be integer where possible.
- **UI breaks on resize** → layout computed from window size instead of `Layout`'s logical size.
- **Clicks go through a modal** → gameplay input still runs under the pause screen.
- **Menu unusable without a mouse** → no focus navigation.
- **Font missing glyphs** → default font lacks the language; load a covering TTF.
- **Per-frame vector cost** → hundreds of `vector` calls each tick; cache static panels.
- **HUD ignores safe areas** → HUD under notches/TV overscan; inset by a margin.

## References

- Read `references/layout-input-and-text.md` for the API table, immediate-mode hit testing,
  text/v2 measurement, scaling modes, focus rules and a UI test checklist.

## Related skills

- `ebitengine-core` — the game loop, images and input this UI builds on.
- `ebitengine-audio` — UI sounds and volume.
- `game-ui-ux` — hierarchy, feedback and readability.
- `accessibility` — contrast, scaling and remapping.
- `pixijs-ui` — the same immediate-vs-retained trade-off in a web engine.
