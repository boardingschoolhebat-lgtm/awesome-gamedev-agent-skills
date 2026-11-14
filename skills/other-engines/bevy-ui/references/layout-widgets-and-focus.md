# Layout, widgets and focus (Bevy 0.20)

Depth for `bevy-ui`: the component model, 0.20 widget flow, flexbox recipes, focus/tab navigation
and test checks.

## Component model

| Component | Purpose |
|-----------|---------|
| `Node` | Layout box: size, flex, padding, margin, position. |
| `BackgroundColor` | Solid fill. |
| `BorderColor` | Border color (`all(...)` helper). |
| `BorderRadius` | Rounded corners (`all(px(8))`, `MAX` for pills). |
| `Text` | Text content (0.20 newtype: `Text::new("...")`). |
| `TextFont` | Font handle and `font_size`. |
| `TextColor` | Glyph color. |
| `TextLayout` | Alignment/wrapping (`TextLayout::justify(Justify::Center)`). |
| `Button` | Headless widget marker (`bevy::ui_widgets`). |
| `Hovered` / `Pressed` | Widget state components, updated by picking. |
| `Interaction` | Classic hover/press enum for manual styling. |
| `TabIndex` / `TabGroup` | Keyboard focus order and groups. |
| `AccessibilityNode` | Screen-reader label/role. |
| `ZIndex` | Global UI draw order. |
| `UiScale` | Global UI scaling resource. |

## Widget flow (0.20)

```text
spawn Button + Hovered + Node + children
        │
pointer/keyboard input (picking + focus)
        │
Pressed/Hovered state updated
        │
Activate event on completed click
        │
observe(|_activate: On<Activate>| { ... })
```

- `Button` from `bevy::ui_widgets` is behavior-only; you supply visuals.
- `observe` attaches the handler to that entity, so no global system is needed.
- `DefaultPlugins` includes the widget and input-focus plugins.
- Classic `Interaction` still works for customs; filter `Changed<Interaction>`.

## Flexbox recipes

### Full-screen centered panel

```rust
Node {
    width: percent(100),
    height: percent(100),
    align_items: AlignItems::Center,
    justify_content: JustifyContent::Center,
    ..default()
}
```

### Vertical menu with spacing

```rust
Node {
    flex_direction: FlexDirection::Column,
    row_gap: px(12),
    padding: UiRect::all(px(24)),
    ..default()
}
```

### HUD corners

```rust
Node {
    position_type: PositionType::Absolute,
    top: px(16),
    left: px(16),
    ..default()
}
```

### Responsive two-column layout

```rust
Node {
    width: percent(100),
    display: Display::Flex,
    flex_direction: FlexDirection::Row,
    column_gap: px(16),
    ..default()
}
```

Percent sizes depend on a sized parent; root nodes should be `percent(100)` or sized from
`UiScale`.

## Sizing units

- `px(12.0)` — logical pixels.
- `percent(50.0)` — percent of parent.
- `Val::Auto` — content/flex-driven.
- `em(2.0)` — relative to the current font size (`EmSize`).
- `rem(1.5)` — relative to the global `RemSize`.

## Focus and accessibility

```rust
use bevy::input_focus::tab_navigation::{TabGroup, TabIndex};

commands.spawn((TabGroup::new(0), children![
    (Button, TabIndex(0), /* visuals */),
    (Button, TabIndex(1), /* visuals */),
]));
```

- `TabIndex` orders focus within a `TabGroup`; `TabGroup::modal()` traps focus in a dialog.
- Enter/Space activate the focused widget and emit `Activate`.
- Add `AccessibilityNode` with a label for icon-only buttons.
- Draw a visible focus ring; the headless widget has no styling.

## State and cleanup

- Tag UI roots (`#[derive(Component)] struct MenuRoot;`) and despawn on state exit.
- Use `OnExit(GameState::Paused)` to run cleanup.
- `commands.entity(e).despawn()` removes descendants.
- For persistent HUD, toggle `Display::None` instead of despawning.

## Text

- `Text::new("Score: 10")` + `TextFont { font_size: 24.0, ..default() }`.
- Load a font with `asset_server.load("fonts/FiraSans-Bold.ttf")`; the default font has limited
  glyph coverage.
- `TextLayout` controls alignment/wrapping; text wraps at the node's width.
- Update text by writing `**text = format!("Score: {score}")` (deref the newtype).
- Localized strings can be 30–40 % longer (`localization`); leave room or wrap.

## Test checklist

1. UI appears at 1280×720 and 1920×1080 without clipping.
2. Buttons respond to mouse and touch; hover/press visuals match state.
3. Clicking outside a modal does not trigger gameplay.
4. Keyboard: Tab moves focus, Enter/Space activates, focus ring visible.
5. Menus despawn on state exit; reopening does not duplicate.
6. Text updates without re-spawning the label.
7. Long/localized strings fit or wrap.
8. Contrast and touch-target size pass (`accessibility`).
9. No per-frame UI restyle without `Changed<Interaction>`.
10. A dedicated UI camera keeps HUD above the world.
