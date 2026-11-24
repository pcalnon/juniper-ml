"""
Check the D-14 carriers' landing texts against their trees and the arc's text rules.

1. Each block of ``tmp/flood4-fix/d14-resume/changelog_entry.txt`` (headed ``== <file>: under ... ### <Group> ... ==``)
   occurs verbatim in that file of the carrier tree, below its top ``## [Unreleased]`` and above the next ``## [``
   heading, and the nearest ``### `` heading above it is the group the header names.
2. ``pr_title.txt``, ``pr_body.txt``, ``commit_body.txt`` and ``changelog_entry.txt``: no CI-skip marker; no ruling
   cited by a number; none of the words that name the arc's own reviewers or sessions; ``<SIBLING-PR>`` in the PR
   body; the PR body's first line is ``TITLE: `` + ``pr_title.txt``; every ``#N`` / ``<repo>#N`` reference is listed
   for a reader to confirm.

Usage:
    python3 util/ad-hoc/2026-11-16_flood4r2_d14_texts_check.py --carrier <root> [--carrier <root> ...] --out <json>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRATCH = Path("tmp/flood4-fix/d14-resume")
HEADER = re.compile(r"^== (?P<file>\S+): under (?P<where>.*?) ==$", re.M)
SKIP_MARKERS = ("[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]", "skip-checks: true", "skip-checks:true")
FORBIDDEN = re.compile(r"\b(MN1|MN2|lens|validator|orchestrator|session \d+|builder M2?)\b", re.I)
RULING_NUMBER = re.compile(r"\bruling (?:no\.? ?)?\d+\b|\brulings? \d+(?:,| and) \d+", re.I)
REFERENCE = re.compile(r"(?:[a-z-]+)?#\d+")


def check_changelog(root: Path) -> list[dict]:
    text = (root / SCRATCH / "changelog_entry.txt").read_text(encoding="utf-8")
    headers = list(HEADER.finditer(text))
    rows = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        block = text[header.end() + 1 : end].rstrip("\n") + "\n"
        target = (root / header["file"]).read_text(encoding="utf-8")
        position = target.find(block)
        group = re.search(r"### (\w+)", header["where"])
        row = {"file": header["file"], "found": position >= 0, "occurrences": target.count(block)}
        if position >= 0:
            top = target.find("## [Unreleased]")
            next_release = target.find("\n## [", top + 1)
            above = target[:position]
            nearest = re.findall(r"^### (\w+)", above, re.M)
            row.update(under_top_unreleased=top >= 0 and top < position and (next_release < 0 or position < next_release), group=nearest[-1] if nearest else None, group_expected=group.group(1) if group else None)
            row["ok"] = row["occurrences"] == 1 and row["under_top_unreleased"] and row["group"] == row["group_expected"]
        else:
            row["ok"] = False
        rows.append(row)
    return rows


def check_texts(root: Path) -> dict:
    scratch = root / SCRATCH
    title = (scratch / "pr_title.txt").read_text(encoding="utf-8").strip()
    texts = {name: (scratch / name).read_text(encoding="utf-8") for name in ("pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt")}
    result = {"title_line_matches": texts["pr_body.txt"].splitlines()[0] == f"TITLE: {title}", "sibling_token": "<SIBLING-PR>" in texts["pr_body.txt"], "problems": [], "references": {}}
    for name, text in texts.items():
        lowered = text.lower()
        result["problems"] += [f"{name}: CI-skip marker {marker!r}" for marker in SKIP_MARKERS if marker in lowered]
        result["problems"] += [f"{name}: {match.group(0)!r}" for match in FORBIDDEN.finditer(text)]
        result["problems"] += [f"{name}: ruling by number {match.group(0)!r}" for match in RULING_NUMBER.finditer(text)]
        result["references"][name] = sorted(set(REFERENCE.findall(text)))
    result["ok"] = result["title_line_matches"] and result["sibling_token"] and not result["problems"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--carrier", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = {}
    for root in args.carrier:
        report[str(root)] = {"changelog": check_changelog(root), "texts": check_texts(root)}
    ok = all(all(row["ok"] for row in item["changelog"]) and item["texts"]["ok"] for item in report.values())
    report["ok"] = ok
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
