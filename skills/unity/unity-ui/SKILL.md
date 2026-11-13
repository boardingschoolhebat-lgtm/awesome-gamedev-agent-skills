---
name: unity-ui
description: >
  Build runtime UI in Unity 6.3: uGUI canvases with CanvasScaler and RectTransform anchoring,
  layout groups, TextMeshPro, buttons and EventSystem input modules, safe-area handling, plus UI
  Toolkit screens with UIDocument, UXML and USS. Use when a Unity project needs a HUD, menu,
  inventory, settings screen, or UI that scales across resolutions. Targets Unity 6.3 LTS
  (6000.3).
---

# Unity UI

Pick one UI system per screen, build it on a correctly scaled canvas or panel, and drive it
through cached references instead of per-frame searches. Targets **Unity 6.3 LTS (6000.3)**.

## When to use

- Use when adding a HUD, menu, pause screen, inventory, settings page or damage numbers.
- Use when UI is blurry, misaligned at other resolutions, unclickable, or rebuilding layout every
  frame.

**When *not* to use:** UI *design* (hierarchy, feedback, accessibility) → `game-ui-ux`; input
actions and rebinding → `unity-input-system`; world-space health bars attached to 3D objects still
use this skill plus `camera-systems`.

## Choose the system first

| | uGUI (Canvas) | UI Toolkit |
|-|---------------|------------|
| Best for | HUDs, world-space UI, prefab-driven screens, existing projects | runtime panels, lists, settings, editor-like layouts |
| Styling | components + prefabs | USS stylesheets and classes |
| Layout | `RectTransform` + layout groups | flexbox-like Yoga layout |
| World space | yes | runtime panels are screen-space |
| Input | `EventSystem` + input module | panel event system; verify gamepad navigation for your version |

Do not mix the two for one screen. Both can coexist in a project; keep their input handling
separate.

## Core workflow (uGUI)

1. **Canvas and scaler.** `Screen Space - Overlay` for most HUDs, `Screen Space - Camera` or
   `World Space` when it must sit in the world. Set `CanvasScaler` to `Scale With Screen Size`,
   reference resolution `1920×1080`, and `Match` around `0.5` (0 for width-led, 1 for height-led
   layouts).
2. **One EventSystem.** The scene needs exactly one `EventSystem`; with the Input System package
   use `InputSystemUIInputModule`, with the legacy input manager `StandaloneInputModule`. Two
   event systems make buttons fire twice or not at all.
3. **Anchor, do not position by hand.** Set `anchorMin`/`anchorMax` for stretch or corner
   anchoring, then `pivot` and `anchoredPosition`/`sizeDelta`. A HUD written against one aspect
   ratio breaks on the next device otherwise.
4. **Let layout groups size things.** `HorizontalLayoutGroup`/`VerticalLayoutGroup` +
   `ContentSizeFitter` + `LayoutElement` replace manual pixel math; avoid changing layout
   properties every frame.
5. **Use TextMeshPro.** `TMPro.TextMeshProUGUI`, with a font asset that includes the glyphs the
   game needs; `text` assignment allocates, so cache strings where it matters.
6. **Wire events once.** `button.onClick.AddListener(HandleClick)` in `OnEnable` or `Awake`, and
   `RemoveListener` in `OnDisable`/`OnDestroy`; a listener added on every enable stacks calls.
7. **Update through references.** Cache `Image`, `TMP_Text` and `Button` fields with
   `[SerializeField]`; never call `GetComponent`/`Find` in `Update`.
8. **Handle the safe area.** Apply `Screen.safeArea` to a full-screen `RectTransform` so notches
   do not cover the HUD.

## Patterns

### 1. A screen-space HUD canvas

```csharp
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public sealed class Hud : MonoBehaviour
{
    [SerializeField] private Image healthFill;          // Image Type = Filled
    [SerializeField] private TMP_Text healthLabel;
    [SerializeField] private Button pauseButton;

    private void Awake()
    {
        // Wire once; RemoveListener in OnDestroy keeps the object clean.
        pauseButton.onClick.AddListener(OnPauseClicked);
    }

    private void OnDestroy() => pauseButton.onClick.RemoveListener(OnPauseClicked);

    public void SetHealth(float current, float max)
    {
        var ratio = max <= 0f ? 0f : Mathf.Clamp01(current / max);
        healthFill.fillAmount = ratio;                  // no layout rebuild
        healthLabel.SetText("{0:0}/{1:0}", current, max);
    }

    private void OnPauseClicked() => GameFlow.TogglePause();
}
```

`Image.fillAmount` only works with `Image.Type = Filled`; a sliced or simple image ignores it.
`TMP_Text.SetText` with a format avoids the intermediate `string` allocation of
`$"{current}/{max}"`.

### 2. Anchoring and scaling

```csharp
// Stretch a panel to its parent with a margin.
var rect = panel.rectTransform;
rect.anchorMin = Vector2.zero;
rect.anchorMax = Vector2.one;
rect.pivot = new Vector2(0.5f, 0.5f);
rect.offsetMin = new Vector2(24f, 24f);     // left, bottom
rect.offsetMax = new Vector2(-24f, -24f);   // right, top (negative)
```

- `offsetMin`/`offsetMax` are the insets from the anchors; with a full stretch they behave like
  margins.
- For a corner element, set both anchors to the same corner, the pivot to that corner, and use
  `anchoredPosition`.
- Put fixed-size elements inside layout groups and give them a `LayoutElement` with
  `preferredWidth`/`preferredHeight` instead of editing `sizeDelta` at runtime.

### 3. Safe area

```csharp
using UnityEngine;

[RequireComponent(typeof(RectTransform))]
public sealed class SafeAreaFitter : MonoBehaviour
{
    private RectTransform _rect;
    private Rect _lastSafeArea;
    private Vector2Int _lastScreen;

    private void Awake() => _rect = GetComponent<RectTransform>();

    private void Update()
    {
        if (Screen.safeArea == _lastSafeArea && Screen.width == _lastScreen.x &&
            Screen.height == _lastScreen.y)
        {
            return;
        }
        Apply();
    }

    private void Apply()
    {
        _lastSafeArea = Screen.safeArea;
        _lastScreen = new Vector2Int(Screen.width, Screen.height);

        var min = _lastSafeArea.position;
        var max = _lastSafeArea.position + _lastSafeArea.size;
        min.x /= Screen.width;
        min.y /= Screen.height;
        max.x /= Screen.width;
        max.y /= Screen.height;

        _rect.anchorMin = min;
        _rect.anchorMax = max;
        _rect.offsetMin = _rect.offsetMax = Vector2.zero;
    }
}
```

`Screen.safeArea` is in pixels with the origin at the bottom-left; divide by the current screen
size before using it as anchors. The width/height check re-applies after a rotation or a window
resize.

### 4. A menu built in UI Toolkit

```csharp
using UnityEngine;
using UnityEngine.UIElements;

[RequireComponent(typeof(UIDocument))]
public sealed class MainMenu : MonoBehaviour
{
    private Button _play;

    private void OnEnable()
    {
        var root = GetComponent<UIDocument>().rootVisualElement;
        _play = root.Q<Button>("play-button");       // name set in UXML or via USS selector
        _play.clicked += OnPlay;
        root.Q<Button>("quit-button").clicked += OnQuit;
    }

    private void OnDisable()
    {
        if (_play != null) _play.clicked -= OnPlay;  // symmetric unsubscribe
    }

    private void OnPlay() => SceneLoader.LoadFirstLevel();
    private void OnQuit() => Application.Quit();
}
```

- `rootVisualElement` is available after the `UIDocument` enables; query in `OnEnable`, not
  `Awake`.
- Give elements names in UXML (`<ui:Button name="play-button" text="Play" />`) and style them with
  USS classes, not inline styles.
- Use `root.Q<VisualElement>("...")` for containers, `ListView` for inventories, and
  `AddToClassList`/`RemoveFromClassList` for state instead of setting colors in C#.
- Subscribe and unsubscribe in matching enable/disable callbacks; UI Toolkit events hold
  references to the delegate target.

### 5. Splitting canvases for performance

```text
Canvas (Screen Space - Overlay, CanvasScaler)
├── StaticCanvas        -- background, labels that never change
└── DynamicCanvas       -- health bars, timers, damage numbers
```

A change to any element on a canvas rebuilds that canvas's batch. Keep frequently updated
elements on their own canvas, and turn off `Raycast Target` on decorative graphics so they do not
participate in hit testing.

## Pitfalls

- **UI is tiny or huge at another resolution** → `CanvasScaler` left on `Constant Pixel Size`.
  Use `Scale With Screen Size` with a reference resolution and a deliberate match value.
- **Buttons do nothing** → no `EventSystem`, the wrong input module for the project's input
  handler, or a full-screen transparent graphic with `Raycast Target` covering them. Check the
  EventSystem and the hierarchy order.
- **Buttons fire twice** → two EventSystems, or a listener added in `Update`/`OnEnable` without
  removal. Add once, remove symmetrically.
- **HUD drifts off-screen on a phone** → anchors set by hand for one aspect ratio. Anchor to the
  target corner/edge and apply `Screen.safeArea`.
- **Layout rebuild spikes** → changing `sizeDelta`, text or layout properties every frame. Update
  only on change, and split canvases.
- **Text is missing glyphs** → the TMP font asset does not include the characters; regenerate the
  atlas or add a fallback font.
- **World-space UI is behind geometry or tiny** → set the canvas `worldCamera`, scale the canvas
  for the world units, and check the `EventCamera` used for clicks.
- **`GetComponent` in `Update`** → cache references in `Awake`; `Find` and `GetComponent` are
  scene searches.
- **UI Toolkit queries return null** → the element name is missing in UXML, or the query runs
  before `OnEnable`. Also check the `PanelSettings` asset is assigned on the `UIDocument`.
- **Runtime UI Toolkit ignores clicks** → check the panel's sorting order and whether a uGUI
  `GraphicRaycaster` overlay is intercepting; both systems can receive pointer input, so keep
  interactive regions apart.

## References

- Read `references/ugui-and-ui-toolkit.md` for the uGUI component table, anchoring rules, layout
  and canvas-splitting guidance, UI Toolkit structure and a resolution test matrix.

## Related skills

- `game-ui-ux` — hierarchy, feedback, readability and accessibility.
- `unity-input-system` — actions, devices and UI input modules.
- `unity-3d-essentials` — cameras and world-space placement for diegetic UI.
- `godot-ui-control` / `unreal-ui` / `defold-ui` — the same concerns in other engines.
