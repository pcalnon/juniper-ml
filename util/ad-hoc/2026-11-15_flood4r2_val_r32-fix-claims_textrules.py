#!/usr/bin/env python3
"""
Screen every text a juniper-cascor fix carrier would land or post for the arc's text rules.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (a claims-lens validation of one carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the cascor pause check-then-act fix carrier's claims lens (session 9)

Reads the carrier's texts (PR title, PR body, commit body, CHANGELOG entry) and the text this
change ADDS to its documents, code and test module (added lines only, from a difflib comparison
with the base copies passed in), then reports every match of: a promised follow-up; a session,
plan, arc, round, register or ruling number; a CI-skip marker; each citation of the Overtoad's
ruling; and the PR body's Requirements section. Writes one JSON report and prints a summary.
Exit 0 always: the report is for a human to judge, not a gate.
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

PATTERNS: Dict[str, str] = {
    "follow_up": r"follow[- ]?up|later (?:PR|pull request)|next (?:PR|pull request)|a future|\bwill (?:be|land|fix|close|add|follow)\b|until the fix|to be fixed|\bTODO\b|\bFIXME\b",
    "arc_session_plan_register": r"\bsession\b|\bplan\b|\barcs?\b|\bround \d|APD-|JR-[A-Z]|R-OBS|\b[NMD]-?\d{1,2}\b|\bF\d{1,2}\b|register|\br\d{2}\b|flood4r2|\bphase \d",
    "ruling_number": r"rulings? (?:no\.? ?)?\d+|§\s*\d|section \d",
    "ruling_citation": r"Overtoad'?s ruling[^.;\n]*",
    "ci_skip": r"\[(?:skip ci|ci skip|no ci|skip actions|actions skip)\]|skip-checks|\*\*\*NO_CI\*\*\*",
}


def added_lines(base: Path, head: Path) -> List[str]:
    """Return the lines head adds relative to base (a new file: every line)."""
    head_lines = head.read_text(encoding="utf-8").splitlines()
    if not base.is_file():
        return head_lines
    base_lines = base.read_text(encoding="utf-8").splitlines()
    out: List[str] = []
    for line in difflib.unified_diff(base_lines, head_lines, lineterm="", n=0):
        if line.startswith("+") and not line.startswith("+++"):
            out.append(line[1:])
    return out


def screen(name: str, lines: List[str]) -> List[dict]:
    hits: List[dict] = []
    for number, line in enumerate(lines, start=1):
        for kind, pattern in PATTERNS.items():
            for match in re.finditer(pattern, line, flags=re.IGNORECASE):
                hits.append({"text": name, "line": number, "kind": kind, "match": match.group(0), "context": line.strip()[:220]})
    return hits


def requirements_section(body: str) -> str:
    match = re.search(r"^## Requirements\s*\n(.*?)(?=^## |\Z)", body, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else "<missing>"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--texts", required=True, type=Path, help="directory holding pr_title.txt, pr_body.txt, commit_body.txt, changelog_entry.txt")
    parser.add_argument("--pair", action="append", default=[], help="NAME=BASE_PATH::HEAD_PATH (added lines of HEAD vs BASE are screened)")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    report: dict = {"hits": [], "requirements": None, "screened": []}
    for leaf in ("pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt"):
        path = args.texts / leaf
        lines = path.read_text(encoding="utf-8").splitlines()
        report["screened"].append({"text": leaf, "lines": len(lines)})
        report["hits"].extend(screen(leaf, lines))
    report["requirements"] = requirements_section((args.texts / "pr_body.txt").read_text(encoding="utf-8"))
    for spec in args.pair:
        name, _, paths = spec.partition("=")
        base_text, _, head_text = paths.partition("::")
        lines = added_lines(Path(base_text), Path(head_text))
        report["screened"].append({"text": name, "added_lines": len(lines)})
        report["hits"].extend(screen(name, lines))

    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    counts: Dict[str, int] = {}
    for hit in report["hits"]:
        counts[hit["kind"]] = counts.get(hit["kind"], 0) + 1
    print("screened:", json.dumps(report["screened"]))
    print("hits by kind:", json.dumps(counts, sort_keys=True))
    print("requirements:", report["requirements"][:200])
    for hit in report["hits"]:
        print(f"{hit['kind']:<26} {hit['text']}:{hit['line']} [{hit['match']}] {hit['context'][:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
