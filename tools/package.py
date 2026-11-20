#!/usr/bin/env python3
"""Package dist/ as the Cloudflare Pages Direct Upload zip."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUTPUT = ROOT.parent / "youchai-courses.zip"

ALLOWED_TOP = {
    "index.html",
    "404.html",
    "_headers",
    "sitemap.xml",
    "robots.txt",
    "feed.xml",
    "assets",
    "courses",
    "reference",
    "quiz",
    "tags",
    "progress",
    "changelog",
}

FORBIDDEN_SUFFIXES = {
    ".md",
    ".py",
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
    ".xlsx",
}


def main() -> int:
    if not DIST.is_dir():
        print(f"FAILED: missing {DIST}")
        return 1

    top_level = {p.name for p in DIST.iterdir()}
    unexpected = top_level - ALLOWED_TOP
    if unexpected:
        print(f"FAILED: unexpected dist entries: {sorted(unexpected)}")
        return 1

    files = sorted((p for p in DIST.rglob("*") if p.is_file()), key=lambda p: p.relative_to(DIST).as_posix())
    if not files:
        print("FAILED: dist is empty")
        return 1

    for path in files:
        rel = path.relative_to(DIST)
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            print(f"FAILED: forbidden path {rel.as_posix()}")
            return 1
        if path.suffix.lower() in FORBIDDEN_SUFFIXES and rel.as_posix() != "robots.txt":
            print(f"FAILED: forbidden file type {rel.as_posix()}")
            return 1
        if path.read_bytes().startswith(b"\xef\xbb\xbf"):
            print(f"FAILED: UTF-8 BOM in {rel.as_posix()}")
            return 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            rel = path.relative_to(DIST).as_posix()
            archive.write(path, rel)

    with zipfile.ZipFile(OUTPUT, "r") as archive:
        names = archive.namelist()
        bad = archive.testzip()
        if bad:
            print(f"FAILED: corrupt zip entry {bad}")
            return 1
        top = {name.split("/", 1)[0] for name in names}
        if top != ALLOWED_TOP:
            print(f"FAILED: zip top level mismatch: {sorted(top)}")
            return 1

    print(f"packaged {len(files)} files into {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
