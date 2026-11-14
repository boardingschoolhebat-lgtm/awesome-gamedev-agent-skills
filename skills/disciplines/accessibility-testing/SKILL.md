---
name: accessibility-testing
description: >
  Audit game accessibility: contrast math, colorblind and motion checks, subtitle/caption
  accuracy, full input-only navigation, remapping, screen-reader limits, assist modes and
  testing with disabled players. Use before release or when accessibility is claimed but unverified.
---

# Accessibility testing

Accessibility claims are testable. Measure contrast, play with the screen off, navigate with one
hand, and watch captions against audio. This is a **compositional** skill: pair with
`accessibility` for design and `playtest-qa` for the test session.

## When to use

- Use when auditing a build, writing an accessibility test plan, or verifying a settings menu.
- Use when players report unreadable text, missed cues, or impossible inputs.

**When *not* to use:** designing the features → `accessibility`; localization layout →
`localization-qa`; platform certification requirements → platform docs.

## Standards to borrow

- **WCAG 2.2** contrast: 4.5:1 for normal text, 3:1 for large text (≥ 24 px or 19 px bold).
- Non-text UI components and focus indicators: 3:1 against adjacent colors.
- Captions: synchronized, speaker-identified, sound effects described.
- Flashing: avoid more than 3 flashes per second (photosensitivity).

Games are not websites, but these thresholds are a useful floor.

## Test matrix

| Area | Test |
|------|------|
| Vision | contrast, text size 100–200 %, colorblind sim, no color-only cues |
| Hearing | captions on, no audio, visual cues for threats |
| Motor | keyboard only, one hand, no rapid input, remap all actions |
| Cognition | clear objectives, pause anywhere, no timed menus |
| Photosensitivity | flash check, reduce-motion mode |
| Screen reader | menus readable where platform supports it |

## Procedures

### 1. Contrast

```text
L = 0.2126 R + 0.7152 G + 0.0722 B      # linearized channels
ratio = (L1 + 0.05) / (L2 + 0.05)       # lighter / darker
```

- Sample actual rendered pixels, not design tokens; backgrounds vary.
- Test HUD over gameplay, subtitles over video, disabled states.
- Large text 3:1; body 4.5:1; icons/focus 3:1.

### 2. Colorblind

- Simulate deuteranopia, protanopia, tritanopia.
- Any cue conveyed by color alone must also use shape, icon, pattern or text.
- Check team colors, loot rarity, damage types, map markers.

### 3. Captions

- Play with audio muted; can you still complete the tutorial?
- Captions match audio within ~1 s, identify speakers, include key SFX.
- Size/background options; no overlap with critical HUD.

### 4. Input

- Complete the first 15 minutes with keyboard only, then gamepad only.
- Remap every action, including menu navigation; detect conflicts.
- Hold/toggle options for sprint, aim, crouch.
- No simultaneous multi-button requirements without an alternative.
- Focus visible at all times; no focus traps.

### 5. Motion and flash

- Reduce motion: camera shake, head bob, FOV kicks, parallax.
- Flash test: count flashes in the most intense 10 s.
- Provide motion smoothing and camera speed options.

### 6. Screen readers and platforms

- Console screen readers vary; test the actual platform, do not assume.
- Menus need labels, roles, and reading order; avoid icon-only buttons.
- Text-to-speech for chat with opt-in.

### 7. Cognitive

- Pause cutscenes and dialogue; skip with summary.
- Objective reminders; waypoint toggle.
- Difficulty assists separate from difficulty presets.

## Reporting

```text
Issue: subtitle for boss roar missing
Area: captions / audio cues
Severity: blocks deaf players from reacting
Repro: mute audio, enter boss arena
Expected: caption "[boss roars]" + visual shockwave cue
```

- Severity by player impact, not effort.
- Include a screenshot/video with the accessibility setting enabled.

## Pitfalls

- **Token-only contrast checks** → rendered backgrounds differ. Sample pixels.
- **Color-only cues** → colorblind players fail. Add shapes/text.
- **Captions paraphrase** → missed information. Verbatim + SFX.
- **Remap partial** → some actions fixed. Cover menus and holds.
- **Motion settings ignored** → reduce-motion does nothing. Wire every shake/bob.
- **Screen reader untested** → labels missing. Test on target platform.
- **Assist mode hidden** → nobody finds it. Surface in first-run settings.
- **Testing only with non-disabled players** → misses real barriers. Include disabled testers.

## Composition

- **Design:** `accessibility` for features and defaults.
- **UI:** `ui-architecture` for focus/navigation; `game-ui-ux` for readability.
- **Subtitles/localization:** `localization-qa` for caption text.
- **QA:** `playtest-qa` for the session script and bug triage.
- **Input:** `input-systems` for remapping and hold/toggle.

## References

- Read `references/contrast-captions-and-input-audit.md` for formulas, an audit sheet and a
  release accessibility checklist.
