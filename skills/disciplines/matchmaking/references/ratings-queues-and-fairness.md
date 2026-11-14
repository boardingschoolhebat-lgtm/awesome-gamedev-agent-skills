# Ratings, queues and fairness

Depth for `matchmaking`: rating math, expansion, parties and tests.

## Elo

```text
Ea = 1 / (1 + 10^((Rb - Ra)/400))
Ra' = Ra + K * (Sa - Ea)
```

- `K` 16 for established, 32 for new players.
- Team: use average rating; apply delta to each member.
- Simple but no uncertainty; new players distort pools.

## Glicko-2 outline

State per player: `r` (rating), `RD` (deviation), `σ` (volatility).

```text
1. Convert to Glicko scale (mu, phi).
2. For each result: g(phi_j), E, variance v.
3. Update phi*, then sigma' via volatility iteration.
4. Convert back; RD shrinks with games played.
```

- New player: `RD` high (e.g. 350), moves fast.
- Inactive player: `RD` grows slowly over time.
- Match quality: probability both players perform similarly, using `RD`.
- Use a library rather than hand-rolling the volatility iteration.

## Queue expansion table

| Wait | Rating window | Max ping | Notes |
|------|---------------|----------|-------|
| 0 s | ±50 | 40 ms | strict |
| 15 s | ±100 | 60 ms | |
| 30 s | ±200 | 80 ms | |
| 60 s | ±400 | 120 ms | allow backfill |
| 120 s | region-wide | 150 ms | bots optional |

- Expand rating before latency; a laggy fair match is worse than a slightly unfair fast one.
- Recompute candidates on a timer (2–5 s), not per frame.

## Party formulas

```text
party_mmr = max(avg(members), top_mmr - 100)
effective = party_mmr + party_size_bonus   # e.g. +25 per extra player
```

- Match party size against party size; if impossible, give solos the higher average.
- Never break a party to fill a match.

## Fairness metrics

| Metric | Target |
|--------|--------|
| Predicted win rate | 45–55 % |
| MMR gap (relative) | < 5 % |
| p95 queue time | < 90 s |
| Accept rate | > 90 % |
| Remake/abandon | < 5 % |
| Backfill share | < 10 % |

## Test checklist

1. New account reaches a stable rating within ~10 matches.
2. Top player cannot farm low MMR indefinitely.
3. Party of 5 does not match five solos of lower average.
4. Queue expands and eventually starts; cancel works.
5. Two regions with different populations behave sanely at off-peak.
6. Disconnect during accept returns the player to queue.
7. Backfill only before cutoff; rewards correct.
8. Season reset preserves uncertainty, not exact rank.
9. Metrics dashboards match expected distributions.
10. Rating updates are idempotent on duplicate result reports.
