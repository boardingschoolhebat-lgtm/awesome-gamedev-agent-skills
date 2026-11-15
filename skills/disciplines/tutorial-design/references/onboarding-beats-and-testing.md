# Onboarding beats and testing

Depth for `tutorial-design`: beat sheet, telemetry, protocol.

## Beat sheet template

| Beat | Goal | Player does | Game shows | Success signal |
|------|------|-------------|------------|----------------|
| 1 Hook | motivate | walk toward goal | vista, objective | reaches marker |
| 2 Move | teach move | move 10 m | contextual prompt | prompt fades |
| 3 Look | teach camera | look at target | highlight | target centered |
| 4 Interact | teach verb | open door | prompt + sound | door opens |
| 5 Test | confirm | open door under time | no prompt | success without help |
| 6 Combine | move + interact | climb and open | minimal hint | completes |
| 7 Mastery | optional | timed challenge | score | reward |

- Each beat: one new verb, one success condition, one failure recovery.
- Budget: 10–20 s per beat; the first 10 minutes should include a real win.

## Prompt rules

```text
[Input glyph] + Verb + Object      e.g. [E] Open door
```

- Max ~8 words; no nested clauses.
- Show once, fade after success or after 8 s; re-show on failure.
- Queue prompts; never display more than one at a time.
- Use live bindings; update on remap immediately.

## Telemetry schema

```json
{
  "event": "tutorial_beat",
  "beat": "interact_door",
  "attempt": 2,
  "success": true,
  "duration_ms": 8400,
  "prompt_shown": true,
  "skipped": false
}
```

- Funnel per beat: entered → prompt seen → action → success → next beat.
- Segment by new/returning, input device, and accessibility settings.
- Privacy: no personal data; aggregate and disclose.

## Playtest protocol

1. Recruit players unfamiliar with the genre.
2. Do not explain controls; observe silently.
3. Note the first confusion, the first success, and every repeated failure.
4. Ask: "What were you trying to do?" not "Was that clear?"
5. Record time-to-first-action and deaths per beat.
6. Re-test after changes with new players; compare beat funnels.

## Checklist

1. Every core verb is taught before it is required.
2. One prompt on screen at a time; copy is verb-first.
3. Practice has no death cost or a local respawn.
4. Prompts use live bindings and device glyphs.
5. Returning players can skip and replay; a codex exists.
6. Captions, text scaling and contrast are available.
7. Tutorial uses the real game systems, not a scripted mock.
8. Telemetry covers each beat's attempts and success.
9. Five new players reach first success without verbal help.
10. Mechanics taught are re-tested later in real play.
