---
name: bevy-ui
description: >
  Build UI in Bevy 0.20 with ECS entities: Node layout (flexbox), text and fonts, buttons via the
  ui_widgets Button/Hovered/Pressed/Activate path or Interaction queries, styling with
  BackgroundColor/BorderColor/BorderRadius, focus and tab navigation, menus and HUD, and
  resolution-independent sizing with px/percent/em/rem. Use when a Bevy game needs menus, HUD or
  clickable UI. Targets Bevy 0.20.
---

# Bevy UI

Bevy UI is ECS: every panel, label and button is an entity with `Node` (layout), style components
and children. Buttons are headless widgets that emit `Activate`, or entities you poll with
`Interaction`. Targets **Bevy 0.20**.

## When to use

- Use when a Bevy game needs a menu, HUD, pause screen, settings panel or clickable button.
- Use when UI text is missing, layout ignores sizes, or clicks do not reach buttons.

**When *not* to use:** ECS architecture and systems → `bevy-ecs`; UI/UX design → `game-ui-ux`;
persistence → `bevy-save`; 2D tile levels → `bevy-tilemap`.

## Core workflow

1. **Spawn a root** with `Node { width: percent(100), height: percent(100), ..default() }` and
   `children![...]` for the tree.
2. **Lay out with flexbox**: `display: Display::Flex`, `flex_direction`, `justify_content`,
   `align_items`, `row_gap`/`column_gap`, `padding`, `margin`.
3. **Size with `px()`/`percent()`** (0.20 helpers) or `Val::Px/Percent/Auto`; `em`/`rem` exist for
   text-relative sizing.
4. **Style** with `BackgroundColor`, `BorderColor`, `BorderRadius`, `TextColor`, `TextFont`.
5. **Buttons**: spawn `Button` + `Hovered` + `Node`, react to `Activate` with an observer, or use
   `Interaction` + `Changed<Interaction>` for the classic pattern.
6. **Mark roots** with a component so despawn is one query; UI otherwise leaks across state
   changes.
7. **Add focus/tab navigation** with `TabIndex`/`TabGroup` for keyboard and accessibility.

## Patterns

### 1. Root, panel and text

```rust
use bevy::prelude::*;

fn setup(mut commands: Commands) {
    commands.spawn((
        Node {
            width: percent(100),
            height: percent(100),
            align_items: AlignItems::Center,
            justify_content: JustifyContent::Center,
            ..default()
        },
        children![(
            Node {
                width: px(420),
                padding: UiRect::all(px(24)),
                flex_direction: FlexDirection::Column,
                row_gap: px(12),
                ..default()
            },
            BackgroundColor(Color::srgb(0.11, 0.15, 0.20)),
            BorderRadius::all(px(12)),
            children![
                (Text::new("Paused"), TextFont { font_size: 40.0, ..default() }),
                (Text::new("Resume"), TextFont { font_size: 24.0, ..default() }),
            ],
        )],
    ));
}
```

- `Node` is the layout component; without it an entity has no UI box.
- `children![...]` is the 0.20 spawn macro; `.with_children(|p| ...)` also works.
- `px()`/`percent()` are the 0.20 sizing helpers; `Val::Px(12.0)` is equivalent.
- A UI entity outside a `Node` tree is not laid out.

### 2. Buttons with the 0.20 widget set

```rust
use bevy::{
    picking::hover::Hovered,
    prelude::*,
    ui::Pressed,
    ui_widgets::{observe, Activate, Button},
};

fn spawn_button(mut commands: Commands, parent: Entity) {
    commands.spawn((
        Button,                       // headless widget: tracks press, emits Activate
        Hovered::default(),           // updated by the picking backend
        Node {
            width: px(240),
            height: px(56),
            justify_content: JustifyContent::Center,
            align_items: AlignItems::Center,
            ..default()
        },
        BackgroundColor(Color::srgb(0.16, 0.44, 0.86)),
        BorderRadius::all(px(10)),
        children![(Text::new("Resume"), TextFont { font_size: 22.0, ..default() })],
        observe(|_activate: On<Activate>| {
            info!("resume clicked");
        }),
    ));
}
```

- `Button` from `bevy::ui_widgets` is behavior-only: it handles pointer/keyboard input and fires
  `Activate` on a completed click.
- `Hovered`/`Pressed` are state components; read them in a system to restyle.
- `Activate` is observed on the button entity, so the handler lives with the widget.
- Add `TabIndex` and wrap in a `TabGroup` for keyboard focus (DefaultPlugins includes the input
  focus plugin).

### 3. Classic `Interaction` pattern

```rust
#[derive(Component)]
struct MenuButton;

fn button_colors(
    mut q: Query<
        (&Interaction, &mut BackgroundColor),
        (Changed<Interaction>, With<MenuButton>),
    >,
) {
    for (interaction, mut color) in &mut q {
        *color = match *interaction {
            Interaction::Pressed => Color::srgb(0.20, 0.70, 0.35).into(),
            Interaction::Hovered => Color::srgb(0.25, 0.55, 0.95).into(),
            Interaction::None => Color::srgb(0.16, 0.44, 0.86).into(),
        };
    }
}
```

- `Interaction` is updated by the picking backend for entities with `Button` (or `Node` +
  interaction components); filter `Changed<Interaction>` so styling runs only on transitions.
- Prefer the widget `Activate` path for new 0.20 code; `Interaction` remains useful for custom
  hover/press visuals.
- Do not put gameplay logic in the color system; emit an event/message instead.

### 4. Layout rules that matter

| Property | Effect |
|----------|--------|
| `display: Flex` | Default for `Node`; flexbox layout. |
| `flex_direction` | `Row`/`Column`. |
| `justify_content` | Main-axis distribution. |
| `align_items` | Cross-axis alignment. |
| `width`/`height` | `px`, `percent`, `auto`, `em`, `rem`. |
| `padding`/`margin` | `UiRect` per side. |
| `row_gap`/`column_gap` | Spacing between children. |
| `position_type: Absolute` | Overlay without affecting siblings. |
| `top/left/right/bottom` | Offsets for absolute nodes. |
| `overflow` | `visible`/`clip`/`hidden` for scrolling. |

- Percent sizes resolve against the parent; a root at `percent(100)` fills the window.
- Text wraps inside its node width; set `TextLayout` for alignment.
- Use `Display::None` to hide without despawning; `Visibility` also works but layout still runs.

### 5. Menus, state and cleanup

```rust
#[derive(Component)]
struct MenuRoot;

fn despawn_menu(mut commands: Commands, q: Query<Entity, With<MenuRoot>>) {
    for e in &q {
        commands.entity(e).despawn();   // 0.20 despawns descendants
    }
}

fn pause(
    keys: Res<ButtonInput<KeyCode>>,
    mut next: ResMut<NextState<GameState>>,
) {
    if keys.just_pressed(KeyCode::Escape) {
        next.set(GameState::Paused);
    }
}
```

- Tag UI roots and despawn on state exit (`OnExit`) so menus do not stack.
- `despawn()` removes the entity and its children in 0.20; no manual recursion.
- Toggle `Display::None` for HUD panels that should persist.

### 6. Resolution, scaling and accessibility

- Size with `percent` for full-screen containers and `px` for touch targets (≥ 44 px).
- `em`/`rem` let text scale with font size; use them for padding around text.
- Add `TabIndex`/`TabGroup` for keyboard navigation and `AccessibilityNode` labels for screen
  readers.
- Keep contrast ≥ 4.5:1 and pair color with icon/text (`accessibility`).
- Test at 1280×720, 1920×1080 and a narrow window; flexbox should reflow without code.

## Pitfalls

- **Nothing renders** → entity has no `Node`, or the UI camera is missing. UI needs a camera; in
  2D the default camera works.
- **Clicks do nothing** → no `Button`/`Interaction` (or picking backend), or another node covers
  the button. Check `ZIndex`/ordering and `PickingBehavior`.
- **Text invisible** → no `TextFont`/`TextColor`, or text entity outside a `Node` hierarchy.
- **Layout ignores width** → percentage without a sized parent, or `Val::Auto` on the axis.
- **UI leaks between states** → roots not despawned on exit.
- **Button handler runs every frame** → querying `Interaction` without `Changed<Interaction>`.
- **v0.18 tutorial code fails** → `Text` and font fields changed; 0.20 uses `Text::new`,
  `TextFont`, and the widget `Button`. Check the version before copying.
- **HUD behind the world** → UI renders in its own pass; a full-screen world sprite/camera order
  can still cover it. Use a dedicated UI camera if needed.
- **Tiny touch targets** → `px(24)` buttons. Use ≥ 44 px.
- **Despawn panic** → despawning children manually then the parent. Despawn only the root.

## References

- Read `references/layout-widgets-and-focus.md` for the 0.20 component table, widget vs
  `Interaction` flow, flexbox recipes, focus/tab setup and a UI test checklist.

## Related skills

- `bevy-ecs` — entities, components, systems and states this UI uses.
- `game-ui-ux` — hierarchy, feedback and readability.
- `accessibility` — contrast, focus, scaling and screen readers.
- `bevy-save` — persisting settings shown in menus.
- `godot-ui-control` / `unity-ui` — equivalent work in other engines.
