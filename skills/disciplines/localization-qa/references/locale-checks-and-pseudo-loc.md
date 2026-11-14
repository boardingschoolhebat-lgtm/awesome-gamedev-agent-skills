# Locale checks and pseudo-loc

Depth for `localization-qa`: ICU patterns, expansion, fonts and checklist.

## ICU examples

```text
{count, plural, =0 {No items} one {# item} other {# items}}

{gender, select, female {She} male {He} other {They}} joined.

{rank, selectordinal, one {#st} two {#nd} few {#rd} other {#th}}
```

- Always include `other`; it is the fallback.
- Exact matches with `=0` are useful for special phrasing.
- Do not translate the ICU keywords; translate the branch text.

## Expansion budget

| Locale | Typical expansion vs English |
|--------|------------------------------|
| German | +30 % |
| Finnish | +30–40 % |
| French | +15–20 % |
| Japanese | −10–20 % (but taller lines) |
| Arabic | +20 % (and RTL) |

- UI budget: +40 % width, +20 % height for body text.
- Buttons: fixed width only for short labels; otherwise auto-size.

## Font coverage

```text
Latin + accents:  àéîõü ñ ç ß
Cyrillic:         Привет
Greek:            Γειά
Arabic:           مرحبا (RTL, shaping)
Hebrew:           שלום (RTL)
CJK:              こんにちは 你好 안녕
Thai:             สวัสดี (mark stacking)
```

- Test shaping, not just presence: Arabic/Thai need proper text shaping.
- Fallback chain: primary font → locale font → system font.

## Pseudo-loc sample

```text
Source:   "Play"
Pseudo:   "[Ṗŀáý···]"
Long:     "[Ṗŀáý····························]"
```

- Brackets expose concatenation.
- Dots/tildes expose truncation.
- Accents expose missing glyphs.

## LQA checklist

1. Every screen in every locale, no English leakage.
2. Longest string per screen fits; no overlap.
3. Plurals at 0/1/2/5/11/21.
4. Dates, times, numbers, currency localized.
5. Fonts render all glyphs; no tofu.
6. RTL layout mirrored; numbers/punctuation correct.
7. Locale switch updates without restart.
8. Voiced lines match subtitles.
9. Sorting and search work per locale.
10. Error/offline strings localized too.
