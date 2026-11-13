# UMG lifetimes, input and DPI (UE 5.8)

Depth for `unreal-ui`: the calls that create and destroy widgets, the input modes and focus rules,
and the settings that keep UI readable at every resolution.

## API used by the skill

| Item | Form | Notes |
|------|------|-------|
| `CreateWidget` | `CreateWidget<T>(UWorld* World, TSubclassOf<UUserWidget> Class)` | Also owner/player-controller overloads; returns null on bad class. |
| `AddToViewport` | `AddToViewport(int32 ZOrder)` | Higher z-order is on top; calling twice adds twice. |
| `AddToPlayerScreen` | `AddToPlayerScreen(int32 ZOrder)` | Split-screen local player viewport. |
| `RemoveFromParent` | `RemoveFromParent()` | Removes from viewport; the object can be re-added. |
| `NativeConstruct` / `NativeDestruct` | virtual overrides | Run on add/remove; re-run when re-added. |
| `BindWidget` | `UPROPERTY(meta = (BindWidget))` | Required widget must exist with the same name. |
| `BindWidgetOptional` | `UPROPERTY(meta = (BindWidgetOptional))` | Null allowed. |
| `UWidgetTree` | `UUserWidget::WidgetTree` | Runtime access to the widget hierarchy. |
| `SetInputMode` | `APlayerController::SetInputMode(const FInputModeDataBase&)` | Choose UI-only, game-and-UI, or game-only. |
| `TakeWidget` | `UUserWidget::TakeWidget()` | Slate widget for focus handling. |
| `SetPause` | `APlayerController::SetPause(bool)` | Pause is separate from input mode. |

## Widget lifetimes

```text
CreateWidget  -> object exists, not on screen
AddToViewport  -> NativeConstruct, visible
RemoveFromParent -> NativeDestruct, object still alive
re-add         -> NativeConstruct again
GC             -> only when no UPROPERTY/AddToRoot reference remains
```

Rules:

- Keep exactly one owning `UPROPERTY()` per widget instance on the controller/game mode/HUD actor.
- `NativeConstruct` may run more than once; bind delegates there and unbind in `NativeDestruct`.
- `NativeDestruct` does not destroy the object; null the pointer if the next open should recreate.
- Do not create a widget per event (each has a cost); create once, then show/hide.
- Widgets created with a null class return null; check before `AddToViewport` to avoid a crash.

## Input mode matrix

| Screen | Input mode | Cursor | Pause |
|--------|------------|--------|-------|
| HUD, informational | leave the current mode | no change | no |
| HUD with clickable buttons | `FInputModeGameAndUI` | show if needed | no |
| Pause menu / modal | `FInputModeUIOnly` + focus widget | yes | yes |
| Gameplay after closing | `FInputModeGameOnly` | no | no |
| Inventory over gameplay | `FInputModeGameAndUI` or UI-only with a deliberate design | yes | optional |

- `FInputModeUIOnly` routes all input to the widget; the pawn stops receiving move/look.
- `FInputModeGameAndUI` keeps gameplay input but widgets can still be clicked; it is the right
  mode for a HUD with a pause button.
- `SetWidgetToFocus` gives keyboard/gamepad navigation a starting point.
- `bShowMouseCursor` is on the player controller, not the widget.
- Pause (`SetPause(true)`) and input mode are independent; set both, and restore both.

## DPI and layout

- Project Settings → User Interface: `DPI Scale Rule = Shortest Side`, `Reference Resolution`
  1080p, `DPI Curve` default. Design at the reference resolution.
- `Canvas Panel` anchors behave like uGUI anchors: pin a corner or stretch to an edge.
- Use `Size Box`/`Scale Box` for controlled resizing; `Scale Box` scales its content by a
  multiplier and can letterbox.
- Text: set a font size that is readable at the reference resolution; the DPI curve scales the
  whole widget. Do not multiply font sizes by hand.
- `Safe Zone` widget for console/TV overscan; add it around HUD content that must stay visible.
- `Retainer Box` renders a widget to a texture (effects, throttled updates); use sparingly.

## Widget animations

- Animate in the UMG designer (opacity, transforms) and play with `PlayAnimation`; avoid hand-driven
  `Tick` interpolation.
- Animations can be played in reverse for close transitions; wait for the finished event before
  `RemoveFromParent` when a close animation must be seen.
- Do not animate layout groups' children sizes every frame; animate a `Render Transform` instead.

## CommonUI notes

CommonUI is a plugin for gamepad-first UI: input actions routed by widget stack, activatable
buttons, and a root widget. Setup is project-wide (input data, actions, root widget class) and
version-coupled to the engine. Use it when the game needs controller-first navigation across
menus; otherwise plain UMG plus `SetInputMode`/focus is simpler. Do not mix CommonUI's input
routing with manual `SetInputMode` calls on the same screens.

## Test checklist

1. Open the HUD: one instance, correct z-order, no duplicate on repeated opens.
2. Open and close a menu five times: no duplicate widgets, delegates fire once.
3. Pause menu: gameplay input stops, cursor appears, focus starts on the first button, gamepad
   navigation moves through all buttons, Escape/back closes.
4. Close the menu: gameplay input returns, cursor hides, time scale/pause restored.
5. 16:9, 21:9, 4:3 and 1080p/4K: HUD anchored, text readable, nothing clipped.
6. Split-screen: each player gets their own widget (`AddToPlayerScreen`), correct data.
7. Open a menu while an animation is playing: no state stuck, widget removed after the close
   animation.
8. Packaged build: widget classes are cooked and referenced (no missing class at runtime); test
   with `-game` and in a packaged build, not only PIE.
