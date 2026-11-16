---
name: game-production
description: >
  Plan and run game production: pillars and scope, vertical slice, milestones, backlog, estimates,
  risk register, team roles, outsourcing, review cadence, content freeze, cert and launch.
  Use when scoping a project, planning milestones, or rescuing a slipping schedule.
---

# Game production

Production is the craft of finishing: choosing a scope that fits the team, proving it with a
vertical slice, and cutting in the right order when reality arrives. This is a **workflow**
skill: pair with `prototype-fast`, `playtest-qa`, `platform-cert` and `steam-publish`.

## When to use

- Use when planning a project, a milestone, a team structure or a scope cut.
- Use when the schedule slips, the team is blocked, or the game is "80 % done" forever.

**When *not* to use:** a game-jam build → `game-jam`; a quick prototype → `prototype-fast`;
store/cert execution → `steam-publish`/`platform-cert`.

## Pillars and scope

```text
3 pillars -> fantasy, verb, tension
scope = content volume x polish x platforms x team
```

- Pillars decide what to protect when cutting.
- Write the **minimum shippable game**: one loop, one progression, one ending.
- Scope in content units (levels, enemies, items), not hours.
- Every feature needs an owner, a deadline and a cut line.

## Vertical slice

- A 15–30 minute slice that looks and plays like the final game.
- Includes the core loop, one progression beat, one boss/set-piece, real UI and audio.
- Proves the fantasy and the pipeline; not a demo of disconnected features.
- Gate: if the slice is not fun, do not scale content.

## Milestones

| Milestone | Exit criteria |
|-----------|---------------|
| Prototype | core verb playable, fun validated |
| Vertical slice | final-quality 15–30 min |
| Alpha | all features in, content placeholder |
| Beta | content complete, bugs triaged |
| Content lock | no new content; polish/fix only |
| Release candidate | cert-ready, zero blockers |
| Launch | store live, build verified |

- Each milestone has a date, a demo and a go/no-go decision.
- Buffer 15–25 % per milestone; do not plan at 100 % capacity.

## Backlog and estimates

- Break work into tasks ≤3 days; anything larger is a milestone, not a task.
- Estimate in ranges (best/likely/worst); track actuals to calibrate.
- Separate **must / should / could / won't** (MoSCoW) and revisit monthly.
- Unknowns become spikes with a timebox (1–3 days), not open-ended research.
- Bugs have severity and a reproduction; a bug tracker without triage is a diary.

## Risk register

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Scope creep | high | high | cut list, change control | producer |
| Key person | medium | high | docs, pairing | lead |
| Cert failure | medium | high | early checklist | QA |
| Platform shift | low | high | abstraction layer | tech lead |

- Review risks every milestone; retire or escalate.
- The top three risks get time on the schedule, not just a document.

## Team and roles

- Core: design, programming, art, audio, QA, production.
- One **decision owner** per discipline; consensus is not a schedule.
- Outsource clear, isolated chunks (art, audio, localization, porting) with a spec and acceptance.
- Protect focus time; meetings scale with uncertainty, not headcount.
- Document decisions (ADR-style) so the team does not relitigate.

## Cadence

```text
weekly: build, playtest, bug triage
biweekly: demo, scope check, risk review
milestone: go/no-go, retrospective
```

- A playable build every week beats a status report.
- Playtests with fresh players at least monthly from the slice onward.
- Cut features at milestone boundaries, not mid-sprint.

## Cutting

Cut in this order:

1. Nice-to-have features.
2. Content volume (fewer levels/items).
3. Platforms.
4. Polish passes on secondary content.
5. Scope of the ending (last resort).

- Never cut the core loop, save reliability, accessibility basics or cert blockers.
- Announce cuts with the reason; silent cuts destroy trust.

## Content freeze and launch

- Content lock: no new content; only fixes and polish.
- Localization freeze earlier than code freeze; text expansion breaks UI.
- Cert submission with a buffer for a fail-and-resubmit cycle.
- Launch checklist: build verified on clean machines, store assets, keys, day-one patch,
  support channel, rollback plan.
- Post-launch: hotfix cadence, telemetry, community comms, sunset plan.

## Pitfalls

- **No vertical slice** → scale a fantasy that was never fun. Gate on the slice.
- **100 % capacity** → any slip is a crisis. Buffer 15–25 %.
- **Feature factory** → many half-features. Finish one loop first.
- **Silent cuts** → team distrust. Announce and explain.
- **Bug diary** → no triage. Severity + owner + repro.
- **Estimate as commitment** → sandbagging. Use ranges and actuals.
- **Outsource without acceptance** → rework. Spec + acceptance criteria.
- **Late localization** → broken UI. Freeze text early.
- **Cert at the end** → resubmit panic. Check requirements from alpha.
- **Crunch as plan** → burnout and bugs. Scope to the team, not the reverse.

## Composition

- **Prototype:** `prototype-fast` for the fun gate.
- **QA:** `playtest-qa` for cadence and triage.
- **Cert:** `platform-cert` for requirements and submission.
- **Publish:** `steam-publish` for store/build execution.
- **Architecture:** `game-architecture` for a codebase that can absorb cuts.

## References

- Read `references/milestones-risks-and-cuts.md` for a one-page plan, milestone table, risk
  register, cut ladder, cadence and a production checklist.
