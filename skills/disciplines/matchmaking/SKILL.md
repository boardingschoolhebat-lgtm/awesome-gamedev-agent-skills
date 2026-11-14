---
name: matchmaking
description: >
  Build matchmaking: queues, MMR/Elo/Glicko-2 rating, party and premade handling, latency and
  region selection, queue-time expansion, backfill, placement and smurf handling. Use for online
  PvP/PvE matchmaking, fair lobbies, or queues that never pop.
---

# Matchmaking

Matchmaking turns a pool of waiting players into a match that is fair, low-latency and fast to
start. Those three goals conflict; the skill is choosing the trade-off explicitly. This is a
**compositional** skill: pair with `multiplayer-netcode` for sessions and `game-economy` for
rewards.

## When to use

- Use when implementing queues, ratings, parties, regions or backfill.
- Use when matches are unfair, queues are slow, or premades stomp solos.

**When *not* to use:** direct-IP/private lobbies only; single-player; turn-based async
matchmaking (simpler rating + pairing).

## Core model

```text
player -> queue(region, mode, party) -> candidate search -> match -> session
```

- **Rating (MMR)**: hidden skill estimate; separate from visible rank.
- **Latency**: predicted ping per candidate server/region.
- **Wait time**: grows tolerance for rating/latency mismatch.
- **Party**: rate the group, not just the best player.

## Rating systems

### Elo (1v1 baseline)

```text
expected = 1 / (1 + 10^((rb - ra) / 400))
ra' = ra + K * (score - expected)     # K ~ 16-32
```

### Glicko-2 (rating + uncertainty)

- Tracks rating `r`, deviation `RD`, volatility `σ`.
- New players have high `RD`; they move fast, then stabilize.
- Update after a rating period (e.g. a day), not every match, for stability.
- Match quality uses `RD` to widen acceptable ranges for uncertain players.

### Team games

- Use the average (or a weighted average) of team ratings for expected score.
- Apply the same delta to all members, scaled by individual performance only if you accept the
  perverse incentives (kills over objectives).
- Premades: add a penalty/bonus to effective MMR for party size.

## Queue expansion

```text
t = 0:   rating ±50,   ping < 40 ms
t = 30s: rating ±150,  ping < 80 ms
t = 60s: rating ±300,  ping < 120 ms, allow backfill
t = 120s: any rating in region (or widen region), start with bots if allowed
```

- Expand one axis at a time; latency matters more than perfect skill.
- Hard cap wait time; a stomp now beats no match.
- Show the player the estimate ("~30s") and let them cancel.

## Patterns

### 1. Candidate search

```text
for candidate in pool(region, mode):
    if abs(candidate.mmr - my.mmr) <= tolerance
       and estimate_ping(candidate) <= max_ping
       and party_compatible(candidate):
        score = w1*mmr_gap + w2*ping + w3*wait
        keep best
```

- Bucket players by rating band to avoid O(n²) scans.
- Evaluate every few seconds, not every frame.
- Prefer filling an existing lobby over creating a new one.

### 2. Party handling

- Compute party MMR: `max(avg_mmr, top_mmr - offset)` to avoid boosting.
- Match party size against party size where possible; otherwise give the solo team a small MMR
  edge.
- Never split a party; queue time is the party's trade-off.

### 3. Region and latency

- Estimate ping from historical RTT or a ping beacon.
- Prefer one region per match; cross-region only after a wait threshold.
- Do not put a 20 ms player and a 180 ms player in the same competitive match if avoidable.

### 4. Backfill

- Fill a running match only before a cutoff (first minute/round).
- Backfilled players get partial rewards and no loss protection abuse.
- Mark the match as backfilled for stats.

### 5. Placement and ranks

- New players: 5–10 placement matches with wide uncertainty, then rank.
- Visible rank derived from MMR thresholds, with soft resets per season.
- Show progress, not just a number; protect against rank anxiety with unranked modes.

### 6. Smurfs and abuse

- Require account level/phone for ranked where appropriate.
- Detect impossible performance jumps; raise `RD` instead of banning on suspicion.
- Report/avoid lists; behavior score can gate matchmaking separately from skill.

## Fairness metrics

```text
predicted win probability ~ 50 % ± 5
avg |team_mmr_diff| / avg_mmr < 5 %
p95 queue time < target (e.g. 90 s)
match abandonment < 5 %
```

- Track by mode, region, party size and hour.
- A 60/40 average is often acceptable for speed; 90/10 is not.

## Pitfalls

- **Queue never pops** → fixed tolerance and small population. Expand with wait time.
- **Premades stomp solos** → party MMR ignored. Apply party penalty and match sizes.
- **Rating inflation** → K-factor too high or no decay/reset. Use Glicko-2 and seasonal soft reset.
- **Ping ignored** → fair on paper, unplayable in practice. Weight latency heavily.
- **Backfill at the end** → joins a lost match, feels bad. Cutoff + compensation.
- **Visible MMR** → anxiety and gaming. Show rank, hide the number.
- **Placement smurfs** → fresh accounts crush lobbies. Uncertainty + account checks.
- **No cancel** → players alt-tab and miss the accept. Accept prompt with timeout.
- **Region merge without warning** → language/latency complaints. Surface the region.

## Composition

- **Sessions/netcode:** `multiplayer-netcode` for authority and reconnect.
- **Party/social:** platform friends/party APIs.
- **BR/competitive modes:** `battle-royale`, `fps-shooter`, `fighting-game`.
- **Rewards:** `game-economy` for match rewards and rank seasons.
- **Telemetry:** `playtest-qa` for queue and fairness metrics.

## References

- Read `references/ratings-queues-and-fairness.md` for Elo/Glicko-2 math, expansion tables, party
  formulas and a matchmaking test checklist.
