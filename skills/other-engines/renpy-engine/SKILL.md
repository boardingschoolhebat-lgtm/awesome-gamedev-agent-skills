---
name: renpy-engine
description: >
  Build visual novels in Ren'Py 8.5: script labels, say/menu, images and transitions, screen
  language, persistent data, saves/rollback, audio, options and builds for desktop, mobile and web.
  Use for a Ren'Py project or a Ren'Py-style visual novel.
---

# Ren'Py engine

Ren'Py is a Python-powered visual-novel engine with its own script language. The script is the
game: labels, dialogue, menus and screens. This is an **engine** skill: pair it with
`visual-novel` and `narrative-design` for structure.

## When to use

- Use for a `.rpy` project, or when adding choices, screens, saves or builds to a Ren'Py VN.
- Use when images/audio do not load, menus break, or a build misses files.

**When *not* to use:** a custom web VN → `visual-novel` + your web engine; a dialogue system
inside another engine → `dialogue-systems`; story structure only → `narrative-design`.

## Versions

- Ren'Py **8.5.3** ("We Can Go to the Moon", May 2026), Python 3. 8.6 is prerelease — do not
  ship it without an explicit request.
- Projects live in a folder with `game/` (scripts, images, audio) and `options.rpy`.
- Launch from the Ren'Py Launcher; CLI is `renpy.sh <project> lint` (Windows:
  `renpy.exe <project> lint`).

## Script basics

```renpy
define e = Character("Eileen", color="#c8ffc8")
default trust = 0

label start:
    scene bg room with fade
    show eileen happy at left with dissolve
    e "Welcome back. Did you sleep?"
    menu:
        "I slept well.":
            $ trust += 1
            e "You look rested."
        "I couldn't sleep.":
            e "That makes two of us."
    jump day_two
```

- `label` names a block; `jump` transfers, `call` returns.
- `define` is for constants set at init; `default` is for per-playthrough state (saved/rolled back).
- `$` runs one Python statement; `python:` runs a block.
- Indentation is syntax; use 4 spaces consistently.

## Dialogue

- `e "Text"` uses the character; a bare string is the narrator.
- Interpolation: `"You have [trust] trust."`; format with `[variable!q]` for quotes.
- Text tags: `{b}`, `{i}`, `{color=#f00}`, `{size=+4}`, `{w}` (wait), `{nw}` (no wait), `{fast}`.
- `extend` continues the previous line; `nvl` for full-screen novel text.
- Voice: `voice "line.ogg"` before the say, or auto-voice with a defined pattern.
- Keep lines short; the say box has limited space at large font sizes.

## Images and transitions

```renpy
image bg school = "bg/school.png"
image eileen happy = "eileen/happy.png"

scene bg school with fade
show eileen happy at center with dissolve
show eileen happy at left
hide eileen with dissolve
```

- `scene` clears the layer; `show` adds/updates a tag; `hide` removes.
- Attributes after the tag (`happy`) select an image variant.
- Transitions: `fade`, `dissolve`, `move`, `pixellate`, or `dissolve(0.4)`.
- ATL `transform` blocks animate position/zoom/alpha; reuse named transforms.
- Layer order: `master` (scene), `screens`, `overlay`; use `zorder` inside screens.

## Menus and choices

```renpy
menu:
    "Trust her." if trust >= 2:
        $ route = "eileen"
    "Ask about the letter.":
        $ route = "letter"
```

- A menu may have a prompt string above the choices.
- Conditions use `if` after the choice string; avoid choices that are always hidden.
- Set flags in `default`, not only inside branches, so saves stay compatible.
- For timed choices use `screen` + `timer`, not a blocking Python loop.

## Screens

```renpy
screen trust_meter():
    frame:
        xalign 0.98 yalign 0.02
        vbox:
            text "Trust: [trust]"
            bar value trust range 10

show screen trust_meter
```

- `screen name(args):` defines UI; `show screen` displays, `hide screen` removes.
- Layout: `vbox`, `hbox`, `grid`, `frame`, `viewport`, `fixed`.
- Widgets: `text`, `textbutton`, `imagebutton`, `bar`, `slider`, `input`.
- Actions: `Jump("label")`, `ShowMenu("save")`, `Return()`, `SetVariable`.
- Use `use other_screen` to compose; `style` for repeated looks.
- Screen language is declarative: do not mutate game state during prediction.

## State, saves and rollback

- Normal variables participate in save/rollback automatically.
- `persistent` survives playthroughs (galleries, endings); `default persistent.x = ...`.
- `renpy.save("slot")` / `renpy.load` for manual slots; the save screen handles most cases.
- `after_load` label fixes old saves; call `renpy.block_rollback()` if you mutate state there.
- Rollback is expected: avoid side effects (file writes, network) in script; use `renpy.block_rollback()`
  around irreversible actions.
- Do not store unserializable objects (open files, surfaces) in save state.

## Audio

```renpy
play music "audio/theme.ogg" fadein 1.0
play sound "audio/click.ogg"
stop music fadeout 2.0
```

- Channels: `music`, `sound`, `voice`; register extra channels with `renpy.music.register_channel`.
- Loop music by default; `play music ... loop` / `noloop`.
- Duck music under voice with channel mixing if needed.
- Respect the player's volume settings; they are built into preferences.

## Options and builds

`game/options.rpy`:

```renpy
define config.name = "My Novel"
define config.version = "1.0"
define build.name = "MyNovel"
define config.save_directory = "MyNovel-1234567890"
define gui.init(1920, 1080)
```

- `gui.init` sets the design resolution; test at 1280×720 and 1920×1080.
- Build via the Launcher's **Build Distributions** (Windows/macOS/Linux, Android, iOS, web).
- Ensure every asset is inside `game/`; Ren'Py archives and packages that folder.
- `lint` catches missing images, labels, audio and style issues before a build.

## Accessibility

- Ren'Py has built-in self-voicing and an accessibility menu; test with it enabled.
- Provide text speed, auto-forward, font scaling and high-contrast options where possible.
- Add `alt` text to screens/images for self-voicing.
- Avoid conveying state by color alone; pair with text/icons.

## Pitfalls

- **Missing image** → typo in tag/attribute or file outside `game/`. Run `lint`.
- **Menu never appears** → condition false or indentation broken.
- **Choices reset on load** → used `define` instead of `default`.
- **Save breaks after update** → removed/renamed variables. Add defaults and `after_load`.
- **Side effect replays on rollback** → file/network write in script. Guard it.
- **Text overflows** → long line at large font. Split lines, test at target resolution.
- **Build misses assets** → files outside `game/` or excluded by build rules.
- **Screen lags** → heavy Python in screen code. Compute in script, display in screen.
- **Audio keeps playing on menu** → stop channels on `MainMenu`/quit.
- **No translation room** → hardcoded text in images. Keep text in dialogue/strings.

## Composition

- **Genre:** `visual-novel` for branching structure, backlog, routes and endings.
- **Narrative:** `narrative-design` for beats, choices and foldback.
- **Dialogue system concepts:** `dialogue-systems` for variables/conditions outside Ren'Py.
- **UI:** `game-ui-ux` for readable text boxes and menus.
- **Localization:** `localization` for translation files and text expansion.

## References

- Read `references/script-screens-and-builds.md` for a project layout, screen patterns, save/
  persistent recipes, lint/build steps and a Ren'Py test checklist.
