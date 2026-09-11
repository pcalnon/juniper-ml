#!/usr/bin/env python3
"""One-shot edit: correct docs/REFERENCE.md's soak ledger-leak row for item F'.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-10

Why a script rather than a hand edit
------------------------------------
``util/open_signed_pr.py`` and its append helper upload WHOLE FILES. ``docs/REFERENCE.md``
is one of the busiest files in the repo -- ml#1886 added 179 lines to it while this work was
in flight -- so an edit made against a stale local copy silently reverts whoever landed in
between. This script applies the edit to whatever the current file says, and refuses if the
anchor is not present exactly once, so a drifted base fails loudly instead of clobbering.

The edit itself: the row claimed "8 of 43 runs read the ledger, and the contamination screen
matches neither its path nor `obs_id`". Both halves are now wrong -- 8 TOUCHED it and exactly
one read its CONTENT (re-derived 2026-09-10), and the screen matches both after item F'.

Idempotent: running it twice is a no-op.

Usage
-----
    python3 util/ad-hoc/2026-09-10_soak_stopping_rule/apply_reference_ledger_edit.py
"""

from __future__ import annotations

import pathlib
import sys

TARGET = pathlib.Path(__file__).resolve().parents[3] / "docs" / "REFERENCE.md"

OLD = (
    "| A hit that is not a read | `grep -rln` returns the path with no content; the ledger's "
    "own `.jsonl` quotes the pointer, outcome and answer in prose. 8 of 43 runs read the "
    "ledger, and the contamination screen matches neither its path nor `obs_id`. |"
)

NEW = (
    "| A hit that is not a read | `grep -rln` returns the path with no content; the ledger's "
    "own `.jsonl` quotes the pointer, outcome and answer in prose. **8 of 43 runs TOUCHED the "
    "ledger; exactly ONE read its contents** (`P18-health-interval-non-positive`, "
    "2026-08-22T21:41:09Z) — the other seven saw the filename in a status line, a diff stat or "
    "a `grep -l` list. Re-derived 2026-09-10 by "
    "`util/ad-hoc/2026-09-10_soak_stopping_rule/ledger_exposure_probe.py`; this row said "
    "\"8 … read the ledger\" until then, which overstates the exposure 8×. The contamination "
    "screen now matches the ledger and splits content from filename; it still does **not** run "
    "as part of scoring. |"
)

MARKER = "8 of 43 runs TOUCHED the ledger"


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print("already applied")
        return 0
    n = src.count(OLD)
    if n != 1:
        print(f"REFUSING: anchor found {n} times in {TARGET} (expected 1). The file has "
              f"drifted -- re-read it and update this script's OLD string.", file=sys.stderr)
        return 1
    TARGET.write_text(src.replace(OLD, NEW), encoding="utf-8")
    print(f"applied the ledger-exposure correction to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
