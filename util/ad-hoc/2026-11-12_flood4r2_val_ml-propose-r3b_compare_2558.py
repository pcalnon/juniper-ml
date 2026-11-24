#!/usr/bin/env python3
"""
Compare what juniper-ml#2558 (the 0.11.5 proposal) changed with what the extended propose.py generates from the same main.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14; juniper-ml#2558

WHY THIS EXISTS
juniper-ml#2558 was generated on main f9582a74 by main's propose.py, with docs/REFERENCE.md edited by hand. The
ml-propose carrier makes propose.py render that file's four release sites. Whether the tool would have produced
this proposal is read off three trees:

* main (f9582a74) and the pull request's commits, from the object store;
* the simulator's sandbox in which the EXTENDED propose.py built a 0.11.5 proposal from main plus the carrier
  (its docs/REFERENCE.md also holds the carrier's own three lines, which are set aside by comparing site lines);
* the simulator's sandbox in which main's propose.py built the same proposal (pyproject.toml, CHANGELOG.md,
  README.md and AGENTS.md come from code the carrier does not change).

Usage:
    python3 <this> --repo <own worktree> --main <sha> --generated <sha of the PR's first commit> --head <PR head>
                   --extended <sandbox landed--patch> --unextended <sandbox main--patch> --out <json>
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only plumbing in the validator's own worktree
import sys
from pathlib import Path

REFERENCE = "docs/REFERENCE.md"
VERSION_CELL = re.compile(r"^\| \*\*Version\*\* .*$", re.MULTILINE)
PARAGRAPH = re.compile(r"^`juniper-ml` \d+\.\d+\.\d+ declares the following pins\..*$", re.MULTILINE)
SERIES_ROW = re.compile(r"^\| \d+\.\d+\.x\s+\|.*$", re.MULTILINE)


def show(repo: Path, spec: str) -> str:
    return subprocess.run(["git", "show", spec], cwd=repo, capture_output=True, check=True).stdout.decode("utf-8")  # nosec B603 B607


def changed_lines(old: str, new: str) -> list:
    old_lines, new_lines = old.splitlines(), new.splitlines()
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False).get_opcodes():
        if tag != "equal":
            out.append({"old_lines": [i1 + 1, i2], "new_lines": [j1 + 1, j2], "removed": i2 - i1, "added": j2 - j1})
    return out


def words(old: str, new: str) -> list:
    a, b = old.split(" "), new.split(" ")
    return [[" ".join(a[i1:i2]), " ".join(b[j1:j2])] for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes() if tag != "equal"]


def sites(text: str) -> dict:
    return {"version_cell": VERSION_CELL.findall(text), "paragraph": PARAGRAPH.findall(text), "series_rows": SERIES_ROW.findall(text)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--main", required=True)
    parser.add_argument("--generated", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--extended", required=True, type=Path)
    parser.add_argument("--unextended", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    main_ref, generated_ref, head_ref = (show(repo, f"{rev}:{REFERENCE}") for rev in (args.main, args.generated, args.head))
    tool_ref = (args.extended / REFERENCE).read_text(encoding="utf-8")
    report: dict = {"main": args.main, "pr_first_commit": args.generated, "pr_head": args.head}
    report["reference_lines_the_pr_changed"] = {"first_commit_vs_main": changed_lines(main_ref, generated_ref), "head_vs_main": changed_lines(main_ref, head_ref)}
    main_sites, head_sites, tool_sites = sites(main_ref), sites(head_ref), sites(tool_ref)
    report["version_cell"] = {"main": main_sites["version_cell"], "pr_head": head_sites["version_cell"], "extended_tool": tool_sites["version_cell"], "pr_equals_tool": head_sites["version_cell"] == tool_sites["version_cell"]}
    report["series_rows"] = {"pr_equals_main": head_sites["series_rows"] == main_sites["series_rows"], "tool_equals_main": tool_sites["series_rows"] == main_sites["series_rows"], "pr_equals_tool": head_sites["series_rows"] == tool_sites["series_rows"]}
    paragraphs = {"main": main_sites["paragraph"], "pr_head": head_sites["paragraph"], "extended_tool": tool_sites["paragraph"]}
    report["paragraph_counts"] = {key: len(value) for key, value in paragraphs.items()}
    if all(len(value) == 1 for value in paragraphs.values()):
        report["paragraph"] = {
            "pr_equals_tool": paragraphs["pr_head"] == paragraphs["extended_tool"],
            "words_main_to_tool": words(paragraphs["main"][0], paragraphs["extended_tool"][0]),
            "words_main_to_pr": words(paragraphs["main"][0], paragraphs["pr_head"][0]),
            "words_tool_to_pr": words(paragraphs["extended_tool"][0], paragraphs["pr_head"][0]),
        }
    files = {}
    for path in ("pyproject.toml", "AGENTS.md", "README.md", "CHANGELOG.md"):
        tool = (args.unextended / path).read_text(encoding="utf-8")
        first, head = show(repo, f"{args.generated}:{path}"), show(repo, f"{args.head}:{path}")
        files[path] = {
            "tool_equals_pr_first_commit": tool == first,
            "tool_equals_pr_head": tool == head,
            "tool_vs_first_commit_changed_blocks": len(changed_lines(tool, first)),
            "first_commit_vs_head_changed_blocks": len(changed_lines(first, head)),
            "sha256": {"tool": hashlib.sha256(tool.encode()).hexdigest()[:12], "pr_first_commit": hashlib.sha256(first.encode()).hexdigest()[:12], "pr_head": hashlib.sha256(head.encode()).hexdigest()[:12]},
        }
    report["other_files_main_propose_vs_pr"] = files
    names = subprocess.run(["git", "diff", "--name-status", args.main, args.head], cwd=repo, capture_output=True, text=True, check=True).stdout.split("\n")  # nosec B603 B607
    report["pr_files"] = [line for line in names if line]
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1)[:9000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
