# Shards, social and economy

Depth for `mmorpg`: sizing, social operations, economy monitoring and tests.

## Zone sizing

```text
tick_budget_ms = 33 (30 Hz) or 16.6 (60 Hz)
entities_per_zone = players + npcs + projectiles
cost ~= base + k * entities^1.2
```

- Measure with bots; do not guess. Add layers before the tick exceeds ~70 % budget.
- Interest grid cell ~20–40 m; replicate nearby cells only.
- Handoff: serialize character, transfer, resume with a short input freeze.

## Social tables

```text
guild(id, name, leader, created_at, bank_log[])
guild_member(guild_id, player_id, rank, joined_at)
chat_message(id, channel, sender, ts, text, flags)
report(id, reporter, target, reason, evidence, status)
auction_listing(id, seller, item, price, expires_at, status)
```

- Every table with player-facing actions has an audit trail.
- Rate limits per account and per channel; escalate repeat offenders.

## Economy monitoring

| Signal | Action |
|--------|--------|
| Median auction price +20 %/week | add sink or reduce faucet |
| New-account trade volume spike | RMT review |
| Duplicate item ids | dupe detection, rollback |
| Gold per player percentile | tune drops, not bans |
| Auction listing churn | fee tuning |

## Test checklist

1. Login queue shows position/ETA and drains correctly.
2. Zone handoff preserves position, buffs, cooldowns.
3. Layer switch does not duplicate loot or mobs.
4. Inventory transaction survives disconnect mid-trade.
5. Guild bank logs every action and blocks unauthorized ranks.
6. Chat report/mute works cross-shard.
7. Auction escrow prevents item/currency loss.
8. Restore from backup reproduces the world within an acceptable window.
9. Group finder backfills and enforces deserter penalty.
10. Server merge preserves names (or grants rename tokens) and currency totals.
