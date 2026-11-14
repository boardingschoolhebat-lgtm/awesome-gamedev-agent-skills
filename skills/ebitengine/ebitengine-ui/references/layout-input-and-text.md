# Layout, input and text (Ebitengine v2.10.5)

Depth for `ebitengine-ui`: logical coordinates, immediate-mode input, text/v2 measurement and the
scaling rules that keep UI aligned.

## API used by the skill

| API | Package | Notes |
|-----|---------|-------|
| `Game.Layout(outsideW, outsideH) (screenW, screenH)` | `ebiten` | Logical screen size; rendering scales to the window. |
| `ebiten.SetWindowSize(w, h)` | `ebiten` | Initial window size in device-independent pixels. |
| `ebiten.SetWindowResizingMode(mode)` | `ebiten` | `WindowResizingModeEnabled` for resizable windows. |
| `ebiten.CursorPositionF()` | `ebiten` | Logical cursor position (v2.10+). |
| `inpututil.IsMouseButtonJustPressed(btn)` | `inpututil` | Edge-triggered; call in `Update`. |
| `inpututil.IsKeyJustPressed(key)` | `inpututil` | Edge-triggered. |
| `inpututil.AppendJustPressedTouchIDs(dst)` | `inpututil` | Touch press IDs. |
| `ebiten.TouchPosition(id)` | `ebiten` | Touch position. |
| `vector.DrawFilledRect(dst, x, y, w, h, clr, antialias)` | `vector` | Panel/button fills. |
| `vector.StrokeRect(dst, x, y, w, h, strokeWidth, clr, antialias)` | `vector` | Outlines, focus rings. |
| `text.Draw(dst, s, face, op)` | `text/v2` | Draws text with layout options. |
| `text.Measure(s, face, lineSpacing)` | `text/v2` | Width/height for layout. |
| `text.NewGoTextFaceSource(r)` | `text/v2` | Parse a TTF/OTF once. |
| `text.GoTextFace{Source, Size}` | `text/v2` | Face at a logical size. |

## Logical vs window coordinates

- `Layout` returns the logical size; `Draw` receives an image of that size.
- The window may be larger/smaller; Ebitengine scales the final image.
- All UI geometry should be in logical units: rects, font sizes, margins.
- `CursorPositionF` returns logical units; `CursorPosition` returns integer logical units.
- On a window scale of 2, a 12 px logical font is 24 physical pixels — still crisp because the
  screen image is scaled by the GPU, not resampled from an intermediate.
- If you need pixel-perfect UI, choose a logical size that divides common window sizes and use
  integer scaling, accepting letterboxing.

## Immediate-mode input

```go
pressed := inpututil.IsMouseButtonJustPressed(ebiten.MouseButtonLeft)
released := inpututil.IsMouseButtonJustReleased(ebiten.MouseButtonLeft)
```

- `IsMouseButtonPressed` is "held"; it repeats every tick.
- A click is `pressed` on the button, then `released` while still inside.
- Store `Down` on the button struct to survive pointer movement.
- Touch: `AppendJustPressedTouchIDs` for presses, `ebiten.TouchPosition(id)` for positions; treat
  the first touch as the pointer.
- Gamepad: `inpututil.IsStandardGamepadButtonJustPressed` for menus; support
  `ebiten.StandardGamepadButtonFrontBottom` as confirm.

## Text/v2

```go
op := &text.DrawOptions{}
op.GeoM.Translate(x, y)
op.LineSpacing = size * 1.4
op.ColorScale.ScaleWithColor(color.White)
op.PrimaryAlign = text.AlignCenter       // horizontal alignment of the block
text.Draw(screen, "Line one\nLine two", face, op)
```

- `text.Measure` returns the block size; call it after loading the face.
- Multi-line text splits on `\n`; `LineSpacing` in pixels (not a multiplier).
- Font size is in logical pixels; keep it ≥ 12–14 for readability at 1× scale.
- `text.NewGoTextFaceSource` reads the whole font; load once at startup.
- Fallback faces: `text.GoTextFace` has a `Source` per script; compose faces for mixed scripts or
  use a font with wide coverage.
- `ebitenutil.DebugPrint` is for debugging only — no styling, fixed font.

## Scaling modes

| Mode | Behavior |
|------|----------|
| Fixed logical size | UI layout is stable; window scaling may letterbox or stretch. |
| Layout returns outside size | UI fills the window; layout must be resolution-independent. |
| Layout returns scaled size | Compromise: clamp scale to integer steps to keep text crisp. |

For resolution-independent UI:

```go
func (g *Game) Layout(outsideW, outsideH int) (int, int) {
    scale := math.Min(float64(outsideW)/640, float64(outsideH)/360)
    if scale < 1 { scale = 1 }
    return int(640 * scale), int(360 * scale)
}
```

## Focus rules

- One focus index; Tab/arrow moves it; Enter/Space activates.
- Focus ring: 2 px stroke or a contrasting fill, visible on every state.
- Hover sets a highlight but does not change focus unless the player clicks.
- Escape closes the topmost modal and restores the previous focus.
- Disabled items are skipped by focus and drawn dimmed.

## UI test checklist

1. Window resized from tiny to fullscreen: layout stays inside bounds, no clipped buttons.
2. Scaled windows (1×, 1.5×, 2×): clicks land on buttons, text readable.
3. Mouse, touch and gamepad each can operate the menu end to end.
4. Press, drag off, release: no accidental activation.
5. Pause modal blocks gameplay input; closing restores it.
6. Long/localized strings fit or wrap; no overlap (`localization`).
7. Focus ring visible; Tab order matches visual order.
8. Font covers every shipped language.
9. Static panels cached if profiling shows vector cost.
10. HUD respects a safe-area margin.
