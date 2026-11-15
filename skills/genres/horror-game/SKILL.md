---
name: horror-game
description: >
  Build a horror game: vulnerability and resource scarcity, pacing and safe zones, monster rules
  and chase AI, lighting and audio, hiding/chase loops, restrained scares, save/checkpoint design
  and accessibility. Use for survival horror, atmospheric horror, or a scary sequence.
---

# Horror game

Horror is anticipated threat plus limited agency. The monster matters less than the rules the
player learns about it. This is a **compositional** skill: pair with `audio-design`,
`level-design`, `game-ai` and `accessibility`.

## When to use

- Use when building survival horror, a chase sequence, a haunted level, or an atmosphere-first game.
- Use when playtests show tension collapsing into boredom or frustration.

**When *not* to use:** action horror where combat is the core → `fps-shooter` + `game-ai`; stealth
planning without fear → `stealth-game`; pure narrative horror → `visual-novel`.

## Pillars

1. **Vulnerability** — the player cannot simply win a fight.
2. **Uncertainty** — rules are learnable but not fully known.
3. **Pacing** — tension, release, tension; not constant screaming.
4. **Agency** — hiding, running, barricading, choosing when to risk.
5. **Restraint** — the unseen is scarier than the shown.

## Resource loop

```text
explore -> gather (light, health, ammo, keys) -> threat -> spend resources -> retreat/safe zone
```

- Scarcity must be tuned so the player is uncomfortable, not softlocked.
- Ammo should be a decision ("fight or avoid"), not a DPS check.
- Light/battery is a timer that shapes exploration; give refills near key routes.
- Safe zones create release; too many remove tension.

## Monster design

| Property | Question |
|----------|----------|
| Rules | What does it react to (sound, light, sight, items)? |
| Counterplay | Hide, run, distract, block, wait? |
| Predictability | Can the player learn its patrol/chase? |
| Escape | Is there always a route or a timer? |
| Presence | Audio/visual tells before it appears? |

- One strong monster with clear rules beats five indistinct ones.
- Chase AI: direct but not perfect; lose sight → search, not omniscience.
- Hiding must be risky (monster checks spots) or tension disappears.
- Scripted scares are seasoning; systemic threat is the meal.

## Pacing

```text
calm exploration (2-5 min) -> unease cues -> encounter -> escape -> recovery beat
```

- Alternate high and low intensity; constant threat exhausts players.
- Foreshadow with sound, environment, and distant glimpses.
- Give the player a moment to breathe after a chase before the next one.

## Audio and lighting

- Audio carries most of the fear: footsteps, breathing, distant impacts, silence.
- 3D audio tells direction; use it for off-screen threats.
- Music is optional; silence plus ambience often works better.
- Darkness needs a readable player light and landmarks; total black is frustrating.
- Flicker and strobing require a photosensitivity option (≤ 3 flashes/s).

## Scares

- Build anticipation, then subvert; do not fire a jumpscare every corridor.
- A quiet room after a loud one is a scare.
- Do not fake danger with unreactable instant deaths; telegraph.
- Respect the player: no cheap "gotcha" that invalidates learning.

## Saves and failure

- Checkpoint before major encounters, not after every step.
- Death should cost progress but not replay 20 minutes.
- Autosave with a visible indicator; allow manual save where the fiction supports it.
- Persistent threats across saves can be a feature; document it.

## Accessibility

- Photosensitivity and motion options, including camera shake and FOV.
- Subtitles for creature sounds and directional cues.
- Difficulty/assist options that reduce threat without removing the story.
- Content warnings for gore, flashing and abuse themes.

## Pitfalls

- **No safe zones** → exhaustion, not fear. Alternate intensity.
- **Unkillable stalker with no counterplay** → frustration. Give rules and escapes.
- **Resource softlock** → no ammo/light and no way forward. Guarantee minimum supplies.
- **Monster teleports** → players stop trusting rules. Keep it physical and consistent.
- **Jumpscare spam** → desensitization. Use restraint.
- **Unreadable darkness** → players get lost, not scared. Landmarks and light.
- **Death loop** → long replays. Checkpoints before encounters.
- **Audio-only cues** → deaf players miss threats. Add visual tells.
- **Forced slow walk** → removes agency. Shorten or justify it.

## Composition

- **AI:** `game-ai` for patrol/chase/search; `stealth-game` for detection models.
- **Audio:** `audio-design` for dynamic music, stingers, 3D cues.
- **Levels:** `level-design` for sightlines, loops, safe rooms.
- **UI:** `game-ui-ux` for minimal HUD and readability.
- **Accessibility:** `accessibility`, `accessibility-testing`.

## References

- Read `references/pacing-monsters-and-scares.md` for a tension curve, monster rule sheet,
  resource budgets and a horror playtest checklist.
