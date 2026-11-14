---
name: playtest-qa
description: >
  Run playtests and QA: test scripts, observation metrics, bug reports and triage, severity
  levels, regression checks, release-candidate smoke tests and accessibility passes. Use before
  a demo/release, or when bugs are reported without reproducible steps.
---

# Playtest & QA

Testing answers two different questions: *is it understandable and fun?* (playtest) and *does it
break?* (QA). This workflow covers both, from script to triage to release checklist.

## When to use

- Use before a demo, jam submission, early access or release; when planning a playtest.
- Use when bug reports lack repro steps, or a fix needs regression coverage.

**When *not* to use:** automated unit tests for code → the project's test framework; balance
tuning without players → `game-economy`; store submission mechanics → `steam-publish`.

## Playtest types

| Type | Size | Best for |
|------|------|----------|
| Self-test | 1 | crashes, flow, obvious confusion |
| Moderated | 3–8 | first-time experience, comprehension |
| Unmoderated | 10+ | funnel metrics, difficulty |
| Focus group | 5–10 | specific feature feedback |

Test with people who have not seen the game. Friends and teammates know too much.

## Script

1. **Goal** — one sentence: what decision does this playtest inform?
2. **Setup** — build id, platform, input device, time limit.
3. **Tasks** — 3–5 concrete goals ("reach the second checkpoint"), not feature tours.
4. **Think-aloud** — ask players to narrate; stay silent otherwise.
5. **Questions** — open-ended, after tasks: "What was confusing?" "What did you expect?"
6. **Wrap** — record where they stopped, deaths, time per task.

Do not explain the game during the test. If you must explain, note it as a comprehension failure.

## Observation metrics

```text
time_on_task, deaths, retries, idle time, menu time,
wrong turns, missed prompts, quit point, verbal confusion
```

- One observer takes notes; another runs the session if possible.
- Record video + timestamp; quotes are more useful than ratings.
- Aggregate by task, not by player.

## Bug report template

```text
Title: [Area] short symptom
Build: 1.4.2 (commit abc123), platform, input
Steps: 1) ... 2) ... 3) ...
Expected:
Actual:
Frequency: 3/3, 1/10
Severity: S1-S4
Evidence: video/log/save
Notes: workaround, suspected cause
```

## Severity

| Level | Meaning | Action |
|-------|---------|--------|
| S1 | crash, data loss, progression block | stop ship |
| S2 | major feature broken, no workaround | fix before ship |
| S3 | minor bug, workaround exists | fix if time |
| S4 | cosmetic/typo | backlog |

- Severity is impact, not effort.
- A crash on a rare path can still be S2 if it loses saves.

## Triage flow

1. Reproduce on the reported build; if not, ask for video/save.
2. Minimize steps; identify the system.
3. Fix, then run the regression check (the original repro + adjacent cases).
4. Add a note to the release checklist if the area is fragile.

## Release-candidate smoke test

```text
[ ] Fresh install, no dev files, default settings
[ ] New game -> first 10 minutes -> save -> quit -> continue
[ ] Settings persist; resolution/window/fullscreen; controller hot-swap
[ ] Pause/resume, alt-tab, focus loss
[ ] Audio devices changed mid-session
[ ] All menus reachable with keyboard and gamepad
[ ] Localization overflow at longest string; RTL if supported
[ ] Subtitles/captions on; colorblind cues; reduced motion
[ ] Performance on min-spec; no memory growth over 30 min
[ ] Crash logs written and contain build id
```

## Telemetry (optional)

- Log only what you will act on: session start/end, level start/end, deaths, settings changes,
  crash.
- Include build id, platform, and a random session id — no personal data.
- Disclose collection and provide opt-out where required.

## Pitfalls

- **Leading questions** → "Wasn't that fun?" Get yes. Ask "What were you trying to do?"
- **Testing only experts** → they skip tutorials and hide onboarding bugs.
- **No build id** → cannot reproduce; always record it.
- **Fixing without repro** → guess patches. Reproduce or instrument first.
- **Ignoring comprehension** → players not doing the intended thing is a design bug, not player
  error.
- **No regression pass** → fixed A breaks B. Re-run adjacent cases.
- **QA at the end only** → expensive. Smoke-test every milestone.
- **Privacy** → telemetry without consent; collect the minimum.

## Composition

- **Onboarding/UI:** `game-ui-ux`, `accessibility`.
- **Save integrity:** `save-systems` (test corrupt/old saves).
- **Performance:** `performance-optimization` for profiling during the pass.
- **Shipping:** `steam-publish` / `itch-publish` checklists.

## References

- Read `references/playtest-script-and-bug-triage.md` for a fill-in script, observation sheet,
  triage matrix and regression checklist.
