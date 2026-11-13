# Tables, formatting and localization QA

Depth for `localization`: table shapes, validation rules, plural data and the checklist that keeps
a shipped game coherent in every language.

## Table formats

| Format | Strengths | Watch out |
|--------|-----------|-----------|
| CSV | Translators know it; engine imports (Godot, Unity) | quoting/commas, encoding, merge conflicts |
| JSON | nested keys, easy tooling | no comments in strict JSON |
| PO / gettext | translator tools, context/comments | engine support varies |
| XLIFF | professional TMS exchange | tooling overhead |
| String Tables (Unreal) | engine-native `FText` | assets, not plain text diffs |

Minimum columns: key, source text, translation, context/comment, status. Add a screenshot or max
length column when the UI is tight.

## Key conventions

```text
<area>.<screen>.<element>            ui.settings.audio.master
<area>.<entity>.<field>              item.potion.health.description
dialogue.<npc>.<scene>.<line>        dialogue.innkeeper.greet.01
error.<system>.<code>                error.network.timeout
```

- Lowercase, dot-separated, ASCII only.
- Never reuse a key for different meanings; "Close" (verb) and "Close" (near) are different keys.
- Keep the source locale in the same table with a `source` column, or one table per locale.
- Mark obsolete keys instead of deleting them immediately; translators may still reference them.

## Placeholder validation

```text
source:      "You have {count} coins and {gems} gems."
translation: "Du hast {gems} Edelsteine und {count} Münzen."
```

Checks to automate in CI:

1. Same placeholder set in source and translation.
2. No stray `{`/`}` and no duplicated placeholder.
3. ICU plural/select syntax parses.
4. No leading/trailing whitespace mismatch that breaks layout.
5. Markup tags balanced (`<b>`, `<color=...>`).
6. No newline count explosion that breaks fixed-height labels.

## Plural and select rules

```text
{count, plural,
  =0 {No coins}
  one {# coin}
  other {# coins}}
```

```text
{gender, select,
  female {She}
  male {He}
  other {They}}
```

- The formatter picks the category from the locale's CLDR rules; you supply the branches.
- Do not translate the category names (`one`, `other`) — only the branch text.
- Ordinals (`1st`, `2nd`) need `{n, selectordinal, ...}` or engine equivalent.
- Lists ("A, B and C") use locale list formatting (`Intl.ListFormat`, ICU `{0, list}`).

## Numbers, dates and currency

| Data | Correct tool |
|------|--------------|
| Decimal/thousands separators | locale number formatting (`Intl.NumberFormat`, `CultureInfo`, `FText`) |
| Currency | locale currency format, not a hardcoded symbol |
| Dates/times | locale date format; store UTC, display local |
| Relative time | "2 hours ago" via locale rules |
| Units | convert + localize the unit name; avoid "km/h" in languages that use different conventions |

Never format with the invariant culture unless the value is machine-readable (save files, logs).

## Fonts and scripts

- Latin/Cyrillic/Greek: usually one font covers it.
- CJK: large glyph sets; prefer system/fallback fonts or subset atlases per language.
- Arabic/Hebrew: right-to-left, cursive shaping; the font needs the shaping tables.
- Thai/Devanagari: complex shaping and different line-break rules.
- TMP/SDF atlases must be regenerated per language or use dynamic SDF.
- Bitmap fonts need per-language atlases; budget texture memory.
- Test at the smallest and largest font sizes shipped.

## RTL checklist

1. Layout mirrored: navigation, panels, icons with direction, sliders, progress bars.
2. Text alignment right; numbers, URLs, code and timestamps stay LTR where appropriate.
3. Punctuation and parentheses mirror correctly.
4. Icons with inherent direction (arrows, "next") mirror; logos and real-world objects do not.
5. Scrollbars and paging direction.
6. Animations that slide "forward" reverse.

## Engine API pointers

| Engine | Read | Switch | Notes |
|--------|------|--------|-------|
| Godot | `tr("KEY")` | `TranslationServer.set_locale("id")` | CSV/PO imported as `Translation` resources |
| Unity | `LocalizedString.GetLocalizedString()`, `StringTable.GetEntry(key)` | `LocalizationSettings.SelectedLocale` | async loading on WebGL; subscribe to `StringChanged` |
| Unreal | `FText::FromStringTable("/Game/UI/ST_UI", "KEY")` | `FInternationalization::Get().SetCurrentCulture("id")` | `FString` is not localized; `FText` is |
| Phaser/web | dictionary lookup / i18next | `i18next.changeLanguage("id")` | use `Intl` for numbers/dates/plurals |
| Roblox | `LocalizationService` + LocalizationTables | automatic per player locale | test with Studio's locale setting |

## QA checklist

1. Pseudo-locale pass: accents render, +40 % text fits, keys never visible.
2. Every screen in the longest locale: buttons, tooltips, errors, subtitles, store page.
3. Placeholders: counts, names, item stats, dates all appear correctly.
4. Plurals: 0, 1, 2, 5, 11, 21, 100 in each language (Arabic especially).
5. Gender/formal variants render the intended branch.
6. RTL: full playthrough of menus and HUD with mirrored layout.
7. Fonts: no tofu in any shipped language; fallback works for player names.
8. Assets: textures with text, voice-over, videos, legal notices per locale.
9. Locale switch at runtime refreshes UI without a restart; setting persists.
10. Fallback: delete a translation and confirm the source text appears, not a crash.
