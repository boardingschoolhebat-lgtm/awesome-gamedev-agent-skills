---
name: localization
description: >
  Localize a game: externalize strings into keyed tables, handle placeholders, plurals, gender and
  rich text, switch locales at runtime, fit expanded text and right-to-left scripts, localize
  fonts, audio and images, and run pseudo-localization QA. Use when a game must support more than
  one language, when UI text is hardcoded, or when translations overflow, break markup, or show
  the wrong plural. Pairs with any engine's UI and save skills.
---

# Game localization

Localization is an architecture decision, not a translation pass: every player-visible string
comes from a keyed table, formatted with locale-aware rules, and tested with pseudo-locales before
real translators touch it.

## When to use

- Use when adding a second language, extracting hardcoded strings, or fixing text that overflows,
  breaks formatting, or uses the wrong plural.
- Use when localizing store pages, subtitles, voice-over scripts or text baked into textures.

**When *not* to use:** general UI layout → `game-ui-ux`; engine UI implementation →
`unity-ui` / `unreal-ui` / `godot-ui-control` / `phaser-ui`; font asset creation →
`create-game-assets`; save-file schema → `save-systems`.

## Core workflow

1. **Externalize everything.** UI labels, dialogue, item names, tooltips, errors, subtitles,
   achievements and store text. Any string a player can see or hear is localizable.
2. **Choose stable keys.** `ui.menu.play`, `item.sword.iron.name`, `dialogue.innkeeper.greet.01`.
   Never key by the English text: editing the source string then orphans every translation.
3. **Define one source locale and a fallback chain.** Missing entries fall back to the source, and
   the UI must show something sane rather than a raw key in production.
4. **Use placeholders, never concatenation.** `"{count} coins"` with named arguments, not
   `count + " coins"`; word order differs per language.
5. **Format plurals, numbers, dates and lists with locale rules.** ICU MessageFormat or the
   engine's smart-string system; `Intl` on the web; never hand-rolled `if (n == 1)`.
6. **Plan for text expansion.** German/Russian strings can be 30–40 % longer; design flexible
   layouts, avoid fixed-width buttons, and test the longest locale.
7. **Handle scripts and fonts.** CJK, Arabic, Hebrew, Thai and Devanagari need glyph coverage,
   shaping and often a different line-break rule; RTL needs mirrored layout, not mirrored text.
8. **Localize assets.** Text in textures, voice-over, subtitles timing, videos, legal notices.
9. **Switch locale at runtime** and persist the choice with the save/settings skill.
10. **Run pseudo-localization first.** Accented characters and +40 % length expose layout bugs
    before translation starts.

## Patterns

### 1. Keyed tables, one file per feature

```json
{
  "ui.menu.play": "Play",
  "ui.menu.quit": "Quit",
  "hud.coins": "{count, plural, =0 {No coins} one {# coin} other {# coins}}",
  "dialogue.innkeeper.greet.01": "Welcome, {playerName}."
}
```

- One table per feature (`ui`, `items`, `dialogue`) keeps diffs reviewable and lets translators
  work in parallel.
- CSV or JSON both work; pick what the engine imports natively and keep it in version control.
- Comments/context columns matter: "Bark" (dog) and "Bark" (tree) translate differently.
- Keep keys stable; add new keys instead of renaming shipped ones.

### 2. Placeholder safety

```csharp
// Unity, Smart Strings / String.Format style:
var text = table.GetEntry("hud.coins").GetLocalizedString(coins);

// Bad: translators cannot reorder, and markup breaks.
var bad = coins + " " + Localize("ui.coins");
```

- Named placeholders (`{playerName}`) survive reordering; positional (`{0}`) are acceptable when
  documented.
- Escape braces that are literal text.
- Validate translated strings: every placeholder present, same set, no extra ones.

### 3. Plurals and gender

| Locale | Plural categories |
|--------|-------------------|
| English | one, other |
| French | one, many, other |
| Polish | one, few, many, other |
| Russian | one, few, many, other |
| Arabic | zero, one, two, few, many, other |
| Japanese/Chinese | other |

Use ICU categories; the engine's formatter selects the right one from the number. Gender and
formality need separate keys or select constructs (`{gender, select, female {...} other {...}}`),
not string concatenation of gendered adjectives.

### 4. Engine bindings

| Engine | Mechanism |
|--------|-----------|
| Godot | `tr("KEY")`, CSV/PO translation resources, `TranslationServer.set_locale("id")` |
| Unity | Localization package: `LocalizedString` + String Tables; `LocalizationSettings.SelectedLocale` |
| Unreal | `FText`, String Tables (`FText::FromStringTable`), `NSLOCTEXT`/`LOCTEXT`, culture via `FInternationalization` |
| Phaser / web | JSON dictionaries + `Intl` (or i18next); no built-in i18n |
| Roblox | LocalizationTables + `LocalizationService` (automatic translation) |

The Unity namespace differs between the Localization package release and the engine module in
newer Unity versions; match the `using` to the project's package/assembly rather than copying a
snippet. Unreal `FText` is the only correct type for display strings; `FString` loses localization.

### 5. Runtime locale switching

```text
1. Load the locale's tables (async on web/Unity WebGL).
2. Set the engine locale (TranslationServer, LocalizationSettings, culture).
3. Refresh every visible string from its key (or subscribe to a locale-changed event).
4. Re-layout: text length and reading direction changed.
5. Persist the choice in settings.
```

Subscribe UI to a "locale changed" event instead of rebuilding the whole scene; refresh text,
fonts and layout for the affected widgets.

### 6. Pseudo-localization

```text
"Play"  ->  "[!!! Ṕĺáý !!!]"
```

- Accent every character to catch non-ASCII rendering and font gaps.
- Add 30–40 % length to expose truncation and overflow.
- Add brackets to catch concatenation and missing keys.
- Run it in every screen, including errors, tooltips, subtitles and store UI.

## Pitfalls

- **Key is shown instead of text in production** → the entry is missing and the fallback is the
  key. Ship a source-locale table and a visible fallback, and fail CI on missing keys.
- **English text used as the key** → editing the source orphans translations. Use stable ids.
- **Placeholder lost in translation** → the translated string omits `{count}` or renames it.
  Validate placeholder sets automatically.
- **Wrong plural** → hand-written `count == 1 ? ...` instead of locale plural rules. Use ICU.
- **Text overflows in German/Russian** → fixed-size UI. Design for expansion and test the longest
  locale.
- **RTL layout broken** → only the text is mirrored; panels, icons and scroll directions are not.
  Mirror the layout and keep numbers/URLs LTR as appropriate.
- **Missing glyphs (tofu)** → the font lacks the script. Add fallback fonts and regenerate
  font atlases for TMP/SDF and bitmap fonts.
- **Dates/numbers look American everywhere** → formatting with the invariant culture. Use the
  selected locale's culture (`Intl`, `CultureInfo`, `FText` formatting).
- **Localized text baked into an image** → cannot be translated. Render it at runtime or ship
  per-locale art.
- **Subtitles out of sync** → translated audio has different timing. Retiming per locale, or keep
  voice-over in one language with localized subtitles.
- **Locale reverts after restart** → the setting was not persisted with `save-systems` /
  `unity-save` / engine settings.

## References

- Read `references/tables-and-qa.md` for table formats, placeholder validation, plural rules,
  font/RTL requirements, engine API pointers and a localization QA checklist.

## Related skills

- `game-ui-ux` — layout, readability and text hierarchy.
- `unity-ui` / `unreal-ui` / `godot-ui-control` / `phaser-ui` — the UI that displays strings.
- `save-systems` / `unity-save` / `godot-save` — persisting the selected locale.
- `create-game-assets` — fonts, iconography and text-in-art constraints.
