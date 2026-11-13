---
name: unreal-ui
description: >
  Build UMG interfaces in Unreal Engine 5.8: widget blueprints and C++ UUserWidget subclasses,
  CreateWidget and AddToViewport lifetimes, BindWidget references, input modes and focus, DPI
  scaling, and HUD, menu and pause patterns. Use when an Unreal project needs a HUD, menu, pause
  screen, inventory, or widget input handling. Targets UE 5.8.
---

# Unreal UMG

Build gameplay UI as UMG widgets: a Widget Blueprint for layout, a C++ or Blueprint class for
behaviour, and an explicit owner that creates, adds and removes it. Targets **Unreal Engine 5.8**.

## When to use

- Use when adding a HUD, menu, pause screen, inventory, settings page or modal dialog.
- Use when a widget does not appear, appears twice, blocks gameplay input, or loses gamepad focus.

**When *not* to use:** UI design and hierarchy → `game-ui-ux`; input actions and mapping contexts
→ `unreal-enhanced-input`; Slate/editor tooling is a different framework; world-space 3D widgets
use UMG plus `unreal-cpp-gameplay`.

## Core workflow

1. **Create the Widget Blueprint.** `Content/UI/WBP_HUD`, with the intended C++ class as its
   parent when the logic is code-driven; keep layout in the designer, logic in the class.
2. **Choose the root panel.** `Canvas Panel` for free placement with anchors, `Overlay`/`Size Box`
   for a single full-screen child, `Vertical Box`/`Horizontal Box` for lists. Anchor HUD elements
   to the edges or corners they belong to.
3. **Set DPI scaling once.** Project Settings → User Interface: `DPI Scale Rule = Shortest Side`,
   reference resolution 1080p, and design at that resolution. Do not compensate with per-widget
   scale hacks.
4. **Create from an owner.** `CreateWidget<UMyHud>(GetWorld(), HudClass)`, keep the result in a
   `UPROPERTY()` so it is not garbage collected, then `AddToViewport(ZOrder)`.
5. **Bind references.** `UPROPERTY(meta = (BindWidget)) UProgressBar* HealthBar;` — the name must
   match the widget in the designer, or the widget fails to load with a clear error.
6. **Set the input mode deliberately.** Menus: `FInputModeUIOnly` with `SetWidgetToFocus` and
   `bShowMouseCursor = true`; HUD overlays: `FInputModeGameAndUI` with focus rules; gameplay:
   `FInputModeGameOnly` when the menu closes.
7. **Wire delegates once.** `Button->OnClicked.AddDynamic(this, &UMyWidget::HandleClick)` in
   `NativeConstruct`, and remove them in `NativeDestruct`; UMG re-runs construct on re-add.
8. **Update from gameplay, not Tick.** Call a setter on the widget when health/score changes; a
   widget `Tick` that polls the pawn is the usual HUD cost.

## Patterns

### 1. A C++ widget base

```cpp
// MyHud.h
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MyHud.generated.h"

class UProgressBar;
class UTextBlock;
class UButton;

UCLASS(Abstract)
class MYGAME_API UMyHud : public UUserWidget
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "HUD")
    void SetHealth(float Current, float Max);

protected:
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;

    UPROPERTY(meta = (BindWidget))
    TObjectPtr<UProgressBar> HealthBar;

    UPROPERTY(meta = (BindWidget))
    TObjectPtr<UTextBlock> HealthText;

    UPROPERTY(meta = (BindWidgetOptional))
    TObjectPtr<UButton> PauseButton;

private:
    UFUNCTION()
    void HandlePauseClicked();
};
```

```cpp
// MyHud.cpp
#include "MyHud.h"
#include "Components/Button.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"

void UMyHud::NativeConstruct()
{
    Super::NativeConstruct();
    if (PauseButton)
    {
        PauseButton->OnClicked.AddDynamic(this, &UMyHud::HandlePauseClicked);
    }
}

void UMyHud::NativeDestruct()
{
    if (PauseButton)
    {
        PauseButton->OnClicked.RemoveDynamic(this, &UMyHud::HandlePauseClicked);
    }
    Super::NativeDestruct();
}

void UMyHud::SetHealth(float Current, float Max)
{
    const float Ratio = Max > 0.f ? FMath::Clamp(Current / Max, 0.f, 1.f) : 0.f;
    if (HealthBar)
    {
        HealthBar->SetPercent(Ratio);
    }
    if (HealthText)
    {
        HealthText->SetText(FText::FromString(FString::Printf(TEXT("%.0f / %.0f"), Current, Max)));
    }
}

void UMyHud::HandlePauseClicked()
{
    // Route through the game mode/player controller, not the widget.
    if (APlayerController* PC = GetOwningPlayer())
    {
        PC->TogglePauseMenu();
    }
}
```

`TObjectPtr` is the current pointer type for UObject members. `meta = (BindWidgetOptional)` lets a
widget that is not in the designer stay null; a required `BindWidget` that is missing fails the
widget blueprint compile, which is the intended early warning.

### 2. Create, add and remove

```cpp
void AMyPlayerController::ShowHud()
{
    if (HudInstance)
    {
        return;                                   // already on screen
    }
    HudInstance = CreateWidget<UMyHud>(this, HudClass);
    if (HudInstance)
    {
        HudInstance->AddToViewport(0);            // z-order 0, below menus
    }
}

void AMyPlayerController::HideHud()
{
    if (HudInstance)
    {
        HudInstance->RemoveFromParent();
        HudInstance = nullptr;                    // recreate on next show
    }
}
```

`AddToViewport` called twice adds the widget twice (two entries in the viewport), so guard with a
`UPROPERTY()` pointer and clear it after `RemoveFromParent`. `AddToPlayerScreen` exists for
split-screen local players.

### 3. Input mode and focus

```cpp
void AMyPlayerController::OpenPauseMenu()
{
    if (!PauseMenu)
    {
        PauseMenu = CreateWidget<UMyPauseMenu>(this, PauseMenuClass);
    }
    PauseMenu->AddToViewport(10);

    FInputModeUIOnly Mode;
    Mode.SetWidgetToFocus(PauseMenu->TakeWidget());
    Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    SetInputMode(Mode);
    bShowMouseCursor = true;
    SetPause(true);
}

void AMyPlayerController::ClosePauseMenu()
{
    if (PauseMenu)
    {
        PauseMenu->RemoveFromParent();
        PauseMenu = nullptr;
    }
    FInputModeGameOnly Mode;
    SetInputMode(Mode);
    bShowMouseCursor = false;
    SetPause(false);
}
```

- `FInputModeUIOnly` stops gameplay input entirely; use it for modal menus, not for a HUD.
- `FInputModeGameAndUI` keeps the game receiving input while the widget can be clicked; set
  `SetHideCursorDuringCapture` deliberately.
- Without `SetWidgetToFocus`, keyboard/gamepad navigation has no start point, and the menu appears
  frozen.
- Unpause with `SetPause(false)` and restore the previous input mode, not a guessed default.

### 4. HUD overlay without stealing input

```cpp
void AMyPlayerController::ShowHudOverlay()
{
    HudInstance = CreateWidget<UMyHud>(this, HudClass);
    HudInstance->AddToViewport(0);

    FInputModeGameAndUI Mode;
    Mode.SetWidgetToFocus(HudInstance->TakeWidget());
    Mode.SetLockMouseToViewportBehavior(EMouseLockMode::LockOnCapture);
    Mode.SetHideCursorDuringCapture(false);
    SetInputMode(Mode);                 // widget can be clicked, game still moves
    bShowMouseCursor = false;
}
```

If the HUD is purely informational, do not change the input mode at all; a widget with no
interactive children does not need focus and should not divert input.

### 5. Lists and data-driven widgets

- Build repeated rows (inventory, leaderboard) in a `UListView` or a `Vertical Box` fed by a
  `UUserWidget` row class; do not hand-place dozens of widgets in the designer.
- Bind rows to a data object (`UObject` with `BlueprintType`) and update only the changed row.
- For tabs, keep one widget per tab and toggle `Visibility` (`Collapsed` removes it from layout,
  `Hidden` keeps its slot) rather than recreating widgets.
- Animate with UMG animations (`PlayAnimation`) for open/close; do not drive layout by hand in
  `Tick`.

### 6. CommonUI and gamepad navigation

CommonUI adds input routing, activatable widgets and widget stacks for gamepad-first games. It is
a plugin with its own setup (input data, root widget, actions); pin its version with the engine and
follow its documentation instead of mixing CommonUI and raw `SetInputMode` calls in the same
screen. For a single-player menu without gamepad focus requirements, plain UMG is enough.

## Pitfalls

- **Widget disappears immediately** → the only reference was a raw pointer, so it was garbage
  collected. Store it in a `UPROPERTY()`.
- **Widget appears twice** → `AddToViewport` called on every open, or a new instance created each
  time. Guard with an instance pointer.
- **Clicks do nothing** → input mode is `GameOnly`, another widget is on top, or the widget is not
  focusable/visible. Check `SetInputMode`, z-order and `Visibility`.
- **Game freezes behind a menu** → `SetPause(true)` with a widget whose `Tick` still expects to
  run, or the pause menu widget is not set to tick while paused. Use the widget's
  `TickFrequency`/player controller tick settings deliberately.
- **Gamepad navigation does not start** → no `SetWidgetToFocus`, or buttons are not focusable.
- **`BindWidget` fails to compile the widget** → the variable name does not match the designer
  widget, or the type is wrong. Rename one side, or use `BindWidgetOptional` when absence is
  valid.
- **Delegate fires multiple times** → `AddDynamic` runs again on every `NativeConstruct` without a
  matching `RemoveDynamic`; bind in construct, unbind in destruct.
- **HUD costs frame time** → per-frame `Tick` polling the pawn. Push updates from gameplay events
  instead.
- **Text is blurry or tiny on 4K** → DPI scale rule/reference resolution is wrong, or the font size
  is set in pixels for one resolution. Set the project DPI rule and use the designer at the
  reference resolution.
- **Widget shows the wrong player's data in split-screen** → `GetOwningPlayer()` is not the
  intended player, or the widget was created with the wrong world/owner. Create per player
  controller and use `AddToPlayerScreen`.

## References

- Read `references/umg-lifetimes-and-input.md` for the UMG API table, widget lifetime rules, input
  mode matrix, DPI settings and a test checklist.

## Related skills

- `game-ui-ux` — hierarchy, feedback, readability and accessibility.
- `unreal-cpp-gameplay` — player controller, game mode and pawns that own the UI.
- `unreal-enhanced-input` — input actions and mapping contexts behind menu actions.
- `unreal-blueprints` — Blueprint-only widgets and event graphs.
- `unity-ui` / `godot-ui-control` / `defold-ui` — the same concerns in other engines.
