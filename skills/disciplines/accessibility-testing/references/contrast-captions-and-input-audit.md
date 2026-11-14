# Contrast, captions and input audit

Depth for `accessibility-testing`: formulas, audit sheet and release checklist.

## Contrast

```text
c = channel / 255
linear = c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ^ 2.4
L = 0.2126*R + 0.7152*G + 0.0722*B
ratio = (max(L1,L2) + 0.05) / (min(L1,L2) + 0.05)
```

Targets: 4.5:1 body, 3:1 large text (≥ 24 px or 19 px bold), 3:1 UI components/focus.

## Audit sheet

| Check | Pass criteria | Result |
|-------|---------------|--------|
| Body contrast | ≥ 4.5:1 in all HUD contexts | |
| Large text | ≥ 3:1 | |
| Focus ring | visible, ≥ 3:1 | |
| Colorblind cues | shape/text alongside color | |
| Captions | verbatim, speakers, SFX, sync ±1 s | |
| No-audio run | tutorial completable | |
| Keyboard only | all menus/actions reachable | |
| Gamepad only | all menus/actions reachable | |
| Remap | every action, conflicts detected | |
| Hold/toggle | sprint/aim/crouch | |
| Reduce motion | shake/bob/FOV disabled | |
| Flash | ≤ 3 flashes/s | |
| Text size | 100–200 % without clipping | |
| Pause | cutscenes/dialogue pausable | |
| Assists | discoverable, separate from difficulty | |

## Caption format

```text
[door creaks]
Guard: Halt! Who goes there?
[sword drawn, metal scrape]
```

- Speaker names for off-screen voices.
- Describe meaningful SFX, not every footstep.
- Background box with adjustable opacity; avoid covering subtitles with HUD.

## Release checklist

1. First-run settings include accessibility (subtitles, remap, motion, contrast).
2. Settings persist and apply immediately.
3. Every critical audio cue has a visual counterpart.
4. Every color-coded element has a second channel.
5. Full game completable with one input device.
6. No unskippable flashing intro.
7. Disabled testers included in the playtest.
8. Known limitations documented honestly (e.g. screen reader coverage).
