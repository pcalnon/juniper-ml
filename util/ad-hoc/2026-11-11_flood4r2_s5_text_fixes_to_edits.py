#!/usr/bin/env python3
"""
Turn a validator's text_fixes.json (a list of exact old -> new fixes) into an edits spec for
2026-11-08_flood4r2_fix_apply_edits.py, which requires every ``old`` to occur exactly once.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 session 5: applying a final check's text fixes at landing)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-08_flood4r2_fix_apply_edits.py (applies the spec this writes),
         util/ad-hoc/2026-11-09_flood4r2_land_findings_to_edits.py (the same job for a findings.json whose fixes are edits)

Usage:
  2026-11-11_flood4r2_s5_text_fixes_to_edits.py <text_fixes.json> <tree> <deliverables-rel> <out edits.json>
      [--skip <finding id prefix> ...]

Each fix is {"finding", "file", "old", "new"[, "expected_count"]}. A ``file`` that starts with ``DELIVERABLES/`` is
mapped into <deliverables-rel> (the carrier's deliverables directory, relative to <tree>); one that starts with
``COPY/`` is the repository path after that prefix. A fix whose ``finding`` starts with a ``--skip`` prefix is left
out and listed. A fix with ``expected_count`` N > 1 becomes N edits: each occurrence's ``old`` is grown backwards a
line at a time until that text occurs exactly once in the file. Every other ``old`` must occur exactly once already.
The files are read, never written. Exit 0 = spec written; 1 = refused (the reason is printed, nothing is written).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DELIVERABLES_PREFIX = "DELIVERABLES/"
COPY_PREFIX = "COPY/"


def occurrences(text: str, needle: str) -> list[int]:
    found: list[int] = []
    start = text.find(needle)
    while start != -1:
        found.append(start)
        start = text.find(needle, start + 1)
    return found


def widen(text: str, position: int, old: str) -> str:
    """Grow ``old`` backwards from ``position``, one line at a time, until it occurs once in ``text``."""
    begin = position
    candidate = old
    while len(occurrences(text, candidate)) != 1:
        if begin == 0:
            raise ValueError("cannot make the occurrence unique by growing its context backwards")
        previous_newline = text.rfind("\n", 0, begin - 1)
        begin = previous_newline + 1
        candidate = text[begin : position + len(old)]
    return candidate


def main(argv: list[str]) -> int:
    if len(argv) < 5:
        print(__doc__)
        return 2
    fixes = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    tree = Path(argv[2]).resolve()
    deliverables = argv[3].strip("/")
    out = Path(argv[4])
    skips = [argv[index + 1] for index, word in enumerate(argv[:-1]) if word == "--skip"]
    edits: list[dict] = []
    skipped: list[str] = []
    for number, fix in enumerate(fixes, start=1):
        finding = str(fix.get("finding", f"fix{number}"))
        if any(finding.startswith(prefix) for prefix in skips):
            skipped.append(f"{finding} -> {fix['file']}")
            continue
        name = fix["file"]
        if name.startswith(DELIVERABLES_PREFIX):
            rel = f"{deliverables}/{name[len(DELIVERABLES_PREFIX):]}"
        elif name.startswith(COPY_PREFIX):
            rel = name[len(COPY_PREFIX) :]
        else:
            print(f"REFUSED: {finding}: file {name!r} starts with neither {DELIVERABLES_PREFIX} nor {COPY_PREFIX}")
            return 1
        path = tree / rel
        if not path.is_file():
            print(f"REFUSED: {finding}: {rel} is not a file under {tree}")
            return 1
        text = path.read_bytes().decode("utf-8")
        old, new = fix["old"], fix["new"]
        expected = int(fix.get("expected_count", 1))
        found = occurrences(text, old)
        if len(found) != expected:
            print(f"REFUSED: {finding}: {rel} holds the old text {len(found)} time(s), expected {expected}")
            return 1
        ident = finding.split(" ", 1)[0]
        if expected == 1:
            edits.append({"id": f"{ident}-{number}", "file": rel, "old": old, "new": new})
            continue
        for index, position in enumerate(found, start=1):
            try:
                wide = widen(text, position, old)
            except ValueError as exc:
                print(f"REFUSED: {finding}: {rel} occurrence {index}: {exc}")
                return 1
            edits.append({"id": f"{ident}-{number}.{index}", "file": rel, "old": wide, "new": wide[: len(wide) - len(old)] + new})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"worktree": str(tree), "edits": edits}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for line in skipped:
        print(f"skipped: {line}")
    print(f"edits: {len(edits)} from {len(fixes)} fixes ({len(skipped)} skipped) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
