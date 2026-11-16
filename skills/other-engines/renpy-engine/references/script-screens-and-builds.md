# Script, screens and builds

Depth for `renpy-engine`: layout, patterns, saves and tests.

## Project layout

```text
MyNovel/
├── game/
│   ├── script.rpy
│   ├── options.rpy
│   ├── screens.rpy
│   ├── gui.rpy
│   ├── images/
│   └── audio/
└── project.json
```

- `game/` is packaged; keep source assets elsewhere if you do not want them shipped.
- `screens.rpy` and `gui.rpy` are generated templates; edit deliberately.

## State patterns

```renpy
default flags = {"met_lyra": False, "route": None}
default persistent.endings = set()

label meet_lyra:
    $ flags["met_lyra"] = True
    show lyra neutral
    lyra "You're late."
```

- Use a dict for many flags; `default` it so old saves get the key.
- `persistent` for meta-progress; never store game-critical state only there.

## Screen patterns

```renpy
screen choice_hud():
    hbox:
        xalign 0.5 yalign 0.95
        spacing 20
        textbutton "Save" action ShowMenu("save")
        textbutton "Skip" action Skip() alternate Skip(fast=True, confirm=True)
        textbutton "Auto" action Preference("auto-forward", "toggle")

screen ending_gallery():
    grid 3 2:
        spacing 10
        for e in endings:
            add "gallery/[e].png" size (320, 180)
```

- `ShowMenu`, `Jump`, `Return`, `SetVariable`, `ToggleScreen` are actions, not functions.
- `timer 5.0 action Jump("timeout")` for timed choices; pair with a visible bar.

## Save and rollback rules

- Any variable that affects the story must be `default`, not `define`.
- Avoid `renpy.save` inside screens; use a button action.
- Wrap irreversible operations:

```renpy
$ renpy.block_rollback()
$ unlock_ending("true_end")
```

- On load, `after_load` can migrate flags; call `renpy.block_rollback()` after migration.

## Lint and build

```bash
renpy.sh /path/to/MyNovel lint
renpy.sh /path/to/MyNovel compile
```

- Fix every lint error; warnings often reveal unreachable labels or missing assets.
- Build from the Launcher's **Build Distributions**; select platforms and archive options.
- Test a clean build on a machine without the SDK; check saves, audio and fonts.

## Checklist

1. `lint` passes with no missing images, audio or labels.
2. Every menu choice is reachable and every branch sets state with `default`.
3. Save/load mid-scene, rollback, and skip work.
4. Old saves load after adding new flags.
5. Persistent unlocks survive a restart and a reinstall (where intended).
6. Text fits at 1280×720 and 1920×1080; long lines are split.
7. Self-voicing reads dialogue and screen alt text.
8. Music/SFX stop on main menu and quit; volume preferences apply.
9. Android/web builds launch and save correctly (test on device).
10. A clean distribution runs without the SDK.
