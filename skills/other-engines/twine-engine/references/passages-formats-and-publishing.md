# Passages, formats and publishing

Depth for `twine-engine`: format choice, patterns, tests.

## Format comparison

| Format | Strength | Watch out |
|--------|----------|-----------|
| Harlowe 3.3 | default, readable macros | fewer advanced APIs |
| SugarCube 2.37 | saves, UI, macros, JS | more concepts to learn |
| Chapbook 2.2 | simple inserts/modifiers | smaller ecosystem |
| Snowman 2.x | JavaScript-first | you build state/UI |

- Changing format later is a rewrite; choose first.
- Record the format and version in the project README.

## Passage patterns

```twine
:: Start
You wake in a cell. [[Listen]] or [[Pull the chain]].

:: Listen
(if: $heard_guard)[You already know the patrol.]
(else:)[(set: $heard_guard to true)Boots, then silence.]
[[Back->Start]]

:: Pull the chain
The chain gives. [[Escape->Courtyard]]
```

- Keep state changes next to the choice that causes them.
- A "return" link is a loop; make it change something or cut it.

## State schema

```text
$gold, $inventory (array), $flags (map), $visited (set)
```

- Initialize every variable in one place.
- Avoid storing derived values (health max) that can drift; compute them.
- Version saves if the schema changes.

## Test script

1. Walk every branch; check no dead ends except intended endings.
2. Save mid-branch, reload, verify variables and inventory.
3. Use browser Back/Forward and the format's history controls.
4. Keyboard-only: tab to every link, activate with Enter.
5. 200 % zoom on a phone-sized viewport.
6. Open the published HTML from disk and over HTTP.
7. Screen reader: headings, link text and passage announcements.

## Checklist

1. One story format, pinned version, no mixed syntax.
2. Every passage reachable; every link resolves.
3. Variables initialized in `StoryInit`/start.
4. Saves round-trip mid-story.
5. Images have alt text; audio is user-initiated and mutable.
6. Keyboard and screen-reader navigation work.
7. Passage text fits mobile; no hover-only choices.
8. Published HTML works offline and from a static host.
9. Source (`.twee`) is in version control, build output is not.
10. Format upgrade is deliberate and tested.
