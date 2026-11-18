---
name: validate-fonts
description: Install new desktop fonts from a download folder into macOS Font Book, validate them with fontTools and Core Text, and remove duplicate faces. Use when the user adds, downloads, or drops fonts, or asks to install or validate fonts in Font Book.
---

# Validate fonts

Installed copies live in `~/Library/Fonts`. That is the library Font Book shows for the current user.

## Run

From this repo:

```bash
python3 scripts/install_fonts.py /path/to/downloaded/fonts
```

Requires `fonttools` (`pip install -r requirements.txt`) and the Swift toolchain (`swift`).

## What the script does

1. Hash desktop fonts (`.ttf`, `.otf`, `.ttc`, `.otc`) in the download folder and in `~/Library/Fonts`.
2. Copy any file whose bytes are not already installed. Clear the quarantine attribute on the copy.
3. Validate each new file with fontTools (checksums, `name`/`cmap`/`head`, glyph order). Leave a file uninstalled if it does not open.
4. Skip `.woff` and `.woff2`. Font Book does not install web fonts.
5. Run the duplicate cleanup in `scripts/dedupe_fonts.py`.
6. Ask Core Text to open every file in `~/Library/Fonts`.

Do not delete anything in the download folder. A read from an iCloud folder can stall; the script times out that one file and continues.

## Report

Say how many files were already installed, how many were copied, how many failed validation, how many duplicates were removed, and the Core Text unreadable count. Name web fonts that were skipped. If a PostScript name is broken, say so and leave that file in place.
