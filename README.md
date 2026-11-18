# font-book

Install downloaded fonts into macOS Font Book, check that they open, and remove duplicate faces.

Two Cursor skills live in `.cursor/skills/`. Open this folder in Cursor and both are available in the project. To use them in every project, copy `validate-fonts` and `dedupe-fonts` into your personal skills folder.

## Setup

```bash
pip install -r requirements.txt
```

macOS, with Font Book and the Swift command-line tools.

## Install and validate a download

```bash
python3 scripts/install_fonts.py /path/to/downloaded/fonts
```

New `.ttf`, `.otf`, `.ttc`, and `.otc` files are copied into `~/Library/Fonts`. Files already installed are skipped. Web fonts (`.woff`, `.woff2`) stay in the download folder. Each new file is checked, then duplicate faces are removed.

## Remove duplicates only

```bash
python3 scripts/dedupe_fonts.py
```

Keeps one file when the same face is installed twice: a byte-for-byte copy, a static cut that repeats a variable font’s default instance, or both an OpenType and a TrueType of the same face. The download folder is never deleted.
