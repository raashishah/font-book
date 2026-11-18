#!/usr/bin/env python3
"""Remove duplicate faces from the macOS user font library (~/Library/Fonts).

Font Book shows that folder. This does not delete files in any download folder.

Keeps one file per PostScript name:
- exact byte duplicates: the shorter filename
- a variable font and a static file with the same name: the variable font
- the same face as both .otf and .ttf: the .otf
- any leftover pair: the shorter filename

Faces with a broken PostScript name (empty, one character, or the literal
word "false") are left in place. Those are bad name tables, not copies.
"""

import hashlib
import os
import sys
from collections import defaultdict

from fontTools.ttLib import TTFont

DESKTOP = {".ttf", ".otf"}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def face(path):
    font = TTFont(path, lazy=True, checkChecksums=0)
    name = ""
    for record in font["name"].names:
        if record.nameID == 6:
            try:
                name = record.toUnicode().strip()
                break
            except Exception:
                pass
    variable = "fvar" in font
    font.close()
    return name, variable


def usable_name(name):
    return bool(name) and name.lower() != "false" and len(name) >= 2 and name.isprintable()


def library_files(dest):
    found = []
    for name in os.listdir(dest):
        if os.path.splitext(name)[1].lower() not in DESKTOP:
            continue
        path = os.path.join(dest, name)
        if os.path.isfile(path):
            found.append(path)
    return found


def remove(path, removed, reason):
    os.remove(path)
    removed.append((os.path.basename(path), reason))


def dedupe(dest):
    files = library_files(dest)
    removed = []

    by_hash = defaultdict(list)
    for path in files:
        by_hash[sha256(path)].append(path)
    for group in by_hash.values():
        if len(group) < 2:
            continue
        group.sort(key=lambda path: (len(os.path.basename(path)), os.path.basename(path)))
        for extra in group[1:]:
            remove(extra, removed, "same bytes as " + os.path.basename(group[0]))

    by_name = defaultdict(list)
    for path in library_files(dest):
        name, variable = face(path)
        if not usable_name(name):
            continue
        by_name[name].append((path, variable))

    for name, items in by_name.items():
        if len(items) < 2:
            continue
        variables = [path for path, variable in items if variable]
        statics = [path for path, variable in items if not variable]
        if variables:
            for path in statics:
                remove(path, removed, "already in variable font " + name)
            continue
        otf = [path for path in statics if path.lower().endswith(".otf")]
        ttf = [path for path in statics if path.lower().endswith(".ttf")]
        if otf and ttf:
            for path in ttf:
                remove(path, removed, "OpenType copy kept for " + name)
            statics = otf
        if len(statics) > 1:
            statics.sort(key=lambda path: (len(os.path.basename(path)), os.path.basename(path)))
            for extra in statics[1:]:
                remove(extra, removed, "kept " + os.path.basename(statics[0]))

    print(f"deduped {len(removed)}")
    for filename, reason in removed:
        print(f"removed {filename} ({reason})")
    return len(removed)


def main():
    dest = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/Library/Fonts")
    if not os.path.isdir(dest):
        print("missing font library", dest, file=sys.stderr)
        return 1
    dedupe(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
