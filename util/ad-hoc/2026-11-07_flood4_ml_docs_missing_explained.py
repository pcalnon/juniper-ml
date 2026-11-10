#!/usr/bin/env python3
"""
Prove every draft line absent from the flood-4 docs carrier is a recorded fix, a dropped history row, or a protected-block skip.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs-carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-08_flood3_verify_carried_lines.py (writes the MISSING list this reads),
         util/ad-hoc/2026-11-07_flood4_ml_docs_fixes.py (fixes.json)

A MISSING line is EXPLAINED when it is a Version History row (`| 0.6.NN  | 2026-`), when it contains the `old`
text of one of that draft's recorded fixes, or when it is one of the `--skipped` substrings (the apply log's
protected-block skips). Anything else is printed UNEXPLAINED and the exit status is 1.

Usage: 2026-11-07_flood4_ml_docs_missing_explained.py <verify_carried.log> <own-diff-dir> <fixes.json> [--skipped TEXT ...]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HISTORY = re.compile(r"^\| 0\.6\.\d+ +\| 20\d\d-")


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 2
    log, diff_dir, fixes_path = Path(argv[1]), Path(argv[2]), Path(argv[3])
    skipped = [argv[k + 1] for k, a in enumerate(argv) if a == "--skipped"]
    with open(fixes_path, encoding="utf-8") as fh:
        fixes = json.load(fh)
    olds: dict[int, list[str]] = {}
    for f in fixes:
        if "old" in f:
            # a multi-line `old` explains each of its lines
            olds.setdefault(f["pr"], []).extend(x for x in f["old"].split("\n") if x.strip())
    pr = None
    unexplained = 0
    counts: dict[str, int] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\[(\d+)\]", line)
        if m:
            pr = int(m.group(1))
            continue
        if not line.strip().startswith("MISSING ") or pr is None:
            continue
        # recover the full added line from the draft's own diff (the log truncates it)
        prefix = line.split(": ", 1)[1]
        full = next((a[1:] for a in (diff_dir / f"{pr}.diff").read_text(encoding="utf-8").split("\n") if a.startswith("+") and a[1:].strip().startswith(prefix.strip()[:120])), prefix)
        if HISTORY.match(full):
            counts["history-row"] = counts.get("history-row", 0) + 1
        elif any(o in full or full.strip() in o for o in olds.get(pr, [])):
            counts["fixed"] = counts.get("fixed", 0) + 1
        elif any(s in full for s in skipped):
            counts["protected-skip"] = counts.get("protected-skip", 0) + 1
        else:
            unexplained += 1
            print(f"UNEXPLAINED #{pr}: {full[:160]}")
    print(f"explained: {counts}; unexplained: {unexplained}")
    return 1 if unexplained else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
