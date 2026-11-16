---
name: twine-engine
description: >
  Build interactive fiction in Twine 2.12: passages and links, variables and conditionals per
  story format (Harlowe 3.3, SugarCube 2.37, Chapbook, Snowman), saves, styling, accessibility
  and HTML publishing. Use for a Twine/Twee hypertext narrative.
---

# Twine engine

Twine is an authoring tool that publishes a self-contained HTML story. Passages are nodes; links
are edges; the story format is the dialect that supplies variables, macros and UI. This is an
**engine** skill: pair it with `visual-novel` and `narrative-design`.

## When to use

- Use for a `.twee`/`.html` Twine story, or when porting a hypertext narrative to the web.
- Use when links break, variables reset, or a story format's syntax is mixed up.

**When *not* to use:** Ren'Py `.rpy` → `renpy-engine`; a dialogue system inside a game engine →
`dialogue-systems`; a fully custom web app → your web stack.

## Versions

- Twine **2.12.1** (Oct 2026). Story formats are separate and versioned:
  **Harlowe 3.3.9** (default), **SugarCube 2.37.3**, **Chapbook 2.2.0**, **Snowman 2.x**.
- **Never mix macro syntaxes.** Harlowe `(set:)` is not SugarCube `<<set>>`.
- Pick the format before writing: Harlowe for ease, SugarCube for depth/saves, Chapbook for
  simple inserts, Snowman for JavaScript-first authors.

## Story structure

```text
Start -> passage A -> passage B -> ending
             |            |
             +-> passage C +-> ending 2
```

- One passage = one beat; short passages read faster on mobile.
- Every link must resolve; broken links show as dead ends (Twine highlights them).
- Name passages by scene, not by number; use tags (`forest`, `ending`) for organization.
- Keep a `Start` passage (or the format's configured start) and avoid orphan passages.

## Links

```twine
[[Open the door]]
[[Open the door->Hallway]]
[[Hallway<-Open the door]]
[[Open the door|Hallway]]
```

- The last form shows custom text and routes to `Hallway`.
- Links can be conditional in most formats; hide or disable rather than dead-end.
- Use back-links or a "return" passage only when the fiction supports it.
- Test every link in Twine's **Test** mode and **Back** through history.

## Variables and logic

### Harlowe

```twine
(set: $gold to 5)
(if: $gold >= 5)[You can afford the sword.]
(link: "Buy")[(set: $gold to $gold - 5)(goto: "Armory")]
```

- `$` story variables, `_` temp variables; `(set:)`, `(if:)`, `(else:)`, `(print:)`, `(goto:)`.
- `(link:)` creates an inline link; `(link-goto:)` is the shorthand.

### SugarCube

```twine
:: StoryInit
<<set $gold to 5>>

:: Shop
<<if $gold >= 5>>You can afford the sword.<<else>>Too expensive.<<endif>>
<<link "Buy" "Armory">><<set $gold to $gold - 5>><</link>>
```

- `StoryInit` initializes variables once; `$` story, `_` temp.
- Macros: `<<set>>`, `<<if>>`, `<<link>>`, `<<print>>`, `<<include>>`.
- `StoryCaption`, `StoryMenu` and `PassageHeader` let you customize UI.

### Chapbook / Snowman

- Chapbook uses inserts/modifiers; check its guide for exact syntax.
- Snowman is JavaScript-first: write markup and script in passages, manage state yourself.

## Saves and history

- Harlowe/SugarCube provide session history and save APIs; SugarCube autosaves by default.
- Initialise variables in `StoryInit` (SugarCube) or at story start (Harlowe), not only in the
  first passage, or loads can miss them.
- Test: save mid-story, reload, and verify variables, visited links and inventory.
- If you need portable saves, export/import JSON and version the schema.

## Styling and media

- Twine publishes HTML/CSS: style with a story stylesheet, not inline styles everywhere.
- Images: keep them small; use `alt` text. Audio: user-initiated playback and a mute control.
- Mobile: readable line length, large tap targets, no hover-only interactions.
- Use semantic HTML and focus styles; test keyboard-only navigation.
- Custom fonts must load offline in the published file or be hosted reliably.

## Publishing

- **Publish to File** produces one HTML file; host it on itch.io, GitHub Pages or any static host.
- Twee/Tweego workflow: `tweego -o story.html story.twee` for source control and CI.
- Keep the `.twee`/`.html` source in version control; the published file is a build artifact.
- Set the story format version in `StoryData` when using Twee; do not silently upgrade formats.
- Test the published file from `file://` and over HTTP; some browsers restrict local assets.

## Accessibility

- Screen readers traverse the passage HTML: use headings, lists and meaningful link text.
- Announce passage changes with a live region if the format does not already.
- Provide text alternatives for images and captions for audio.
- Avoid timed links without an option; offer a "reduce motion" path for animations.
- Test with keyboard only and at 200 % zoom.

## Pitfalls

- **Mixed syntax** → `(set:)` in SugarCube or `<<set>>` in Harlowe does nothing. Pick one format.
- **Variables reset on load** → initialized in a passage, not `StoryInit`/start.
- **Broken link** → renamed passage. Twine marks it; fix before publishing.
- **Orphan passages** → unreachable content. Check the story map.
- **Huge passages** → walls of text. Split into beats.
- **Hover-only choices** → unusable on touch. Use links/buttons.
- **Assets missing offline** → external fonts/images. Inline or bundle them.
- **Save incompatibility** → renamed variables. Version and migrate.
- **Format auto-upgrade** → new macro behavior. Pin the format version for a release.
- **No alt text** → inaccessible images. Add descriptions.

## Composition

- **Genre:** `visual-novel` for routes, backlog, endings.
- **Narrative:** `narrative-design` for beats, branching and foldback.
- **UI:** `game-ui-ux` for readable typography and choice layout.
- **Localization:** `localization` for translated passages and text expansion.

## References

- Read `references/passages-formats-and-publishing.md` for a format comparison, passage patterns,
  save/testing recipes and a Twine checklist.
