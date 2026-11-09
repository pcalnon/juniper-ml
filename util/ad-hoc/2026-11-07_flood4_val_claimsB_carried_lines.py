"""
Re-derive, per flood-4 docs draft, which of the draft's own added lines reached the docs carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 docs carrier validation (claims lens, slice B); notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Independent of the builder's own verify step: the draft's diff is computed here from
refs/flood4/pr/<N> against its merge-base with origin/main, not read from the builder's
extracted hunks. Each added, non-blank, non-stamp line is classified as:

  present    the line occurs verbatim in the carrier's copy of the file
  on-main    the line already occurs verbatim in main's copy (not a draft addition)
  rewritten  a fixes.json entry for this PR has an 'old' fragment contained in the line
  missing    none of the above

Usage:
  python3 <this file> <repo checkout at origin/main> <carrier worktree> <fixes.json> <out.json> <PR>...

The script only reads: git merge-base / git diff in the checkout, and plain file reads of
the carrier worktree. It writes only <out.json>.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

DOC_PATHS = (
    "CHANGELOG.md",
    "docs/REFERENCE.md",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "docs/DOCUMENTATION_OVERVIEW.md",
    "docs/QUICK_START.md",
    "juniper-config-tools/README.md",
    "juniper-service-core/README.md",
)

STAMP_RE = re.compile(r"^\*\*(Version|Last Updated|Date):?\*\*:?")
HISTORY_ROW_RE = re.compile(r"^\|\s*\d+\.\d+\.\d+[^|]*\|\s*\d{4}-\d{2}-\d{2}\s*\|")


def run(cmd: list[str], cwd: str) -> str:
    """Run a read-only command and return its stdout; raise on failure."""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError("%s failed (%d): %s" % (" ".join(cmd), proc.returncode, proc.stderr.strip()))
    return proc.stdout


def added_lines(repo: str, pr: int) -> dict[str, list[str]]:
    """Return {path: [added line, ...]} for the draft's own diff (merge-base..head)."""
    ref = "refs/flood4/pr/%d" % pr
    base = run(["git", "merge-base", "origin/main", ref], repo).strip()
    out = run(["git", "diff", "-U0", "--no-color", base, ref, "--", *DOC_PATHS], repo)
    result: dict[str, list[str]] = {}
    path = None
    for line in out.splitlines():
        if line.startswith("+++ "):
            target = line[4:]
            path = target[2:] if target.startswith("b/") else None
            continue
        if line.startswith("+") and not line.startswith("+++") and path:
            text = line[1:]
            if not text.strip():
                continue
            if STAMP_RE.match(text.strip()) or HISTORY_ROW_RE.match(text.strip()):
                continue
            result.setdefault(path, []).append(text)
    return result


def read_text(path: Path) -> str:
    """Read a file as UTF-8, or return '' when it does not exist."""
    try:
        with path.open(encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        return ""


def main(argv: list[str]) -> int:
    if len(argv) < 6:
        print(__doc__)
        return 2
    repo, carrier, fixes_path, out_path = argv[1], argv[2], argv[3], argv[4]
    prs = [int(x) for x in argv[5:]]
    with open(fixes_path, encoding="utf-8") as handle:
        fixes = json.load(handle)
    report: dict[str, dict] = {}
    for pr in prs:
        olds = [f.get("old", "") for f in fixes if f.get("pr") == pr and f.get("old")]
        per = {"present": 0, "on-main": 0, "rewritten": 0, "missing": []}
        for path, lines in added_lines(repo, pr).items():
            carrier_text = read_text(Path(carrier) / path)
            main_text = read_text(Path(repo) / path)
            for text in lines:
                if text in carrier_text:
                    per["present"] += 1
                elif text in main_text:
                    per["on-main"] += 1
                elif any(old and old in text for old in olds):
                    per["rewritten"] += 1
                else:
                    per["missing"].append({"path": path, "line": text[:300]})
        report[str(pr)] = per
        print("#%d present=%d on-main=%d rewritten=%d missing=%d" % (pr, per["present"], per["on-main"], per["rewritten"], len(per["missing"])))
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
