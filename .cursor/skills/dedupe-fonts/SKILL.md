---
name: dedupe-fonts
description: Remove duplicate font faces from macOS Font Book's user library. Use when the user asks to check, clean, or remove duplicate fonts in Font Book, or after installing a folder that contains both variable and static cuts.
---

# Dedupe fonts

Font Book's user library is `~/Library/Fonts`. Cleanup only touches that folder.

## Run

From this repo:

```bash
python3 scripts/dedupe_fonts.py
```

Pass another library path only when the user names one. Requires `fonttools`.

## What it removes

One file stays for each PostScript name.

- Exact byte duplicates: keep the shorter filename.
- A static file whose PostScript name is already the default instance of a variable font: keep the variable font. Other static weights stay.
- The same face as both `.otf` and `.ttf`: keep the OpenType file.
- Any leftover pair of the same face: keep the shorter filename.

Leave faces whose PostScript name is missing, a single character, or the literal word `false`. Those are broken name tables, not duplicate files.

## Report

List how many files were removed and the rule that removed each one. Say which broken-name families were left in place.
