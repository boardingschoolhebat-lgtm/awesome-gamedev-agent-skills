# Seasons, events and retention

Depth for `liveops`: templates, pass math, event checklist and metrics.

## Season template

```text
Name/theme:
Dates (UTC):            start / end / downtime
Headline feature:
Reward track:           tiers, free vs premium, theme
Events:                 week 1, mid-season, finale
Balance patch:
Store rotation:
Marketing beats:        teaser, launch, mid, finale
Success metrics:        participation, completion, retention delta
```

## Battle pass math

```text
xp_per_tier = total_season_xp / tiers
weeks = season_days / 7
xp_per_week_needed = total_season_xp / weeks
player_xp_per_week ~= sessions * xp_per_session
```

- Target completion: ~65 % of tiers for a player who plays 3–4 sessions/week.
- Soft cap weekly XP to keep late joiners viable via catch-up.
- Price the pass below the cost of buying tiers; tiers are a shortcut, not the plan.

## Event checklist

```text
[ ] Start/end in UTC; display local time
[ ] Feature flag + kill switch
[ ] Rewards defined and testable
[ ] No progression blockers if event fails
[ ] Localized strings and store assets ready
[ ] Analytics events for start, participation, completion
[ ] Support/FAQ entry
[ ] Rollback plan
```

## Retention definitions

| Metric | Definition |
|--------|------------|
| D1 | % of new players returning 1 day later |
| D7 / D30 | same, 7 / 30 days |
| Session frequency | sessions per active player per week |
| Stickiness | DAU / MAU |
| Pass completion | % of buyers reaching max tier |
| Event participation | % of DAU entering the event |

- Segment by platform, region and new vs returning.
- Compare against the previous season, not only absolute targets.

## Incident comms template

```text
We are aware of <issue> affecting <platforms> since <time UTC>.
Impact: <what players cannot do>.
Next update: <time>.
Workaround: <if any>.
```
