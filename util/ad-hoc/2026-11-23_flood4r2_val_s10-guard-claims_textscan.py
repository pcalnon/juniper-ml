#!/usr/bin/env python3
"""
Scan every text the agent guard 1.4.0 change would put on main or in its pull request for CI-skip markers, foreign
ids, follow-up language and the rename, and list the ruling citations.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- read-only validation (claims lens on the agent guard 1.4.0 texts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py; CHANGELOG.md; docs/REFERENCE.md

Usage:
    python3 -I 2026-11-23_flood4r2_val_s10-guard-claims_textscan.py <texts dir> <base dir> <staged dir> <out.json>

<texts dir> holds pr_title.txt, pr_body.txt, commit_body.txt and changelog_entry.txt. For each modified file, only
the lines the change adds (difflib against the base copy) are scanned; each added helper is scanned whole.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

PATTERNS = {
    "ci_skip": r"\[(skip ci|ci skip|no ci|skip actions|actions skip)\]|skip-checks\s*:|\*\*\*NO_CI\*\*\*",
    "overtoad": r"overtoad",
    "arc_or_session": r"session \d|flood-?4|flood4|round[- ]?\d|\bR-[A-Z]{2,}|\bD-1\d\b|\bJR-[A-Z]",
    "followup": r"follow-?up|next update|will (be|follow|land|add)|a later (pr|pull request)|its own (pr|pull request)|in a future",
    "ruling": r"owner'?s? rulings? [^.;]{0,80}",
}
MODIFIED = ["CHANGELOG.md", "docs/REFERENCE.md", "util/claude_agent_guard.py", "tests/test_claude_agent_guard.py", "tests/test_claude_agent_guard_brace_cap.py"]


def added_lines(base: Path, staged: Path) -> list:
    old = base.read_text(encoding="utf-8").splitlines()
    new = staged.read_text(encoding="utf-8").splitlines()
    out = []
    for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag in ("replace", "insert"):
            out.extend((j + 1, new[j]) for j in range(j1, j2))
    return out


def main(argv: list) -> int:
    texts, base, staged, out = Path(argv[1]), Path(argv[2]), Path(argv[3]), Path(argv[4])
    corpus = []
    for name in ("pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt"):
        corpus.extend((name, i + 1, line) for i, line in enumerate((texts / name).read_text(encoding="utf-8").splitlines()))
    for rel in MODIFIED:
        corpus.extend((rel, n, line) for n, line in added_lines(base / rel, staged / rel))
    for helper in sorted((staged / "util" / "ad-hoc").glob("*.py")):
        rel = "util/ad-hoc/" + helper.name
        corpus.extend((rel, i + 1, line) for i, line in enumerate(helper.read_text(encoding="utf-8").splitlines()))
    hits = {key: [] for key in PATTERNS}
    for name, n, line in corpus:
        for key, pattern in PATTERNS.items():
            for m in re.finditer(pattern, line, re.IGNORECASE):
                hits[key].append({"where": "%s:%d" % (name, n), "match": m.group(0)[:120]})
    rulings = sorted({h["match"] for h in hits["ruling"]})
    report = {"lines_scanned": len(corpus), "counts": {k: len(v) for k, v in hits.items()}, "ruling_citation_forms": rulings, "hits": {k: v for k, v in hits.items() if k != "ruling"}}
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"lines_scanned": report["lines_scanned"], "counts": report["counts"]}))
    for key in ("ci_skip", "overtoad", "followup"):
        for h in hits[key]:
            print(key, h["where"], h["match"])
    by_file = {}
    for h in hits["arc_or_session"]:
        by_file.setdefault(h["where"].split(":")[0], []).append(h["match"])
    for name, matches in by_file.items():
        print("arc_or_session", name, len(matches), sorted(set(matches))[:6])
    for r in rulings:
        print("ruling-form:", r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
