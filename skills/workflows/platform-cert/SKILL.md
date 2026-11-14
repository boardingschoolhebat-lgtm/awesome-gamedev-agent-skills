---
name: platform-cert
description: >
  Plan console/platform certification: submission stages, requirement categories, test benches,
  age ratings (IARC/ESRB/PEGI), store metadata, day-one patches and failure triage. Use before a
  console submission or when a cert failure blocks release.
---

# Platform certification

Certification is a gate with published rules and private details. You cannot memorize it: fetch
the current requirements document for each platform from its developer portal. This workflow
turns that document into a plan, a smoke test and a triage loop.

## When to use

- Use when preparing a PlayStation, Xbox or Nintendo submission, or a major patch.
- Use when a cert failure needs triage or a submission date is at risk.

**When *not* to use:** PC-only store pages → `steam-publish` / `itch-publish`; age rating
questionnaire alone → the rating body's own tool.

## What is public vs gated

| Platform | Regime | Availability |
|----------|--------|--------------|
| Xbox | Xbox Requirements (XR) | public (Microsoft Learn) |
| PlayStation | TRC (Technical Requirements Checklist) | gated (DevNet) |
| Nintendo | Lotcheck submission guidelines | gated (developer portal) |

- **Never invent requirement numbers.** Quote the document version you are testing against.
- TRC/Lotcheck contents are under NDA: do not paste them into public docs or AI prompts you do
  not control.
- Platform holders publish severity vocabularies (e.g. Xbox uses CFR/SRI/ION classes); confirm
  current names and SLAs in the portal.

## Plan

```text
1. Pick target platforms and regions.
2. Fetch current requirements + test cases; record versions.
3. Map each requirement to an owner and a test.
4. Build a cert test bench (devkits, accounts, network conditions).
5. Run a mock cert pass 4-6 weeks before submission.
6. Freeze, submit, triage failures, resubmit.
```

- Requirements change; re-fetch at the start of every milestone.
- Regions change age ratings and sometimes content (e.g. gambling presentation).
- Budget at least one resubmission cycle in the schedule.

## Requirement categories (common shape)

```text
base/system:     boot, suspend/resume, storage, user switching
accounts/PRIV:   profiles, sign-in, privacy, parental controls
commerce:        store, entitlements, refunds, currency display
online:          sessions, matchmaking, voice, cross-play, safety
achievements:    unlock, progress, offline behavior
updates/DLC:     patching, versioning, entitlements
accessibility:   platform-level requirements
localization:    system language, region formats
```

- The exact clauses differ per platform; the categories are a checklist skeleton, not a
  substitute for the document.

## Test bench

- Retail/devkit hardware for each target, plus the minimum storage scenario.
- Clean accounts per region; child/parent accounts for privacy tests.
- Constrained network: offline, high latency, packet loss, NAT types.
- Multiple users signed in, controller disconnect, suspend/resume mid-match.
- A build with no dev menus, debug output, or test entitlements.

## Age ratings

- **Digital**: IARC questionnaire generates region-specific ratings (ESRB, PEGI, USK, CERO,
  ClassInd, etc.).
- **Physical**: ESRB/PEGI boards review a content questionnaire and gameplay video.
- Disclose violence, language, sexual content, drugs, gambling (including simulated), and
  interactive elements (in-app purchases, user-generated content, online interactivity).
- DLC with a higher rating than the base game needs its own rating.
- Misrepresenting content can pull the store listing.

## Store metadata and compliance

- Accurate screenshots/gameplay; no fake UI.
- Privacy policy URL, support contact, EULA.
- Required localized store text per region.
- Correct entitlement and cross-buy behavior.
- Age gate where required.

## Submission flow

```text
pre-check (internal) -> submission checks -> BVT/technical test -> cert test -> pass/fail
```

- Fix failures with the smallest change; large changes restart risk.
- Keep a failure log: requirement id, test case, severity, repro, fix, evidence.
- Day-one patch: submit it alongside the base build; it must also pass cert.
- Do not ship a patch that changes content rating without re-rating.

## Pitfalls

- **Testing against an old requirements doc** → avoidable failures. Re-fetch each milestone.
- **No mock cert** → failures at the worst time. Run one 4–6 weeks out.
- **Dev-only code in the build** → instant fail. Strip menus, logs, cheats.
- **Ignoring suspend/resume** → common failure. Test mid-save, mid-match, mid-cutscene.
- **Rating mismatch** → store pulled. Keep the questionnaire current with content.
- **No resubmission budget** → missed launch. Plan two cycles.
- **Publishing NDA details** → contractual risk. Keep TRC/Lotcheck internal.
- **Patch untested on the certified base** → patch cert fails. Test upgrade paths.

## Composition

- **QA:** `playtest-qa` for the smoke test and bug triage.
- **Builds:** `steam-publish` for PC packaging parallels; `editor-tooling` for build scripts.
- **Localization:** `localization-qa` for system-language and region checks.
- **Accessibility:** `accessibility-testing` for platform-level requirements.
- **LiveOps:** `liveops` for patch cadence around cert windows.

## References

- Read `references/cert-plan-and-failure-triage.md` for a submission timeline, failure log
  template and a pre-submission checklist.
