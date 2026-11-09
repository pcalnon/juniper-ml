#!/usr/bin/env python3
"""
Independent fidelity check of the juniper-canopy flood-4 DOCS carrier against the drafts' own hunks and main.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy DOCS carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#790 #791 #793 #796; flood-4 validation brief (fidelity lens)

Reads git objects from the canopy primary (the drafts' heads and their PR base SHAs) and the carrier's working-tree
files READ-ONLY; writes nothing to any repository. For every file the carrier changes:
  * each line the carrier ADDS vs main must be a line some draft adds (verbatim), a piece of a draft line the
    carrier wrapped, or a stamp line; anything else is listed as UNEXPLAINED-ADD;
  * each line the carrier DELETES vs main must be a line some draft deletes, or a stamp line; else UNEXPLAINED-DEL;
  * each non-stamp line a draft adds must be in the carrier verbatim or as wrapped pieces; else DRAFT-LINE-MISSING;
  * every stamp line in the carrier (header and footer) is listed with main's value, so a reader can check one bump.

    python3 2026-11-07_flood4_val_canopy_docs_fidelity.py <canopy primary> <carrier worktree> <main sha> <probe commit> <pr>=<base>..<head> ...

<probe commit> holds the carrier's files (made in the validator's OWN worktree); only its file LIST is used.
"""

from __future__ import annotations

import difflib
import json
import re
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
from pathlib import Path

STAMP = re.compile(r"^\*\*(Version|Last Updated|Date)(:\*\*|\*\*:)")


def _git(root: str, *args: str) -> str:
    return subprocess.run(["git", "-C", root, *args], check=True, capture_output=True, text=True).stdout


def _show(root: str, rev: str, path: str) -> str | None:
    try:
        return _git(root, "show", f"{rev}:{path}")
    except subprocess.CalledProcessError:
        return None


def _delta(a: str, b: str) -> tuple[list[str], list[str]]:
    added, deleted = [], []
    for line in difflib.unified_diff(a.split("\n"), b.split("\n"), lineterm="", n=0):
        if line.startswith(("+++", "---", "@@")):
            continue
        if line.startswith("+"):
            added.append(line[1:])
        elif line.startswith("-"):
            deleted.append(line[1:])
    return added, deleted


def _norm(s: str) -> str:
    return " ".join(s.split())


def main() -> int:
    primary, carrier, main_sha, probe = sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4]
    drafts = {}
    for spec in sys.argv[5:]:
        pr, rng = spec.split("=", 1)
        base, head = rng.split("..", 1)
        drafts[pr] = (base, head)
    # The file LIST comes from a probe commit made in the validator's own worktree; no git command runs in the carrier.
    changed = [p for p in _git(primary, "diff", "--name-only", main_sha, probe).split() if p]
    report: dict = {"main": main_sha, "files": {}}
    draft_add: dict[str, dict[str, list[str]]] = {}
    draft_del: dict[str, dict[str, list[str]]] = {}
    for pr, (base, head) in drafts.items():
        for path in _git(primary, "diff", "--name-only", base, head).split():
            a, d = _delta(_show(primary, base, path) or "", _show(primary, head, path) or "")
            draft_add.setdefault(path, {})[pr] = a
            draft_del.setdefault(path, {})[pr] = d
    for path in changed:
        main_text = _show(primary, main_sha, path) or ""
        carrier_text = (carrier / path).read_text(encoding="utf-8")
        c_add, c_del = _delta(main_text, carrier_text)
        adds_by_pr = draft_add.get(path, {})
        dels_by_pr = draft_del.get(path, {})
        all_draft_adds = {line for lines in adds_by_pr.values() for line in lines}
        all_draft_dels = {line for lines in dels_by_pr.values() for line in lines}
        norm_draft_adds = [_norm(x) for x in all_draft_adds if x.strip()]
        unexplained_add, unexplained_del = [], []
        for line in c_add:
            if line in all_draft_adds or STAMP.match(line) or not line.strip():
                continue
            n = _norm(line)
            if any(n and n in big for big in norm_draft_adds):
                continue  # a piece of a draft line the carrier wrapped
            unexplained_add.append(line)
        for line in c_del:
            if line in all_draft_dels or STAMP.match(line) or not line.strip():
                continue
            unexplained_del.append(line)
        missing = {}
        carrier_norm = _norm(carrier_text)
        carrier_lines = set(carrier_text.split("\n"))
        for pr, lines in adds_by_pr.items():
            miss = [x for x in lines if x.strip() and not STAMP.match(x) and x not in carrier_lines and _norm(x) not in carrier_norm]
            if miss:
                missing[pr] = miss
        stamps = {
            "main": [line for line in main_text.split("\n") if STAMP.match(line)],
            "carrier": [line for line in carrier_text.split("\n") if STAMP.match(line)],
        }
        report["files"][path] = {
            "carrier_added": len(c_add),
            "carrier_deleted": len(c_del),
            "drafts": sorted(adds_by_pr),
            "UNEXPLAINED-ADD": unexplained_add,
            "UNEXPLAINED-DEL": unexplained_del,
            "DRAFT-LINE-MISSING": missing,
            "stamps": stamps,
        }
    # Draft-touched files the carrier does NOT change.
    report["draft_files_not_in_carrier"] = sorted(set(draft_add) - set(changed))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
