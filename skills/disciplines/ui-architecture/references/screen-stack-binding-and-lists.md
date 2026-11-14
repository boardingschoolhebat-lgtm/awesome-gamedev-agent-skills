# Screen stack, binding and lists

Depth for `ui-architecture`: stack rules, binding patterns, virtualization and tests.

## Screen stack pseudocode

```text
stack = []

push(screen):
    if stack.not_empty: stack.top.hide()
    stack.push(screen)
    screen.show()
    screen.focus_first()
    update_pause()

pop():
    if stack.empty: return
    stack.pop().hide()
    if stack.not_empty: stack.top.show(); stack.top.focus_last()
    update_pause()

update_pause():
    gameplay.paused = stack.any(s => s.pauses_game)
```

- `replace` = pop all + push (main menu).
- Modals push with `blocks_input = true`.
- Back button maps to `pop()`; the root screen ignores back.

## Binding patterns

Pull (simple):

```text
on_show: refresh_all()
on_change: refresh_field(key)
```

Push (scalable):

```text
subscribe(model.changed, view.apply)
view.apply(key, value) -> switch(key) { ... }
```

- Always unsubscribe on hide/destroy.
- Use a dirty set and flush once per frame for high-frequency values.
- Keep formatting in the view; keep raw values in the model.

## List virtualization

```text
visible_range = floor(scroll / row_height) .. ceil((scroll + viewport) / row_height)
for i in visible_range: bind(row_pool[i % n], data[i])
```

- Fixed row height makes math trivial; variable height needs measured layout.
- Bind by stable id, not index, if the list reorders.
- Recycle rows across screens only if the row type matches.

## Theme tokens

```text
color.bg        #12141a
color.text      #f2f4f8
color.accent    #4cc2ff
space.sm        4
space.md        8
space.lg        16
type.body       16
type.title      24
```

- Swap the token set for high contrast / colorblind modes.
- No raw values in widget code.

## Test checklist

1. Push/pop 10 screens; no leaked handlers or duplicated UI.
2. Back from every screen reaches a valid state.
3. Pause state matches the stack.
4. Focus returns to the invoking control.
5. Gamepad-only navigation reaches every action.
6. Long list (1,000 rows) scrolls at frame rate.
7. Rapid open/close during gameplay does not desync HUD.
8. Longest localized string fits; RTL mirrors layout.
9. UI hidden state costs no layout/update.
10. Save/load restores menu-independent state correctly.
