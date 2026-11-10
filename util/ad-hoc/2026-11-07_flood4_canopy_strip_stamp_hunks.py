#!/usr/bin/env python3
"""
Strip documentation stamp edits and whitespace-only line edits from a fleet docs diff (canopy flood-4).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy docs carrier (#790 #791 #793 #796); adapted from
         2026-10-08_flood3_strip_stamp_hunks.py

Usage: 2026-11-07_flood4_canopy_strip_stamp_hunks.py <in.patch> <out.patch>

Differences from the flood-3 helper, both found on these drafts:
  * A stamp is matched by its VALUE too (x.y.z, YYYY-MM-DD, or "Month D, YYYY"). The flood-3 regex
    matched the `**Last Updated**:` prefix alone, so it would have dropped #793's prose line
    `**Last Updated**: <today UTC>`, which documents the AGENTS.md header format.
  * Each change block is rebuilt as a diff between main's lines and the draft's lines with every
    stamp and every whitespace-only change put back to main's bytes. Neutralising a stamp in place
    reorders a block that interleaves stamps with other edits (#790's CICD_QUICK_START.md header),
    and a whitespace-only change is how #790 dropped main's two-space hard breaks on lines 3-5.
Prints every line it restores, so nothing is dropped silently.
"""

from __future__ import annotations

import difflib
import re
import sys

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
STAMP = re.compile(r"^\*\*(Version|Last Updated|Date)(?:\*\*:|:\*\*)\s*(?:\d+\.\d+\.\d+|\d{4}-\d{2}-\d{2}|(?:" + MONTHS + r") \d{1,2}, \d{4})\s*$")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def stamp_key(text: str) -> str | None:
    m = STAMP.match(text)
    return m.group(1) if m else None


def rebuild_block(removed: list[str], added: list[str], path: str, log: list[str]) -> list[str]:
    """Return diff lines for one change block after restoring stamps and whitespace-only edits."""
    used = [False] * len(removed)
    target: list[str] = []
    for a in added:
        key = stamp_key(a)
        if key is not None:
            idx = next((k for k, r in enumerate(removed) if not used[k] and stamp_key(r) == key), None)
            if idx is not None:
                used[idx] = True
                target.append(removed[idx])
                log.append(f"{path}: stamp restored to main's {removed[idx].strip()!r} (draft: {a.strip()!r})")
                continue
            log.append(f"{path}: ADDED stamp-like line kept (no counterpart): {a.strip()!r}")
            target.append(a)
            continue
        idx = next((k for k, r in enumerate(removed) if not used[k] and r != a and r.rstrip() == a.rstrip()), None)
        if idx is not None:
            used[idx] = True
            target.append(removed[idx])
            log.append(f"{path}: whitespace-only edit reverted to main's bytes: {removed[idx]!r}")
            continue
        target.append(a)
    for k, r in enumerate(removed):
        if not used[k] and stamp_key(r) is not None:
            log.append(f"{path}: REMOVED stamp with no replacement (kept as a removal): {r.strip()!r}")
    out: list[str] = []
    sm = difflib.SequenceMatcher(a=removed, b=target, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            out.extend(" " + x for x in removed[i1:i2])
        else:
            out.extend("-" + x for x in removed[i1:i2])
            out.extend("+" + x for x in target[j1:j2])
    return out


def process_body(body: list[str], path: str, log: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(body):
        line = body[i]
        if line.startswith(("-", "+")):
            removed: list[str] = []
            added: list[str] = []
            while i < len(body) and body[i].startswith(("-", "+")):
                (removed if body[i].startswith("-") else added).append(body[i][1:])
                i += 1
            out.extend(rebuild_block(removed, added, path, log))
            continue
        out.append(line)
        i += 1
    return out


def main() -> int:
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out: list[str] = []
    log: list[str] = []
    header: list[str] = []
    hunks: list[str] = []
    path = ""

    def flush() -> None:
        if header and hunks:
            out.extend(header)
            out.extend(hunks)

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git "):
            flush()
            header, hunks = [line], []
            path = line.split(" b/", 1)[-1]
            i += 1
            while i < len(lines) and not lines[i].startswith(("@@", "diff --git ")):
                header.append(lines[i])
                i += 1
            continue
        m = HUNK.match(line)
        if m:
            old_start, new_start, tail = int(m.group(1)), int(m.group(3)), m.group(5)
            i += 1
            body: list[str] = []
            while i < len(lines) and not lines[i].startswith(("@@", "diff --git ")):
                body.append(lines[i])
                i += 1
            new_body = process_body(body, path, log)
            if not any(x.startswith(("+", "-")) for x in new_body):
                log.append(f"{path}: hunk @@ -{old_start} dropped (no change left)")
                continue
            old_len = sum(1 for x in new_body if x.startswith((" ", "-")))
            new_len = sum(1 for x in new_body if x.startswith((" ", "+")))
            hunks.append(f"@@ -{old_start},{old_len} +{new_start},{new_len} @@{tail}")
            hunks.extend(new_body)
            continue
        i += 1
    flush()
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    for entry in log:
        print(entry)
    print(f"{src}: {len(log)} log entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
