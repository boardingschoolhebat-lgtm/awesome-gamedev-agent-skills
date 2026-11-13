---
name: accessibility
description: >
  Make a game playable by more people: remappable and hold/toggle input, subtitles and captions,
  colorblind-safe palettes and contrast, scalable text and UI, motion/shake/flash reduction,
  difficulty and assist options, audio cues and screen-reader-friendly web UI. Use when a game
  needs accessibility options, fails a readability or control review, or a player cannot complete
  a section. Pairs with any engine's UI and input skills.
---

# Game accessibility

Accessibility is a set of options and defaults that let more players finish the game: readable
text, remappable controls, captions, no unavoidable flashing, and assistance that does not
require a separate "easy mode" rewrite.

## When to use

- Use when adding options menus, subtitles, remapping, colorblind modes, or difficulty assists.
- Use when playtesting shows players missing cues, unable to read text, or fighting controls.
- Use when shipping to platforms or stores that require accessibility metadata.

**When *not* to use:** general UI layout and feedback → `game-ui-ux`; input architecture
implementation → `input-systems`; localization of the text itself → `localization`; color palette
production → `create-game-assets`.

## Start with the four blockers

1. **Can the player read it?** Text size, contrast, scalable UI, plain language.
2. **Can the player control it?** Remapping, hold-vs-toggle, sensitivity, one-hand and
   keyboard-only paths.
3. **Can the player perceive it?** Subtitles/captions, non-color cues, audio cues for visual
   events, visual cues for audio events.
4. **Can the player tolerate it?** Reduce motion, screen shake, flashing, camera bob, bloom.

Ship these as settings with sensible defaults; do not hide them behind a difficulty choice.

## Core workflow

1. **Audit the critical path.** Play from start to finish looking for: text under ~18 px at
   1080p, color-only signals, timed prompts, precision inputs, flashing, and audio-only cues.
2. **Fix defaults first.** High contrast text, subtitles on by default, no unavoidable shake,
   clear focus indicators. Defaults help everyone; options help the rest.
3. **Add remapping and alternatives.** Every action bindable, two keys per action, hold/toggle
   for aim/sprint/crouch, adjustable repeat and dead zones.
4. **Add subtitles and captions.** Speaker names, background sounds, direction hints; size,
   background opacity and color options.
5. **Add colorblind-safe encoding.** Pair color with shape, icon, pattern, position or label;
   offer palettes rather than a single "colorblind mode".
6. **Add motion and flash controls.** Camera shake, head bob, motion blur, film grain, flash
   intensity; respect the OS "reduce motion" setting where the platform exposes it.
7. **Add assists without changing the story.** Aim assist, longer timers, skip puzzles, invincibility,
   auto-complete QTEs, navigation hints.
8. **Verify with real constraints.** Keyboard-only, controller-only, muted audio, grayscale,
   large text, and a 200 % UI scale.

## Patterns

### 1. Contrast that actually passes

```text
relative luminance:  L = 0.2126 R + 0.7152 G + 0.0722 B   (linearized sRGB channels)
contrast ratio:      (L1 + 0.05) / (L2 + 0.05)            (lighter over darker)
```

- WCAG AA: 4.5:1 for normal text, 3:1 for large text (≥ 24 px, or ≥ 19 px bold).
- WCAG AAA: 7:1 normal, 4.5:1 large.
- Do not round: 4.49:1 fails 4.5:1.
- Check the **rendered** background, not the intended one: a text over a gradient or video needs a
  solid backing panel or an outline.
- Do not encode state with hue alone: a red/green health bar needs a label, icon or fill pattern
  as well.

```python
def luminance(rgb):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)
```

### 2. Input options

```text
- Every action remappable, including menu navigation.
- Two bindings per action (keyboard + gamepad) and a "reset to defaults".
- Hold/toggle for sprint, aim, crouch, and any sustained press.
- Adjustable dead zone, sensitivity, inversion, and vibration.
- No rapid repeated taps without an alternative (or a "hold instead" option).
- Pause anywhere that is not a server-authoritative multiplayer match.
```

Avoid chorded inputs as the only path (Ctrl+Alt+key), and do not require simultaneous
keyboard+mouse for a basic action if a controller-only path is feasible.

### 3. Subtitles and captions

```text
[door creaks]
Innkeeper: You're late. (sighs)
[footsteps approaching from the left]
```

- Speaker names and sound descriptions in brackets; direction when it matters.
- Options: size (small/medium/large), background (none/box/dim), color, and a preview line.
- Keep captions on screen long enough to read: roughly 2 seconds + reading time, and never
  shorter than 1 second.
- Localize captions like any other string (`localization`).
- Do not put critical information only in audio without a visual or caption alternative.

### 4. Motion, flash and camera

- Screen shake: slider (0–100 %), default modest; never on the critical path.
- Flashing: cap to three flashes per second and keep luminance change below the general flash
  threshold; offer a "reduce flashes" toggle for effects.
- Camera bob, motion blur, depth of field, film grain, chromatic aberration: individual toggles.
- FOV slider (60–110) and camera distance for motion sickness.
- Respect platform reduce-motion settings where available; otherwise surface the option early.

### 5. Difficulty and assists

| Assist | Why |
|--------|-----|
| Aim assist / magnetism | motor impairments, controller play |
| Longer or pausable timers | cognitive and motor constraints |
| Skip puzzle / skip section | blockers with no alternative path |
| Invincibility / reduced damage | completing the story |
| Auto-complete QTEs | rapid repeated input |
| Navigation markers / quest arrows | orientation and memory |
| Combat speed slider | reaction time |

Assists should not mock the player, change achievements silently, or require a new game. Document
what each one changes.

### 6. Web and screen readers

- Use real semantic HTML for menus (`<button>`, `<nav>`, `<label>`), not divs with click handlers.
- Keyboard focus visible and ordered; Escape closes modals; focus trapped in dialogs.
- `aria-label` on icon-only buttons; `aria-live` for score/toast updates.
- Respect `prefers-reduced-motion` and `prefers-color-scheme`.
- A canvas game still needs a DOM layer for menus if screen-reader access is a goal.

## Pitfalls

- **"Colorblind mode" that only shifts hue** → still unreadable for some players. Add shape,
  pattern, icon or text.
- **Subtitles that only cover dialogue** → important sounds (alarms, approaching enemies) are
  missed. Caption them too.
- **Text scales but panels do not** → overflow and clipping. Scale the layout, not only fonts.
- **Remapping that breaks menus** → menu navigation is hardcoded. Route all input through the
  same action map.
- **Shake/flash options buried** → players quit before finding them. Surface accessibility in the
  first-run options and in pause.
- **Assists disable achievements silently** → communicate the rule before the player commits.
- **Accessibility only on "easy"** → difficulty and accessibility are different axes. Keep
  options independent.
- **No keyboard-only path** → mouse-only menus or drag-only interactions. Provide focus and
  activation keys.
- **Low-contrast placeholder text** → hints and disabled states often fail contrast. Check every
  state, not only the main label.
- **No screen-reader labels in the web build** → canvas-only UI is invisible to assistive tech.
  Provide DOM menus and labels.

## References

- Read `references/options-and-test-matrix.md` for the options checklist, contrast examples,
  caption timing rules, platform features and a playtest matrix by constraint.

## Related skills

- `game-ui-ux` — hierarchy, readability and feedback design.
- `input-systems` — remapping, action maps, dead zones and buffering.
- `localization` — translating captions and UI text.
- `audio-design` — audio cues and ducking for captions.
- `game-feel` — shake, flash and feedback that must remain optional.
