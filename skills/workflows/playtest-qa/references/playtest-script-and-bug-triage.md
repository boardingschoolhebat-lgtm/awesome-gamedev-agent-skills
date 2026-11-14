# Playtest script and bug triage

Depth for `playtest-qa`: reusable script, observation sheet, triage and regression.

## Playtest script (fill in)

```text
Study:            <what decision this informs>
Build:            <version + commit>
Date / place:     <>
Facilitator:      <>
Observer:         <>
Participant:      <first-time? genre experience?>

Warm-up (2 min)
  "I'm testing the game, not you. Think aloud. I won't answer questions during play."

Tasks (20-30 min)
  1. Start a new game and reach <first objective>.
  2. <Core mechanic task>.
  3. <Failure/retry task>.
  4. <Menu/settings task>.

Prompts (only if stuck 60 s)
  "What are you trying to do right now?"
  "What do you expect to happen?"

Wrap (5 min)
  What was clear? What was confusing? What did you want to do that you couldn't?
  Would you play again? Why?
```

## Observation sheet

| Time | Task | Event | Quote / note |
|------|------|-------|--------------|
| 00:42 | 1 | missed prompt | "where do I go?" |
| 03:10 | 2 | died ×3 | tried to jump the gap |

Summarize per task: completion, time, deaths, confusion themes.

## Triage matrix

| Impact \ Frequency | Always | Often | Rare |
|--------------------|--------|-------|------|
| Crash/data loss | S1 | S1 | S2 |
| Blocked progression | S1 | S2 | S2 |
| Feature broken | S2 | S2 | S3 |
| Cosmetic | S4 | S4 | S4 |

## Regression checklist

```text
[ ] Original repro no longer occurs
[ ] Adjacent states: enter/exit, retry, reload, multiplayer
[ ] Save/load after the fixed action
[ ] No new console errors/warnings
[ ] Performance unchanged (frame time)
[ ] Automated tests for the touched system pass
```

## Minimal telemetry events

```text
session_start  {build, platform, session_id}
level_start    {level_id}
level_end      {level_id, result, duration_s, deaths}
quit           {reason?}
crash          {build, stack_hash}
```

- No names, emails, or precise location; hash ids.
- Retain raw events briefly; aggregate for decisions.
