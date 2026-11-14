---
name: ui-architecture
description: >
  Architect runtime UI: screen stack and routing, data binding, list virtualization, theming
  tokens, focus/navigation, localization expansion and UI performance. Engine bindings for Unity
  UI Toolkit, Godot Control, Unreal UMG and web. Use for menus/HUD that grow into spaghetti.
---

# UI architecture

`game-ui-ux` decides what the interface looks like; this skill decides how it is wired. A screen
stack, one-way data flow and virtualized lists keep UI maintainable past the first ten screens.
It is **compositional**: pair with `game-ui-ux`, `localization` and `accessibility`.

## When to use

- Use when adding menus/screens, a settings system, inventory lists, or UI that updates every
  frame.
- Use when UI state desyncs from gameplay, or opening a menu tanks FPS.

**When *not* to use:** layout, spacing, contrast and visual hierarchy → `game-ui-ux`; input
rebinding → `input-systems`; HUD art → `create-game-assets`.

## Principles

1. **One source of truth** — UI reads game state; it does not own it.
2. **One-way data flow** — state → view; user events → commands → state.
3. **Screens are a stack** — push/pop with explicit focus and pause rules.
4. **Bind, don't poll** — subscribe to changes; avoid per-frame `SetText`.
5. **Virtualize long lists** — create only visible rows.
6. **Theme by tokens** — colors/spacing/type in one place, not per widget.

## Screen stack

```text
push(screen):  pause gameplay? blur focus? hide HUD?
pop():         restore previous, restore focus, resume if stack empty
replace():     for main-menu transitions
modal:         blocks input below, traps focus
```

- Exactly one screen has focus; the stack decides.
- Back/Esc pops; never leave a dead-end screen.
- Pause is derived from the stack (`count > 0`), not toggled ad hoc.
- Restore the previously focused control when returning.

## Data binding

```text
model.health changed -> view.set("health", value)
button.clicked       -> command("buy", item_id)
```

- Subscribe on show, unsubscribe on hide (avoid leaks and double handlers).
- Coalesce updates: mark dirty, refresh once per frame at most.
- Format in the view (`"HP 80/100"`), not in the model.
- Use stable ids for list rows so recycling does not mix data.

## Engine bindings

### Unity UI Toolkit

```csharp
var root = uiDocument.rootVisualElement;
var list = root.Q<ListView>("inventory");
list.itemsSource = items;
list.makeItem = () => new Label();
list.bindItem = (el, i) => ((Label)el).text = items[i].DisplayName;
list.fixedItemHeight = 32;
root.Q<Button>("close").clicked += Close;
```

- `UIDocument` + `PanelSettings`; UXML for structure, USS for theme.
- `ListView` virtualizes and recycles rows — supply `makeItem`/`bindItem`.
- Use `dataSource`/`dataSourcePath` for bindings in newer Unity versions; verify against your
  Unity version.
- `rootVisualElement.Q<T>(name)` for lookup; cache references, do not query per frame.

### Godot Control

```gdscript
@onready var list: ItemList = %InventoryList

func _ready() -> void:
    Inventory.changed.connect(_refresh)

func _refresh() -> void:
    list.clear()
    for item in Inventory.items:
        list.add_item(item.display_name)
```

- `Control` anchors/containers handle layout; `%UniqueName` avoids deep paths.
- Signals for updates; `queue_redraw()` only for custom `_draw`.
- `focus_mode` + `grab_focus()` for controller navigation.

### Unreal UMG

- `UUserWidget` + `WidgetBlueprint`; expose events/properties to Blueprint.
- `ListView` for virtualized entries; `CommonUI` for input routing and activatable widgets.
- Bind with property bindings sparingly (they poll); prefer event-driven updates.

### Web (DOM/canvas)

- DOM UI for menus, canvas for HUD; do not rebuild the DOM per frame.
- Use a small store + subscribers; template rows and recycle for lists.
- CSS variables as theme tokens.

## Theming

```text
tokens: color.bg, color.text, color.accent, space.sm/md/lg, type.title/body
```

- One token file per platform; widgets reference tokens, never raw hex.
- Support high-contrast and colorblind palettes by swapping tokens.
- Font fallback per locale; test the longest translated string.

## Performance

- Hide inactive screens (`display: none` / `visible = false`), do not just move offscreen.
- Avoid layout rebuilds: batch text updates, avoid changing hierarchy per frame.
- Virtualize lists over ~30 rows; pool rows.
- Profile UI separately; text layout is often the cost.
- Cap HUD updates (health bar at 10–20 Hz is enough).

## Pitfalls

- **UI owns game state** → desync on save/load. Keep state in gameplay, UI as view.
- **Polling every frame** → CPU cost and missed changes. Event-driven binding.
- **Handler leaks** → subscribe on enable, never unsubscribe. Pair with hide/destroy.
- **List recycling bug** → stale closures/indices in `bindItem`; bind fresh data per row.
- **Focus lost after pop** → no focus restoration; controller users get stuck.
- **Pause toggled per menu** → double-pause/resume bugs. Derive from stack.
- **Hard-coded strings** → no localization; use keys and placeholders.
- **Theme sprawl** → per-widget colors drift; use tokens.
- **Rebuilding lists** → clear/add every update; diff or bind instead.

## Composition

- **Visual design:** `game-ui-ux` for layout, hierarchy, contrast.
- **Localization:** `localization` for expansion, RTL, font coverage.
- **Accessibility:** `accessibility` for focus, remapping, captions.
- **Input:** `input-systems` for navigation and glyphs.
- **Engine UI:** `unity-ui`, `unreal-ui`, `godot-ui-control`, `defold-ui`, `ebitengine-ui`.

## References

- Read `references/screen-stack-binding-and-lists.md` for stack pseudocode, binding patterns,
  list virtualization and a UI test checklist.
