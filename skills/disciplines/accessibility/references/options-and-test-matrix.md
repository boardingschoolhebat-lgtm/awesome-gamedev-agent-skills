# Options, contrast and test matrix

Depth for `accessibility`: the settings to ship, the numbers behind readability, and a playtest
matrix organized by player constraint.

## Options checklist

### Display
- UI scale (100–200 %) and text size (small/medium/large/extra large).
- Subtitle size, background opacity, speaker colors, caption sound descriptions.
- Contrast/high-contrast UI theme; avoid relying on hue.
- Colorblind palettes (protanopia, deuteranopia, tritanopia) plus non-color cues.
- Reduce motion, reduce flashes, disable camera shake/bob/motion blur/grain/vignette.
- FOV slider, camera distance, invert Y, brightness/gamma calibration screen.

### Controls
- Full remapping for keyboard, mouse and gamepad; two bindings per action.
- Hold/toggle for sprint, aim, crouch, block; toggle for any sustained press.
- Dead zone, sensitivity, acceleration, vibration strength.
- One-hand layouts and keyboard-only menu navigation.
- Auto-aim/aim assist strength; assist presets.

### Gameplay
- Difficulty independent of accessibility toggles.
- Longer/pausable timers, skip puzzle/section, reduced damage/invincibility.
- Navigation markers, quest arrows, objective reminders.
- Auto-complete QTEs, input buffering, coyote time on prompts.
- Combat speed or turn-based option where feasible.

### Audio
- Separate master/music/SFX/voice/dialogue buses (see `audio-design`).
- Mono downmix option; visual indicators for important sounds.
- Captions on by default; speaker names; direction hints.

### First run and pause
- Accessibility entry in the first-run flow, not only deep in settings.
- The same options reachable from pause and from the main menu.
- A "reset to defaults" that also resets remaps.

## Contrast reference

| Pair | Ratio (approx) | Use |
|------|----------------|-----|
| #FFFFFF on #000000 | 21:1 | maximum |
| #FFFFFF on #767676 | 4.54:1 | passes AA normal text |
| #000000 on #FFFFFF | 21:1 | maximum |
| #777777 on #FFFFFF | 4.48:1 | just fails AA |
| #FFFFFF on #FF0000 | 4.0:1 | fails AA normal text |

Rules:

- 4.5:1 normal text, 3:1 large text (AA); 7:1 / 4.5:1 for AAA.
- Check hover, disabled, placeholder and error states.
- Text over gameplay needs a backing panel or outline; the contrast behind it changes.
- Color alone is not an indicator: add icon, pattern, label or position.

## Caption timing

```text
minimum on screen: 1.0 s
reading time:      ~0.3 s per word (adjust for language)
hold after speech: ~0.5 s
```

- Never overlap two speakers without a clear layout.
- Keep captions within the safe area and above the HUD; allow a background box.
- Localized captions can be 30–40 % longer (`localization`).

## Motion and flash

- General flash threshold: no more than three flashes in any one-second period, and avoid large
  luminance changes; offer a reduce-flash toggle for lightning, muzzle flashes and hit flashes.
- Screen shake amplitude slider; default low; disable in cutscenes where it adds nothing.
- Provide a static camera option for cutscenes with heavy motion.
- Respect OS-level reduce-motion where the platform exposes it.

## Platform features

| Platform | Feature |
|----------|---------|
| Windows/Xbox | Xbox Accessibility Guidelines; narrator and high-contrast system themes |
| PlayStation | system text size, color filters, controller remapping |
| Switch | system button remapping, zoom |
| iOS/Android | dynamic type, reduce motion, voice control, switch control |
| Web | semantic HTML, focus order, ARIA, `prefers-reduced-motion`, zoom to 200 % |

Consoles also require store accessibility metadata; fill it accurately (it is checked).

## Playtest matrix

| Constraint | Test |
|------------|------|
| Keyboard only | complete menus and the first level without a mouse |
| Controller only | complete the same path; no keyboard prompts |
| Muted | complete a section with audio off, using captions/visual cues |
| Grayscale | identify hazards, allies, items and states without hue |
| 200 % UI | no clipping, no overlapping text, all buttons reachable |
| Reduced motion | cutscenes and combat remain playable with shake/flash off |
| Low vision | 4.5:1 text, scalable fonts, no text baked into textures |
| Motor impairment | hold/toggle, aim assist, pausable timers, one-hand layout |
| Cognitive | objective reminders, skip puzzle, plain language |
| Screen reader (web) | menus and key state announced; focus visible |

Passing the matrix means a person can complete the critical path under each constraint, not that
the option merely exists.
