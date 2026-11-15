---
name: tutorial-design
description: >
  Design onboarding and tutorials: teach one mechanic at a time, safe practice, contextual
  prompts, diegetic teaching, skip/revisit, and telemetry that proves comprehension. Use when
  new players quit, miss mechanics, or a tutorial feels like a text wall.
---

# Tutorial design

A tutorial is a level whose job is to change the player's behavior. It succeeds when players
perform the mechanic correctly without being told twice, not when they finish reading. This is a
**compositional** skill: pair with `level-design`, `game-ui-ux` and `playtest-qa`.

## When to use

- Use when designing the first 10 minutes, a new mechanic, or a mid-game teaching beat.
- Use when playtests show confusion, repeated deaths, or skipped/ignored prompts.

**When *not* to use:** difficulty tuning after mastery → `game-balance`; narrative pacing →
`narrative-design`; control remapping/accessibility → `accessibility`.

## Principles

1. **Teach by doing.** A prompt the player acts on beats a paragraph.
2. **One mechanic at a time.** Introduce, practice, test, then combine.
3. **Safe failure.** Practice with no death cost, or a fast, local respawn.
4. **Immediate feedback.** Confirm success within a few frames and name what happened.
5. **Contextual, not front-loaded.** Show the prompt where the mechanic is needed.
6. **Show, then tell.** Demonstrate with a ghost, arrow or example, then label it.
7. **Respect returning players.** Skip, replay and a mechanics codex.
8. **Never block on reading.** Text advances, pauses the sim, and is captioned.

## Beat structure

```text
hook -> introduce -> guided practice -> independent test -> combine -> mastery
```

- Hook: a 10–30 s fantasy that motivates the mechanic.
- Introduce: one verb, one input, one visible result.
- Guided: prompt + safe target; success is hard to miss.
- Test: same verb, less prompting, a small consequence.
- Combine: pair with the previous verb.
- Mastery: optional challenge for confident players.

## Prompt copy

- Verb-first: "Hold **Shift** to sprint", not "Sprinting is performed by holding Shift".
- One sentence, one action; no lore in the prompt.
- Use the player's actual bindings and device glyphs.
- Anchor to the object: prompt near the door, not in a corner.
- Fade after success; do not stack three prompts at once.
- Localize with keys, and leave room for +40 % text expansion.

## Diegetic vs explicit

| Approach | Use when | Risk |
|----------|----------|------|
| Diegetic (signs, NPC, environment) | immersion matters, action is simple | missed by players who ignore scenery |
| Explicit overlay | precision needed, accessibility | breaks flow, text wall |
| Hybrid | most games | inconsistent tone if overused |

- Whatever the style, the mechanic must be testable immediately.
- Critical mechanics need a non-diegetic fallback (codex, prompt, tooltip).

## Measuring comprehension

```text
time_to_first_action
attempts_to_first_success
deaths_in_tutorial
prompt_seen -> action_taken rate
skip_rate
drop-off at each beat
post_tutorial mechanic use (e.g. dodge rate in first fight)
```

- Instrument beats, not just the tutorial start/end.
- Watch 5–10 new players; telemetry tells you where, observation tells you why.
- If players succeed but cannot repeat it later, the tutorial taught the prompt, not the mechanic.

## Accessibility

- Captions for spoken instructions; text size and contrast options.
- Remap prompts to the live bindings; support keyboard, gamepad and touch.
- Adjustable tutorial pacing; pause on prompt; no timed reading.
- Option to replay any tutorial from the menu.
- Avoid teaching via color alone; pair with shape/icon.

## Pitfalls

- **Text wall at the start** → players skip everything. Teach at the point of use.
- **Unskippable tutorial** → returning players churn. Offer skip + codex.
- **Prompt spam** → players stop reading. One prompt, fade on success.
- **Teaching by failure only** → frustration. Guided practice before the test.
- **Mechanic introduced once, never reused** → forgotten. Re-test later.
- **Tutorial and real game differ** → skills do not transfer. Use the real systems.
- **No failure recovery** → stuck at the first pit. Local respawn, no lost progress.
- **Assuming genre literacy** → missed basics. Teach camera, move, interact explicitly.
- **No measurement** → cannot prove it works. Instrument beats and watch players.

## Composition

- **Levels:** `level-design` for teaching layouts and sightlines.
- **UI:** `game-ui-ux` + `ui-architecture` for prompts, codex and focus.
- **QA:** `playtest-qa` for observation scripts and comprehension metrics.
- **Accessibility:** `accessibility` + `accessibility-testing` for captions/remapping.
- **Narrative:** `narrative-design` when teaching is woven into the story.

## References

- Read `references/onboarding-beats-and-testing.md` for a beat sheet, prompt rules, telemetry
  schema, playtest protocol and a tutorial checklist.
