#!/usr/bin/env python3
"""Check that every `#anchor` link in the given markdown files resolves to a heading slug.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc evaluation helper for juniper-data)
Application:  Cursor-fleet flood #3 evaluation (agent data-docs)
Author:       Paul Calnon (generated with Claude Code)
Version:      0.1.0
License:      MIT License

Single-use. juniper-data's `juniper-check-doc-links` hook passes a link to an existing file with
a nonexistent `#anchor` (negative control, 2026-10-08), so it is no evidence that the anchors a
docs consolidation adds resolve. This checks them directly.

Slugs follow GitHub: lowercase; drop every character that is not a letter, digit, space, hyphen
or underscore; each space becomes one hyphen (runs are NOT collapsed); duplicate headings get
`-1`, `-2`, ... suffixes. Headings inside fenced code blocks are ignored.

    python3 util/ad-hoc/2026-10-08_data_docs_check_anchors.py REPO_ROOT FILE.md [FILE.md ...]

Exit 0 when every anchor resolves, 1 otherwise. Cross-repo links (`../../<repo>/...`) and
external URLs are skipped and counted.
"""

import os
import re
import sys

LINK = re.compile(r"\]\(([^)\s]*#[^)\s]+)\)")
HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")


def slug(text: str) -> str:
    text = re.sub(r"`", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def slugs(path: str) -> set[str]:
    out: set[str] = set()
    seen: dict[str, int] = {}
    fenced = False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            m = HEADING.match(line)
            if not m:
                continue
            s = slug(m.group(2))
            n = seen.get(s, 0)
            out.add(s if n == 0 else f"{s}-{n}")
            seen[s] = n + 1
    return out


def main() -> int:
    root = sys.argv[1]
    bad = checked = skipped = 0
    cache: dict[str, set[str]] = {}
    for rel in sys.argv[2:]:
        src = os.path.join(root, rel)
        with open(src, encoding="utf-8") as fh:
            text = fh.read()
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://")):
                skipped += 1
                continue
            file_part, anchor = target.split("#", 1)
            dest = os.path.normpath(os.path.join(os.path.dirname(src), file_part)) if file_part else src
            if not os.path.realpath(dest).startswith(os.path.realpath(root)):
                skipped += 1
                continue
            if not os.path.exists(dest):
                print(f"MISSING FILE {rel}: {target}")
                bad += 1
                continue
            if dest not in cache:
                cache[dest] = slugs(dest)
            checked += 1
            if anchor not in cache[dest]:
                print(f"BROKEN ANCHOR {rel}: {target}")
                bad += 1
    print(f"checked {checked} anchor link(s), skipped {skipped}, broken {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
