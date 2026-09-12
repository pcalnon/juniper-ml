#!/usr/bin/env python3
"""One-shot: correct docs/REFERENCE.md's false description of remove_stale_worktrees.bash.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-12

Why
---
`docs/REFERENCE.md` described the script as "Removes all stale worktrees". It has NO
staleness predicate of any kind -- it is `git worktree list | grep worktrees` piped into an
unconditional `git worktree remove` loop. The "NEVER run it" warning existed only in
session-scoped memory and in handoff prompts; `AGENTS.md` never mentioned the script, and
`docs/REFERENCE.md` carried only the false description. A fresh session therefore read an
invitation and no warning.

Established by independent consensus 2026-09-12 (4 reviewers, distinct entry points).

Idempotent; refuses on a drifted anchor.
"""

from __future__ import annotations

import pathlib
import sys

TARGET = pathlib.Path(__file__).resolve().parents[3] / "docs" / "REFERENCE.md"

OLD = "    ├── remove_stale_worktrees.bash       # Removes all stale worktrees"
NEW = (
    "    ├── remove_stale_worktrees.bash       # DO NOT RUN -- no staleness predicate; "
    "unconditional `git worktree remove` over every path matching `grep worktrees`. "
    "Use scripts/cleanup_session_worktrees.py or util/worktree_cleanup.bash instead."
)

MARKER = "DO NOT RUN -- no staleness predicate"


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print("already applied")
        return 0
    if src.count(OLD) != 1:
        print(f"REFUSING: anchor found {src.count(OLD)} times (expected 1)", file=sys.stderr)
        return 1
    TARGET.write_text(src.replace(OLD, NEW), encoding="utf-8")
    print(f"corrected the description in {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
