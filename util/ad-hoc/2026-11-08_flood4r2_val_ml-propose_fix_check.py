#!/usr/bin/env python3
"""Check that the validator's proposed F1/F5/F7 checklist fixes keep the carrier's propose suite green.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (independent validation of the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-propose-code-lens/findings.json (F1, F5, F7)

Applies the three exact old->new replacements to ``<worktree>/util/release_train/propose.py`` (each old string must
occur once), runs the whole propose suite, prints the result, and restores the file byte-for-byte (sha256 checked).
Run it ONLY against the validator's own worktree.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess  # nosec B404 - fixed argv (this interpreter), no shell
import sys
from pathlib import Path

REVIEW_NOTES = """        if report.get("matrix_row") == "added":
            notes.append("the previous series' row is not touched: if a PR since that series' last release rewrote it in place (an escaping column pin, or a hand floor raise that ReferenceCompatibilityMatrixTest made move the then-current row), restore the pins that series published")
        if report.get("recurrence") == "edited":
            notes.append("the clause now names this release, so words after its pins that say what a release changed (': it raises ...') now describe this one: reword them")
        if report.get("recurrence_moved"):"""

FIXES = [
    (
        '            done.append(f"a new `{series}` matrix row (the older rows stay: they describe published releases)")',
        '            done.append(f"a new `{series}` matrix row (the older rows are not touched)")',
    ),
    ('        if report.get("recurrence_moved"):', REVIEW_NOTES),
    ('    if meta_bump or report.get("matrix_row") == "edited":', "    if meta_bump or done:"),
]


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    args = ap.parse_args(argv)
    root = Path(args.worktree)
    target = root / "util" / "release_train" / "propose.py"
    original = target.read_bytes()
    before = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    for old, new in FIXES:
        if text.count(old) != 1:
            print("anchor not unique:", old[:80])
            return 2
        text = text.replace(old, new)
    try:
        target.write_text(text, encoding="utf-8")
        for cache in (root / "util").rglob("__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)
        proc = subprocess.run([sys.executable, "-B", "-m", "unittest", "tests/test_release_train_propose.py"], cwd=str(root), capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
        print("\n".join(ln for ln in proc.stderr.strip().splitlines() if ln.startswith(("Ran ", "OK", "FAILED", "FAIL:", "ERROR:"))))
    finally:
        target.write_bytes(original)
    after = hashlib.sha256(target.read_bytes()).hexdigest()
    print("restored identical:", before == after)
    return 0


if __name__ == "__main__":
    sys.exit(main())
