---
name: liveops
description: >
  Run live operations: season cadence, battle-pass and reward tracks, limited events, daily/
  weekly retention loops, content calendar, patch notes, and sunsetting. Use for a games-as-a-
  service roadmap, seasonal content, or events that keep players returning.
---

# LiveOps

LiveOps is the operating rhythm of a game after launch: what changes, when, and why players come
back. Content alone is not a plan — cadence, rewards and communication are. This is a
**compositional** skill: pair with `game-economy`, `analytics` and `playtest-qa`.

## When to use

- Use when planning seasons, battle passes, events, login rewards or a content calendar.
- Use when retention drops between content drops.

**When *not* to use:** a finished premium game with no post-launch content; a jam build; pure
store setup → `steam-publish`.

## The operating loop

```text
measure -> decide -> produce -> ship -> communicate -> measure
```

- Every season has a theme, a headline feature, a reward track and a date.
- Ship smaller beats between major drops (events, balance patches, cosmetics).
- Never ship a season without instrumentation to judge it.

## Cadence

| Cadence | Content | Purpose |
|---------|---------|---------|
| Weekly | challenges, shop rotation | habit |
| Bi-weekly | limited event, balance patch | variety |
| 6–10 weeks | season + battle pass | major goal |
| Quarterly | expansion/major mode | re-engagement |

- Pick a cadence you can sustain for a year; missed seasons hurt more than small ones.
- Overlap production: season N+1 content is built while N runs.
- Leave buffer for cert/platform review.

## Battle pass

```text
tiers 1..N, XP per tier, free track + premium track
weekly XP cap (soft), catch-up at season end
premium price fixed; no pay-to-progress beyond the pass
```

- Free track must contain meaningful rewards, not just currency.
- Time-to-complete: ~60–75 % of season length for a regular player.
- Catch-up: double XP weekends or retroactive claims; never make late joiners hopeless.
- Show progress clearly; no hidden XP caps.
- Avoid FOMO overload: items can return, or state clearly they will not.

## Events

- Event types: login streak, community goal, limited mode, themed shop, boss raid.
- One mechanic twist, well tested; do not stack three new systems.
- Rewards exclusive to the event but not power-critical.
- Start/end times in UTC, visible in-game with a countdown.
- Have a rollback/kill switch for broken events.

## Retention loops

```text
daily: login reward, 3 dailies, shop refresh
weekly: weekly quests, raid reset, leaderboard
seasonal: pass, rank reset, major content
```

- Rewards should respect the player's time; 20–40 minutes covers dailies.
- Streak systems need forgiveness (one missed day) or they cause churn.
- Avoid punishing absence so hard that returning feels impossible.

## Communication

- Patch notes: changes, reasons, known issues, and player-facing impact.
- Roadmap: honest dates or "when it's ready"; update when plans change.
- Incident comms: acknowledge, estimate, fix, post-mortem for major outages.
- Localize announcements for major regions; keep a canonical source.

## Metrics that matter

- D1/D7/D30 retention, season pass completion, event participation.
- Session frequency and session length; time-to-first-reward for new players.
- Conversion and refund rate; support ticket volume by topic.
- Content consumption: how many players see the new content.

## Sunsetting

- Announce early; stop selling passes when content stops.
- Keep servers or offline mode viable; refund policy per platform.
- Preserve saves/export where possible; thank the community.

## Pitfalls

- **Content treadmill** → team burns out, seasons slip. Scope to cadence, reuse systems.
- **FOMO fatigue** → players quit to avoid missing out. Bring items back or reduce exclusives.
- **Battle pass too grindy** → completion under 30 %. Tune XP and catch-up.
- **Event breaks the game** → no kill switch. Feature-flag events.
- **No measurement** → cannot tell what worked. Instrument before shipping.
- **Balance patch surprises** → communicate changes and compensate where needed.
- **Season reset backlash** → explain what resets, preserve cosmetics.
- **Timezone bugs** → event ends early/late. Store UTC and show local time.

## Composition

- **Economy:** `game-economy` for pass value, shop pricing, inflation.
- **Analytics:** `analytics` for retention and event funnels.
- **QA:** `playtest-qa` for event smoke tests.
- **Publishing:** `steam-publish`/`itch-publish` for build cadence.
- **Moderation/UGC:** `modding-and-tools` when events feature community content.

## References

- Read `references/seasons-events-and-retention.md` for a season template, pass math, event
  checklist and live-ops metrics definitions.
