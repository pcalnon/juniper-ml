"""
Revert over-eager basename swaps made by 2026-07-04_notes_rename_refupdate.py.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-07-04
Status: retired 2026-07-06 — migration complete (kept for provenance)
Retire when: the notes/ naming-convention migration PR is merged and verified
Related: util/ad-hoc/2026-07-04_notes_rename_refupdate.py

The basename rewrite must NOT apply when the surrounding path shows the
reference targets a file that was never renamed:
  (a) a SIBLING repo's notes tree — e.g. juniper-cascor/notes/development/
      CONSOLIDATED_DEVELOPMENT_RECORD.md coincidentally shares a basename
      with juniper-ml's renamed file;
  (b) juniper-ml's own EXEMPT dirs (legacy/, releases/, requirements/,
      templates/) — e.g. notes/legacy/REGRESSION_ANALYSIS_2026-04-03.md
      shares a basename with the renamed notes/regressions/ file.
This script maps NEW basenames back to OLD wherever they appear directly
under either context. Run after the refupdate pass; idempotent.

Usage:  python util/ad-hoc/2026-07-04_notes_rename_context_revert.py [--apply]
"""

import re
import subprocess
import sys
from pathlib import Path

MAP_TSV = Path("util/ad-hoc/2026-07-04_notes_rename_map.tsv")
SKIP_FILES = {
    "util/ad-hoc/2026-07-04_notes_rename_map.tsv",
    "util/ad-hoc/2026-07-04_notes_rename_convention.py",
    "util/ad-hoc/2026-07-04_notes_rename_refupdate.py",
    "util/ad-hoc/2026-07-04_notes_rename_context_revert.py",
}
SIBLINGS = "cascor-client|cascor-worker|data-client|cascor|canopy|data|deploy|recurrence|slacker"
SIBLING_CTX = rf"(?<![A-Za-z0-9-])juniper-(?:{SIBLINGS})(?:/(?:blob|tree)/[^\s/]+)?/notes/[^\s`\"'()\[\]]*?"
EXEMPT_CTX = r"notes/(?:legacy|releases|requirements|templates)/[^\s`\"'()\[\]]*?"


def main():
    apply_edits = "--apply" in sys.argv[1:]
    rules = []
    for line in MAP_TSV.read_text().splitlines():
        old, new = line.split("\t")
        old_base, new_base = old.rsplit("/", 1)[-1], new.rsplit("/", 1)[-1]
        rules.append((re.compile(f"({SIBLING_CTX}){re.escape(new_base)}"), old_base))
        rules.append((re.compile(f"({EXEMPT_CTX}){re.escape(new_base)}"), old_base))
    total_files = total_hits = 0
    for f in subprocess.run(["git", "ls-files"], check=True, capture_output=True, text=True).stdout.splitlines():
        if f in SKIP_FILES:
            continue
        p = Path(f)
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = 0
        for rx, old_base in rules:
            text, n = rx.subn(lambda m, ob=old_base: m.group(1) + ob, text)
            hits += n
        if hits:
            total_files += 1
            total_hits += hits
            print(f"{hits:5d}  {f}")
            if apply_edits:
                p.write_text(text, encoding="utf-8")
    mode = "APPLIED" if apply_edits else "DRY RUN"
    print(f"{mode}: {total_hits} context reverts in {total_files} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
