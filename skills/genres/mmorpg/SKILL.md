---
name: mmorpg
description: >
  Build an MMO: sharding and zones, persistent world state, interest management, chat and
  moderation, guilds/social systems, group content, economy and content cadence. Use for a
  persistent online RPG or large shared world.
---

# MMORPG

An MMO is a persistent world plus a social graph plus an economy. The hard problems are not
combat — they are state at scale, player trust, and content cadence. This is a **compositional**
skill: pair with `multiplayer-netcode`, `game-economy`, `quest-design` and `liveops`.

## When to use

- Use when building a persistent shared world with many concurrent players, guilds and chat.
- Use when designing sharding, group content, or a player-driven economy.

**When *not* to use:** small co-op sessions → `co-op-design`; battle royale matches →
`battle-royale`; single-player RPG → `rpg`.

## Architecture

```text
login/auth -> character service -> world shard/zone -> interest grid -> clients
                     |                    |
                 inventory            chat/social
                     |                    |
                 database <---------- economy ledger
```

- **Shard**: independent copy of the world; characters are bound to a shard.
- **Zone**: spatial partition inside a shard; handoff when crossing.
- **Interest management**: only nearby entities are replicated.
- **Services**: inventory, chat, guild, auction, matchmaking as separate concerns.
- Persist via transactional writes; never trust the client for items or currency.

## World and scale

- Target concurrent users per zone, not "players" in the abstract; measure tick cost.
- Crowding: dynamic layers/instances when a zone exceeds a threshold.
- Handoff must be seamless: freeze input briefly, transfer state, resume.
- Global services (chat, auction) need their own scaling and rate limits.
- Login queues are a feature: show position and estimated wait.

## Persistence

```text
character: stats, inventory, quests, position, cooldowns
account:   unlocks, cosmetics, entitlements
world:     spawns, nodes, housing, guild bank
```

- Schema migrations are permanent; version every table.
- Inventory operations are transactions with idempotency keys.
- Backups and point-in-time recovery; test restores.
- Never delete player data on a bug; soft-delete and repair.

## Social systems

| System | Notes |
|--------|-------|
| Chat | channels, filters, rate limits, report/mute, moderation queue |
| Guild | ranks, permissions, bank logs, invites, name uniqueness |
| Friends/ignore | cross-shard presence, privacy settings |
| Group finder | roles, ilevel gates, backfill, deserter penalty |
| Mail | attachments, expiry, anti-dupe |
| Auction | listing fees, buyout, escrow, price history |

- Every social feature needs abuse handling; assume harassment.
- Log trade and guild bank actions for dispute resolution.
- Name policy and reservations; rename tokens.

## Combat and group content

- Server-authoritative damage and loot; client prediction only for movement/animations.
- Roles: tank/healer/dps; encounter design assumes them.
- Dungeons: 4–5 players, 20–40 min; raids: 8–20, scheduled.
- Loot: personal or need/greed; bad-luck protection.
- Scaling: level sync for old content; item level caps.

## Economy

- Faucets: quests, drops, vendors; sinks: repairs, fees, consumables, housing.
- Auction house is the inflation sensor; track median prices per tier.
- Bind-on-pickup/equip to limit flipping; escrow to prevent dupe laundering.
- Gold sellers: detect transfers, limit new-account trade, monitor mails.
- Server merges need economy reconciliation, not just character transfer.

## Content cadence

- Patch cadence: small updates every 2–4 weeks, major every 3–6 months.
- Horizontal progression (cosmetics, mounts, housing) between gear tiers.
- Catch-up mechanics for returning players.
- Seasonal events via `liveops`; avoid permanent power creep.

## Anti-cheat and fairness

- Server validates movement, cooldowns, loot, currency.
- Detect bots by behavior patterns; do not ban on a single signal.
- Rate-limit chat and auction; CAPTCHA or gating for suspicious accounts.
- Rollback/compensation policy for outages and dupes.

## Pitfalls

- **Single-shard ambition** → crowding and tick death. Layer/instance early.
- **Client-authoritative inventory** → dupes and RMT. Transactions + audit.
- **Chat without moderation** → harassment drives churn. Report/mute/filter from day one.
- **Guild bank without logs** → theft disputes. Log every deposit/withdrawal.
- **Auction without sinks** → inflation. Listing fees and consumable sinks.
- **Content drought** → subscription churn. Cadence and horizontal goals.
- **Server merge without economy reconciliation** → price chaos. Plan currencies and names.
- **No login queue** → thundering herd. Queue with position and ETA.
- **Backups untested** → data loss on failure. Restore drills.

## Composition

- **Netcode:** `multiplayer-netcode` for authority, interest, prediction.
- **Economy:** `game-economy` for faucets/sinks and inflation.
- **Quests:** `quest-design` for quest state and rewards.
- **LiveOps:** `liveops` for seasons and events.
- **Moderation:** `modding-and-tools` for UGC policy; `analytics` for detection signals.

## References

- Read `references/shards-social-and-economy.md` for zone/shard sizing, social tables, economy
  monitoring and an MMO test checklist.
