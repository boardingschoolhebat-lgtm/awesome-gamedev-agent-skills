---
name: analytics
description: >
  Instrument a game: event taxonomy and schema, funnels, cohorts, retention and KPI definitions,
  A/B tests, dashboards, validation and privacy/consent. Use for telemetry design, player
  behavior questions, or analytics that nobody trusts.
---

# Game analytics

Analytics exists to answer decisions, not to collect everything. Define the question, the event
schema, and the metric before writing a line of telemetry. This is a **compositional** skill:
pair with `playtest-qa`, `liveops` and `game-economy`.

## When to use

- Use when adding telemetry, defining KPIs, building funnels, or running an A/B test.
- Use when dashboards disagree with reality or events are missing/duplicated.

**When *not* to use:** crash reporting only → platform crash service; server monitoring →
backend observability; marketing attribution → store/platform analytics.

## Start from questions

```text
Question: where do new players quit?
Metric:   % reaching level 2 within 10 minutes
Events:   session_start, level_start, level_end, quit
Decision: if < 40 %, shorten the tutorial
```

- If no decision depends on it, do not log it.
- One owner per metric; documented definition.

## Event taxonomy

```text
<object>_<action>   e.g. level_start, purchase_complete, quest_abandon
```

Schema per event:

```json
{
  "name": "level_end",
  "ts": "server or client time, ISO-8601",
  "session_id": "random uuid",
  "player_id": "hashed stable id",
  "build": "1.4.2+abc123",
  "platform": "steam",
  "props": { "level_id": "forest_02", "result": "win", "duration_s": 312, "deaths": 4 }
}
```

- Stable names; never rename without a migration/alias.
- Enums, not free text; units in the key (`duration_s`).
- No personal data in props; hash ids.
- Include build and platform on every event.

## Core metrics

| Metric | Formula |
|--------|---------|
| DAU/MAU | unique players per day / per month |
| Retention Dn | new cohort active on day n / cohort size |
| Session length | median session duration |
| Conversion | buyers / active players |
| ARPDAU | revenue / DAU |
| Funnel step % | reached step / reached previous step |
| Churn | players active last period, not this one |

- Report medians and percentiles, not only averages.
- Segment before concluding: platform, region, new vs veteran.

## Funnels and cohorts

```text
session_start -> tutorial_start -> tutorial_end -> level_1_start -> level_1_end
```

- A funnel step must be reachable in one session to compare cleanly.
- Cohorts by install week; compare like-for-like.
- Watch survivorship bias: only counting players who stayed.

## A/B tests

```text
hypothesis -> metric -> sample size -> randomize -> run -> analyze
```

- One primary metric; guardrail metrics for harm.
- Randomize by player, not session, unless the change is session-scoped.
- Precompute sample size; do not peek and stop early.
- Practical significance matters more than p-values.
- Document the result, including nulls.

## Pipeline

```text
client -> queue/batch -> ingest endpoint (validate) -> warehouse -> dashboards
```

- Batch and retry; never block gameplay on telemetry.
- Validate schema server-side; drop malformed events with counters.
- Sample high-volume events deliberately and document the rate.
- Version the schema; keep raw events for re-processing.

## Privacy and consent

- Collect the minimum; no names, emails, or precise location.
- Disclose collection; opt-out where required (GDPR/COPPA/local law).
- Retention limit; delete on request.
- Do not log chat content or device identifiers unless justified.
- Server-side events are more trustworthy than client-reported ones.

## Patterns

### 1. Server-authoritative key events

```text
server emits purchase_complete, level_end, quest_complete
client emits ui_click, settings_change
```

- Economy and progression events must come from the server.
- Client events are for UX, not truth.

### 2. Session stitching

- `session_id` at launch; rotate after a long idle.
- Link sessions to a hashed player id for cohorting.
- Handle offline play: queue events and flush on reconnect.

### 3. Debug overlay

- Show the last N events and their send status in dev builds.
- A missing event should be visible during QA, not discovered in a dashboard.

## Pitfalls

- **Vanity metrics** → downloads/DAU without decisions. Tie to questions.
- **Duplicate events** → double-counted funnels. Idempotency keys.
- **Renamed events** → broken dashboards. Version and alias.
- **Client-trusted economy** → inflated numbers and cheats. Server events.
- **No build dimension** → cannot attribute a regression. Always include build.
- **Averages only** → skewed by whales/outliers. Use percentiles.
- **Peeking at A/B tests** → false positives. Pre-register and wait.
- **PII in props** → legal risk. Hash and minimize.
- **Blocking on send** → frame hitches. Async queue with caps.

## Composition

- **Testing:** `playtest-qa` for qualitative context behind numbers.
- **LiveOps:** `liveops` for retention and event metrics.
- **Economy:** `game-economy` for sinks, conversion and inflation.
- **Performance:** `performance-optimization` for frame-time telemetry.
- **Backend:** `multiplayer-netcode` for server-side event emission.

## References

- Read `references/event-schema-funnels-and-privacy.md` for a full event catalog, funnel math,
  A/B sample-size guidance and a telemetry QA checklist.
