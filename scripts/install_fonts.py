#!/usr/bin/env python3
"""Install desktop fonts into Font Book, validate them, then remove duplicate faces.

Usage:
    python3 scripts/install_fonts.py /path/to/downloaded/fonts

Copies .ttf, .otf, .ttc, and .otc files that are not already in ~/Library/Fonts.
Skips .woff and .woff2. Does not delete anything in the download folder.
"""

import hashlib
import os
import shutil
import signal
import subprocess
import sys
from collections import defaultdict

from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dedupe_fonts import dedupe

DESKTOP = {".ttf", ".otf", ".ttc", ".otc"}
WEB = {".woff", ".woff2"}


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout()


signal.signal(signal.SIGALRM, _alarm)


def sha256(path, seconds=25):
    digest = hashlib.sha256()
    signal.alarm(seconds)
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    finally:
        signal.alarm(0)
    return digest.hexdigest()


def validate(path):
    notes = []
    signal.alarm(30)
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext in {".ttc", ".otc"}:
            from fontTools.ttLib import TTCollection

            collection = TTCollection(path)
            return notes, f"collection {len(collection.fonts)}"
        try:
            font = TTFont(path, checkChecksums=2, lazy=True, recalcBBoxes=False, recalcTimestamp=False)
        except Exception as error:
            if "checksum" in str(error).lower():
                notes.append("checksum")
                font = TTFont(path, checkChecksums=0, lazy=True, recalcBBoxes=False, recalcTimestamp=False)
            else:
                raise
        for table in ("name", "cmap", "head"):
            if table not in font:
                notes.append("missing " + table)
        font.getGlyphOrder()
        font.close()
        return notes, ""
    finally:
        signal.alarm(0)


def install_missing(root, dest):
    installed = {}
    for name in os.listdir(dest):
        path = os.path.join(dest, name)
        if os.path.splitext(name)[1].lower() in DESKTOP and os.path.isfile(path):
            installed[sha256(path, 30)] = path

    sources = []
    web = 0
    for dirpath, _, files in os.walk(root):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            path = os.path.join(dirpath, name)
            if ext in DESKTOP:
                sources.append(path)
            elif ext in WEB:
                web += 1

    by_hash = defaultdict(list)
    timeouts = []
    for path in sources:
        try:
            by_hash[sha256(path)].append(path)
        except Timeout:
            timeouts.append(path)
            print("TIMEOUT", path, flush=True)

    used = set(os.listdir(dest))
    copied = bad = warns = 0
    for digest, paths in by_hash.items():
        if digest in installed:
            continue
        src = paths[0]
        base = os.path.basename(src)
        name = base
        if name in used:
            parent = os.path.basename(os.path.dirname(src)).replace(" ", "_")
            stem, ext = os.path.splitext(base)
            name = f"{stem}__{parent}{ext}"
            n = 2
            while name in used:
                name = f"{stem}__{parent}_{n}{ext}"
                n += 1
        target = os.path.join(dest, name)
        try:
            signal.alarm(25)
            try:
                shutil.copy2(src, target)
            finally:
                signal.alarm(0)
            subprocess.run(["xattr", "-d", "com.apple.quarantine", target], capture_output=True)
            notes, _ident = validate(target)
        except Exception as error:
            bad += 1
            print("BAD", src, type(error).__name__, str(error).splitlines()[0][:160], flush=True)
            try:
                os.remove(target)
            except OSError:
                pass
            continue
        used.add(name)
        copied += 1
        if notes:
            warns += 1
            print("WARN", name, notes, flush=True)

    already = len(by_hash) - (copied + bad)
    print(
        f"unique {len(by_hash)} already {already} copied {copied} bad {bad} warn {warns} web_skipped {web} timeouts {len(timeouts)}",
        flush=True,
    )
    return bad


def coretext(dest):
    swift = r'''
import CoreText
import Foundation
let dest = CommandLine.arguments[1]
let files = try FileManager.default.contentsOfDirectory(atPath: dest).filter {
  ["otf","ttf","ttc","otc"].contains(($0 as NSString).pathExtension.lowercased())
}
var bad = 0
for name in files {
  let url = URL(fileURLWithPath: dest + "/" + name) as CFURL
  let descs = CTFontManagerCreateFontDescriptorsFromURL(url) as? [CTFontDescriptor] ?? []
  if descs.isEmpty { bad += 1; print("UNREADABLE \(name)") }
}
print("coretext_ok \(files.count - bad) unreadable \(bad)")
if bad > 0 { exit(1) }
'''
    result = subprocess.run(["swift", "-e", swift, dest], capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


def main():
    if len(sys.argv) < 2:
        print("usage: python3 scripts/install_fonts.py /path/to/downloaded/fonts", file=sys.stderr)
        return 1
    root = os.path.abspath(sys.argv[1])
    dest = os.path.expanduser("~/Library/Fonts")
    os.makedirs(dest, exist_ok=True)
    if not os.path.isdir(root):
        print("missing source folder", root, file=sys.stderr)
        return 1
    bad = install_missing(root, dest)
    dedupe(dest)
    code = coretext(dest)
    return 1 if bad or code else 0


if __name__ == "__main__":
    raise SystemExit(main())
