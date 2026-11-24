#!/usr/bin/env python3
"""
Apply exact old -> new text edits to an uncommitted carrier worktree, all or nothing, with sha256 before and after.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: applying the independent validators' findings to the carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt; tmp/flood4r2-val/<lens>/findings.json (the findings applied)

Usage:
  2026-11-08_flood4r2_fix_apply_edits.py <edits.json> <log.json> [--dry-run]

edits.json:
  {"worktree": "<absolute path>",
   "edits": [{"id": "<finding id>", "file": "<repo-relative path>", "old": "<exact text>", "new": "<replacement>"}]}

Every ``old`` must occur EXACTLY once in its file, as the file stands after the edits listed before it, or nothing
is written at all. An edit whose ``new`` already occurs exactly once, with its ``old`` absent or contained in that
``new`` (an insertion), is reported as ``already-applied`` and skipped, so a re-run is idempotent. Files are read and written as UTF-8 bytes, so line
endings and a missing final newline are kept. The log records each file's sha256 before and after.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    spec = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    log_path = Path(argv[2])
    dry_run = "--dry-run" in argv[3:]
    root = Path(spec["worktree"]).resolve()
    texts: dict[str, str] = {}
    before: dict[str, str] = {}
    rows = []
    ok = True
    for edit in spec["edits"]:
        rel = edit["file"]
        if rel not in texts:
            raw = (root / rel).read_bytes()
            before[rel] = _sha(raw)
            texts[rel] = raw.decode("utf-8")
        text = texts[rel]
        count_old = text.count(edit["old"])
        count_new = text.count(edit["new"]) if edit["new"] else 0
        if count_new == 1 and (count_old == 0 or edit["old"] in edit["new"]):
            # Also covers an insertion, whose new text contains the old: re-applying it would insert twice.
            status = "already-applied"
        elif count_old == 1:
            texts[rel] = text.replace(edit["old"], edit["new"], 1)
            status = "applied"
        else:
            status = f"REFUSED (old occurs {count_old} times, new {count_new} times)"
            ok = False
        rows.append({"id": edit["id"], "file": rel, "status": status, "line": text[: text.index(edit["old"])].count("\n") + 1 if count_old == 1 else None})
    after: dict[str, str] = {}
    if ok and not dry_run:
        for rel, text in texts.items():
            data = text.encode("utf-8")
            if _sha(data) != before[rel]:
                (root / rel).write_bytes(data)
            after[rel] = _sha((root / rel).read_bytes())
    record = {"worktree": str(root), "dry_run": dry_run, "all_applied": ok, "edits": rows, "sha256_before": before, "sha256_after": after if ok and not dry_run else None}
    log_path.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        print(f"{row['id']:10} {row['file']}: {row['status']}" + (f" (line {row['line']})" if row["line"] else ""))
    print(f"all_applied={ok} dry_run={dry_run} log={log_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
