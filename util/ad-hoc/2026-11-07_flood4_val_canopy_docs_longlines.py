#!/usr/bin/env python3
"""
List every line longer than a limit that each draft ADDS (its own hunks), and every such line in the carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy DOCS carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#790 #791 #793 #796 (markdownlint MD013 at 512)

Reads git objects from the canopy primary and the carrier's files read-only; writes nothing to any repository.

    python3 2026-11-07_flood4_val_canopy_docs_longlines.py <canopy primary> <carrier worktree> <limit> <probe> <main> <pr>=<base>..<head> ...
"""

from __future__ import annotations

import difflib
import json
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
from pathlib import Path


def _git(root: str, *args: str) -> str:
    return subprocess.run(["git", "-C", root, *args], check=True, capture_output=True, text=True).stdout


def main() -> int:
    primary, carrier, limit, probe, main_sha = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
    out: dict = {"limit": limit, "drafts": {}, "carrier": {}}
    for spec in sys.argv[6:]:
        pr, rng = spec.split("=", 1)
        base, head = rng.split("..", 1)
        rows = []
        for path in _git(primary, "diff", "--name-only", base, head).split():
            if not path.endswith(".md"):
                continue
            old = _git(primary, "show", f"{base}:{path}").split("\n")
            new = _git(primary, "show", f"{head}:{path}").split("\n")
            for line in difflib.unified_diff(old, new, lineterm="", n=0):
                if line.startswith("+") and not line.startswith("+++") and len(line) - 1 > limit:
                    rows.append({"path": path, "len": len(line) - 1, "start": line[1:80]})
        out["drafts"][pr] = rows
    for path in _git(primary, "diff", "--name-only", main_sha, probe).split():
        lines = (carrier / path).read_text(encoding="utf-8").split("\n")
        long_ = [{"line": i, "len": len(x)} for i, x in enumerate(lines, start=1) if len(x) > limit]
        if long_:
            out["carrier"][path] = long_
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
