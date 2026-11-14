# Event schema, funnels and privacy

Depth for `analytics`: catalog, math, testing and compliance.

## Event catalog (starter)

| Event | Key props | Source |
|-------|-----------|--------|
| session_start | platform, build | client |
| session_end | duration_s, reason | client |
| tutorial_start/end | step, skipped | client |
| level_start/end | level_id, result, duration_s, deaths | server |
| quest_accept/complete/abandon | quest_id | server |
| purchase_start/complete/fail | sku, price, currency, reason | server |
| settings_change | key, value | client |
| crash | build, stack_hash | client |
| match_start/end | mode, mmr_bucket, duration_s | server |

## Funnel math

```text
step_conversion = reached[i] / reached[i-1]
overall         = reached[last] / reached[0]
```

- Report absolute counts with percentages; small cohorts mislead.
- Segment by acquisition week and platform.
- A step can exceed 100 % only with duplicate events — investigate.

## A/B sample size (rough)

```text
n per arm ~= 16 * p * (1-p) / delta^2
```

- `p` baseline rate, `delta` minimum detectable effect.
- Example: p = 0.40, delta = 0.02 → ~9,600 per arm.
- Use a calculator/library; this is only a sanity check.
- Stop when the precomputed sample is reached, not when it looks significant.

## Privacy checklist

```text
[ ] Consent/notice where required
[ ] No PII in event props
[ ] Hashed, rotating player id
[ ] Retention period defined
[ ] Opt-out honored everywhere (including crash reports)
[ ] Children's data handled per COPPA/local law
[ ] Data processing agreement with vendors
[ ] Deletion request path
```

## Telemetry QA checklist

1. Every event has name, ts, session, build, platform.
2. No duplicates on retry (idempotency key).
3. Offline events flush once on reconnect.
4. Server events match client-visible outcomes.
5. Schema validation rejects malformed props.
6. Sampling rate documented and applied consistently.
7. Dashboard totals match raw event counts.
8. Funnel steps are ordered and reachable.
9. Opt-out stops all non-essential events.
10. Debug overlay shows send failures in dev builds.
