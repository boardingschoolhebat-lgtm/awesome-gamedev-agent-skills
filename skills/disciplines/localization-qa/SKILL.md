---
name: localization-qa
description: >
  QA localized games: string freeze and context, ICU plurals/select, pseudo-localization,
  expansion and truncation, font/glyph coverage, RTL mirroring, number/date/currency formats,
  VO and text-in-images, and per-locale bug severity. Use before shipping translations or when
  localized UI breaks.
---

# Localization QA

Translation is content plus layout plus runtime. A correct string in the wrong box, wrong plural
form or missing glyph is still a bug. This is a **compositional** skill: pair with `localization`
for architecture and `ui-architecture` for layout.

## When to use

- Use when preparing strings for translation, reviewing localized builds, or fixing overflow.
- Use when plurals, fonts, RTL or dates break in non-English locales.

**When *not* to use:** building the string-table system → `localization`; translating text
itself → a translator/LQA vendor; voice recording → audio pipeline docs.

## Pipeline

```text
author (source) -> freeze -> translate (with context) -> import -> pseudo-loc test
-> LQA per locale -> fix -> regression -> ship
```

- **String freeze**: no source changes after the cutoff; late changes cost more.
- Give translators **context**: screenshot, max length, character gender, UI location, tone.
- Never concatenate fragments; use one message with placeholders.
- Keep keys stable; renaming keys breaks translations.

## Text rules

```text
Good:  "{count, plural, =0 {No items} one {# item} other {# items}}"
Bad:   "You have " + count + " item" + (count == 1 ? "" : "s")
```

- ICU `plural`/`select`/`selectordinal` with CLDR categories (`zero/one/two/few/many/other`);
  languages differ (Arabic has six, Japanese one).
- `#` formats the number per locale.
- Placeholders: `{playerName}`, `{count}` — translators may reorder them.
- Do not put markup in translatable text unless the pipeline supports it.
- Dates/numbers/currency via locale formatters, never hand-built strings.
- Avoid text in images; if unavoidable, localize the asset.

## Layout and fonts

- Plan for **+30–40 % expansion** (German, Finnish); CJK often shorter but taller.
- Set max lengths per key and test the longest translation, not English.
- Auto-size or wrap; never clip critical text or overlap buttons.
- Font fallback per locale; verify every glyph (accents, Cyrillic, CJK, Arabic, Thai).
- Dynamic fonts: include the full character set or fallback chain.
- RTL: mirror layout (not icons like clocks/logos), flip alignment, test punctuation and
  numbers.

## Pseudo-localization

```text
[!!! Ŝéé ḿé ïñ ŧĥé ŧéšŧ !!!]      # accented + padded
```

- Accents catch missing glyphs; padding catches truncation; brackets catch concatenation.
- Run pseudo-loc on every build before real translations land.
- Include a long-string pseudo-locale (e.g. 1.4×) for layout stress.

## Runtime checks

- Locale switch without restart; cached strings refresh.
- Fallback to source language for missing keys, with a visible marker in dev builds.
- No hard-coded strings in code, animations, or achievement names.
- Plural/gender correctness at 0, 1, 2, 5, 11, 21, 101.
- Sorting/collation per locale (names, inventory).
- Input fields: IME support for CJK; no assumptions about character count.

## Engine bindings

- **Unity**: `LocalizationSettings`, `LocalizedString.GetLocalizedStringAsync`, String Tables +
  Smart Strings for plurals/variables; verify API against your package version (namespace moved
  to `Unity.Localization` in Unity 6.7 docs).
- **Godot**: `tr("KEY")`, CSV/PO import, `TranslationServer.set_locale()`; test RTL with
  `TextServer`.
- **Unreal**: `FText`, String Tables, culture-aware `FText::Format`; never `FString` for UI.
- **Web/Phaser/Pixi**: keyed JSON + `Intl.NumberFormat`/`Intl.PluralRules`.

## LQA bug severity

| Severity | Example |
|----------|---------|
| Critical | wrong language shown, unreadable text, broken layout blocking play |
| Major | mistranslation changing meaning, missing glyphs, clipped critical text |
| Minor | awkward phrasing, inconsistent terminology |
| Cosmetic | spacing, punctuation style |

- Log locale, key, screenshot, expected/actual.
- Track terminology glossary compliance.

## Test matrix

```text
locales: source, pseudo-loc, longest-expansion, RTL, CJK
screens: main menu, HUD, dialogue, inventory, settings, store, errors, achievements
states: 0/1/many counts, long names, max numbers, offline errors
```

## Pitfalls

- **Concatenation** → untranslatable grammar. Use full messages with placeholders.
- **English-length layouts** → clipped buttons. Pseudo-loc + expansion budget.
- **Missing glyphs** → tofu boxes. Font fallback and full charset.
- **Plural bugs** → only `one/other`. Use CLDR categories.
- **Hard-coded strings** → mixed-language UI. Key everything.
- **RTL mirroring icons** → backwards arrows/logos. Mirror layout, not symbols.
- **Late string changes** → stale translations. Freeze and re-import.
- **No context** → wrong tone/gender. Provide screenshots and notes.
- **Locale switch needs restart** → poor UX. Refresh bound strings.

## Composition

- **Architecture:** `localization` for tables, keys, runtime switching.
- **Layout:** `ui-architecture` for expansion-safe screens.
- **Accessibility:** `accessibility`, `accessibility-testing` for captions/fonts.
- **QA:** `playtest-qa` for build verification.

## References

- Read `references/locale-checks-and-pseudo-loc.md` for ICU examples, expansion budgets, font
  coverage and an LQA checklist.
