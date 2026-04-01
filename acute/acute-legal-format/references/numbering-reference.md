# Template Numbering Reference

The template uses **abstractNum 8** linked via **numId 37** to drive all automatic numbering in legal documents.

Read this file when you need the exact XML for numbering overrides or when debugging numbering issues.

## Multi-Level List Structure

| Level (ilvl) | Style | Format | Pattern | Example |
|---|---|---|---|---|
| 0 | ARTICLE | decimal | `ARTICLE %1` | ARTICLE 1 |
| 1 | SECTIONHEADING / Section101Heading | decimalZero | `%1.%2` | 1.01, 1.02 |
| 2 | aText | lowerLetter | `(%3)` | (a), (b), (c) |
| 3 | iText | lowerRoman | `(%4)` | (i), (ii), (iii) |

## Key XML Snippets

### To suppress numbering on a paragraph (e.g., ARTICLE title)

```xml
<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>
```

### To reference a specific numbering level

```xml
<!-- Level 0 (ARTICLE) — usually inherited from style, no explicit numPr needed -->
<w:pPr><w:pStyle w:val="ARTICLE"/></w:pPr>

<!-- Level 1 (Section) — usually inherited from style -->
<w:pPr><w:pStyle w:val="SECTIONHEADING"/></w:pPr>

<!-- Level 2 (a-text) — usually inherited from style -->
<w:pPr><w:pStyle w:val="aText"/></w:pPr>

<!-- Level 3 (i-text) — usually inherited from style -->
<w:pPr><w:pStyle w:val="iText"/></w:pPr>
```

### AbstractNum 8 Level Definitions (from template)

**Level 0 — ARTICLE**
- numFmt: decimal
- lvlText: `ARTICLE %1`
- suff: nothing (no tab/space after number)
- jc: center
- pStyle: ARTICLE

**Level 1 — Section**
- numFmt: decimalZero (produces 01, 02, etc.)
- lvlText: `%1.%2` (produces 1.01, 2.03, etc.)
- suff: tab
- jc: left
- ind: left=720, hanging=720
- pStyle: Section101Heading

**Level 2 — (a) text**
- numFmt: lowerLetter
- lvlText: `(%3)`
- suff: tab
- jc: left
- ind: left=1440, hanging=720
- pStyle: aText

**Level 3 — (i) text**
- numFmt: lowerRoman
- lvlText: `(%4)`
- suff: tab
- jc: left
- ind: left=2160, hanging=720
- pStyle: iText

## Notes

- The numbering chain resets at each new article (level 0 restart)
- Section numbers within an article increment: 1.01, 1.02, ... 2.01, 2.02, etc.
- Letter items (a), (b), (c) restart at each new section
- Roman items (i), (ii), (iii) restart at each new letter item
- **numId 37** is the instance that links to abstractNum 8. Always use numId 37 in paragraph numbering references.
