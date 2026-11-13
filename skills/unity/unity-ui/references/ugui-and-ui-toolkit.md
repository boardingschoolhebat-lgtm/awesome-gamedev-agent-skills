# uGUI and UI Toolkit reference (Unity 6.3)

Depth for `unity-ui`: the components that matter, the anchoring rules, performance boundaries and
the resolution matrix to test.

## uGUI components

| Component | Job | Notes |
|-----------|-----|-------|
| `Canvas` | render mode and sorting | `Screen Space - Overlay` ignores cameras; `Screen Space - Camera` needs a `worldCamera`. |
| `CanvasScaler` | resolution adaptation | `Scale With Screen Size`, reference resolution, `matchWidthOrHeight`. |
| `GraphicRaycaster` | pointer hit testing | Required for clicks; one per interactive canvas. |
| `EventSystem` | input dispatch | Exactly one; module must match the project's input backend. |
| `RectTransform` | layout | anchors, pivot, `anchoredPosition`, `sizeDelta`, `offsetMin/Max`. |
| `Image` | sprite/color/fill | `fillAmount` needs `Type = Filled`. |
| `RawImage` | texture without sprite import | useful for render textures. |
| `TextMeshProUGUI` | text | font asset, `SetText`, rich text, auto-size. |
| `Button` | click | `onClick` event; `interactable` for enable/disable. |
| `Slider`, `Toggle`, `Dropdown` | settings | each has an event; wire once and unsubscribe. |
| `LayoutGroup` | arrange children | `Horizontal`, `Vertical`, `Grid`; costs rebuilds. |
| `ContentSizeFitter` | size to content | combine with layout groups, not both on a child. |
| `LayoutElement` | preferred/min size | keeps layout groups from fighting. |
| `Mask` / `RectMask2D` | clipping | `RectMask2D` is cheaper for rectangular clipping. |
| `CanvasGroup` | group alpha/raycast | fade and block interaction without touching children. |

## Scaling rules

| Layout | Reference resolution | Match |
|--------|----------------------|-------|
| Landscape mobile/desktop | 1920×1080 | 0.5 (or 0 for width-led) |
| Portrait mobile | 1080×1920 | 0.5 (or 1 for height-led) |
| Fixed-aspect desktop | native | `Constant Pixel Size` with a manual scale is acceptable |

`matchWidthOrHeight` interpolates between width-based and height-based scaling; pick one axis when
the layout must preserve a fixed dimension (for example a portrait list that must always show N
rows).

## Anchoring cheat sheet

```text
Full-screen:  anchorMin (0,0), anchorMax (1,1), offsets = margins
Top-left:     anchorMin/Max (0,1), pivot (0,1), anchoredPosition = (-x, -y)
Top-right:    anchorMin/Max (1,1), pivot (1,1), anchoredPosition = (-x, -y)
Bottom-center anchorMin/Max (0.5,0), pivot (0.5,0), anchoredPosition = (0, y)
Stretch horizontally: anchorMin (0,y), anchorMax (1,y), sizeDelta.y fixed
```

- `sizeDelta` means "size relative to the anchors": with a full stretch it is the *extra* size
  beyond the parent, not the absolute size.
- Set the pivot before positioning; `anchoredPosition` is measured from the pivot.
- For a health bar that scales with a parent, set the fill image to `Type = Filled`,
  `fillMethod = Horizontal`, and animate `fillAmount` rather than the rect.

## Canvas performance

- Every UI change marks the canvas dirty; a canvas rebuild re-batches all its elements. Split
  static and dynamic elements into separate canvases.
- Disable `Raycast Target` on text and decorative images that do not need clicks.
- Prefer `CanvasGroup.alpha` for fading a whole panel over per-element alpha.
- Avoid enabling/disabling many objects per frame; toggle a `CanvasGroup` or a single root.
- Layout groups rebuild on child changes; do not animate child sizes inside a layout group.
- Text updates allocate; cache formatted strings when a value changes every frame.

## UI Toolkit structure

```text
Assets/UI/
├── MainMenu.uxml        -- hierarchy (VisualElement, Button, Label, ListView)
├── MainMenu.uss         -- styles and classes
└── MainMenuPanel.asset  -- PanelSettings (scale mode, theme, sorting order)
```

- `UIDocument` references a `VisualTreeAsset` (UXML) and a `PanelSettings`.
- `rootVisualElement.Q<Button>("play-button")` finds by name; `.Q<VisualElement>(className:
  "card")` finds by USS class.
- USS supports `.class`, `#name`, descendant selectors and transitions; prefer classes over
  inline `style.*` assignments.
- `ListView` virtualizes long lists (inventory, leaderboard) — bind `itemsSource` and
  `makeItem`/`bindItem`.
- Panel scale mode (`Constant Pixel Size`, `Scale With Screen Size`) lives on `PanelSettings`;
  match it to the uGUI scaler when both exist.
- Runtime input: the panel dispatches pointer events itself. Check the panel's input handling and
  your input module for gamepad/keyboard focus in the Unity version you target, rather than
  assuming uGUI's EventSystem covers both.

## Test matrix

| Check | How |
|-------|-----|
| Aspect ratios | 16:9, 19.5:9, 4:3, 21:9 in Game view; HUD stays anchored and readable |
| Resolutions | 1280×720, 1920×1080, 2560×1440; no blurry text or clipped panels |
| Safe area | Device Simulator with a notch; nothing interactive under it |
| Input | Mouse, touch, gamepad; focus visible and navigable |
| Pause | Menu opens, gameplay input blocked, time scale restored on close |
| Localization | Longest string fits; TMP fallback glyphs render |
| Performance | Profiler: no per-frame layout rebuild on the HUD canvas |
| Scene reload | Event listeners do not accumulate after loading the scene twice |
