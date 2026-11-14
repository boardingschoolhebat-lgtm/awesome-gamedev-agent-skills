# Cert plan and failure triage

Depth for `platform-cert`: timeline, log template, checklist.

## Timeline (relative to submission)

```text
T-8 weeks   fetch requirements, map owners, book devkits
T-6 weeks   feature complete; start requirement tests
T-4 weeks   mock cert pass; fix blockers
T-2 weeks   content/rating freeze; store metadata
T-1 week    final build, smoke test, submission package
T-0         submit; triage window opens
T+1..2 wk   fixes + resubmission if needed
```

## Failure log

```text
Requirement:  <id + title from the current doc>
Platform:     Xbox / PlayStation / Nintendo, doc version
Severity:     <platform class>
Test case:    <id or steps>
Repro:        1) ... 2) ... 3) ...
Expected:
Actual:
Evidence:     video/log/save
Fix:          commit + build id
Status:       open / fixed / verified
```

- One row per failure; group by category for trend analysis.
- Track resubmission count and time-to-fix.

## Pre-submission checklist

```text
[ ] Requirements doc versions recorded; all clauses mapped
[ ] No dev menus, debug text, test entitlements
[ ] Boot, suspend/resume, user switch, storage full
[ ] Sign-in, privacy, parental controls, child account
[ ] Offline behavior for online features
[ ] Achievements/trophies unlock and persist offline
[ ] Store metadata, ratings, privacy policy correct per region
[ ] Patch path from the previous certified build tested
[ ] Localization for all system languages shipped
[ ] Accessibility platform requirements verified
[ ] Crash logs and build id present
[ ] Submission package matches the tested build hash
```

## Rating notes

- IARC for digital storefronts; ESRB/PEGI boards for physical.
- Disclose simulated gambling, UGC, purchases, online interactivity.
- Re-rate DLC/patches that add stronger content.
