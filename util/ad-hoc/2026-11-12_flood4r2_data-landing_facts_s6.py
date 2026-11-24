#!/usr/bin/env python3
"""
Re-derive, on juniper-data's main and on the stage-3 carrier, the facts stage 3's PR texts and stamps cite.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: finishing juniper-data's stage-3 carrier, session 6)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (stages 1 and 2 merged, so "main" is a new commit: every cited line and count is re-read)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: 2026-11-11_flood4r2_data-landing_facts.py (the same idea for three stages on the older main);
         notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    python3 <this> --repo <juniper-data primary> --main <commit> --older <commit> [--older ...]
                   --carrier <stage-3 worktree> --date-long "November 13, 2026" --date-iso 2026-11-13 --out <json>

Facts (read-only: git rev-parse, show and grep on commits; file reads in the carrier):
  - the blob ids of juniper_data/api/security.py and middleware.py at --main and at each --older commit;
  - main's security.py lines the PR body cites as the defect, and the carrier's lines it cites as the fix;
  - how many test files under juniper_data/tests declare a module-level ``pytestmark`` at --main and in the carrier.
    The count's scope is that one directory, in a commit or in the carrier: no ``tmp/`` is searched;
  - every stamp site of docs/REFERENCE.md and docs/DEVELOPER_CHEATSHEET.md: main's line, the carrier's line, and
    whether the carrier's is main's version plus one patch step, dated --date-long / --date-iso, header == footer;
  - whether either doc holds a Version History table;
  - CHANGELOG.md: the release headings, and where the carrier's added lines sit.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only git queries
import sys
from pathlib import Path

SECURITY = "juniper_data/api/security.py"
MIDDLEWARE = "juniper_data/api/middleware.py"
REFERENCE = "docs/REFERENCE.md"
CHEATSHEET = "docs/DEVELOPER_CHEATSHEET.md"
PYTESTMARK = re.compile(r"^pytestmark\b", re.MULTILINE)
VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def _git(repo: Path, *argv: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *argv], capture_output=True, text=True, check=True).stdout  # nosec B603 B607


def _line(text: str, number: int) -> str:
    return text.split("\n")[number - 1]


def _numbered(text: str, needle: re.Pattern) -> list[dict]:
    return [{"line": number, "text": line} for number, line in enumerate(text.split("\n"), 1) if needle.search(line)]


def _next_patch(line: str) -> str | None:
    found = VERSION.search(line)
    if not found:
        return None
    major, minor, patch = (int(part) for part in found.groups())
    return f"{major}.{minor}.{patch + 1}"


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--main", required=True)
    ap.add_argument("--older", action="append", default=[])
    ap.add_argument("--carrier", type=Path, required=True)
    ap.add_argument("--date-long", required=True)
    ap.add_argument("--date-iso", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    carrier = args.carrier.resolve()
    main_sha = _git(repo, "rev-parse", args.main).strip()
    facts: dict = {"main": main_sha, "carrier": str(carrier)}

    facts["blobs"] = {path: {ref: _git(repo, "rev-parse", f"{ref}:{path}").strip() for ref in (*args.older, main_sha)} for path in (SECURITY, MIDDLEWARE)}
    facts["blob_unchanged_from_the_older_commits_to_main"] = {path: len(set(ids.values())) == 1 for path, ids in facts["blobs"].items()}

    main_security = _git(repo, "show", f"{main_sha}:{SECURITY}")
    facts["security_py_at_main"] = {str(number): _line(main_security, number).strip() for number in (250, 251, 254, 427)}
    carrier_security = (carrier / SECURITY).read_text(encoding="utf-8")
    carrier_middleware = (carrier / MIDDLEWARE).read_text(encoding="utf-8")
    facts["carrier_cited_lines"] = {
        **{f"security.py:{number}": _line(carrier_security, number).strip() for number in (220, 243, 276, 279, 318, 323, 327, 328, 458)},
        **{f"middleware.py:{number}": _line(carrier_middleware, number).strip() for number in (205, 206, 225, 233)},
    }
    facts["carrier_middleware_equals_main"] = carrier_middleware == _git(repo, "show", f"{main_sha}:{MIDDLEWARE}")

    at_main = [line.split(":", 1)[1] for line in _git(repo, "grep", "-l", "-E", "^pytestmark", main_sha, "--", "juniper_data/tests").splitlines()]
    in_carrier = sorted(str(path.relative_to(carrier)) for path in (carrier / "juniper_data" / "tests").rglob("test_*.py") if PYTESTMARK.search(path.read_text(encoding="utf-8")))
    facts["pytestmark_files"] = {"scope": "juniper_data/tests only", "at_main": len(at_main), "in_carrier": len(in_carrier), "carrier_beyond_main": sorted(set(in_carrier) - set(at_main)), "main_beyond_carrier": sorted(set(at_main) - set(in_carrier))}

    stamp = re.compile(r"^\*\*(Version|Last Updated|Date)\b")
    sites = []
    for path in (REFERENCE, CHEATSHEET):
        main_text = _git(repo, "show", f"{main_sha}:{path}")
        carrier_text = (carrier / path).read_text(encoding="utf-8")
        main_sites = _numbered(main_text, stamp)
        carrier_sites = _numbered(carrier_text, stamp)
        facts.setdefault("version_history_table", {})[path] = bool(re.search(r"(?im)^#+\s*version history", carrier_text))
        for index, site in enumerate(carrier_sites):
            before = main_sites[index]["text"] if index < len(main_sites) else None
            row = {"path": path, "line": site["line"], "main_line": main_sites[index]["line"] if index < len(main_sites) else None, "main_value": before, "carrier_value": site["text"]}
            if "Version" in site["text"]:
                row["version_is_main_plus_one_patch_step"] = before is not None and (_next_patch(before) or "") in site["text"]
            if "Last Updated" in site["text"]:
                row["dated_the_landing_day"] = args.date_long in site["text"]
            if "**Date**" in site["text"]:
                row["dated_the_landing_day"] = args.date_iso in site["text"]
            sites.append(row)
        facts.setdefault("stamp_site_counts", {})[path] = {"main": len(main_sites), "carrier": len(carrier_sites)}
    facts["stamp_sites"] = sites
    reference_sites = [site for site in sites if site["path"] == REFERENCE]
    facts["reference_header_equals_footer"] = {
        "version": len({VERSION.search(site["carrier_value"]).group(0) for site in reference_sites if site["carrier_value"].startswith("**Version")}) == 1,
        "date": len({site["carrier_value"] for site in reference_sites if "Last Updated" in site["carrier_value"]}) == 1,
    }

    main_changelog = _git(repo, "show", f"{main_sha}:CHANGELOG.md")
    carrier_changelog = (carrier / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = _numbered(carrier_changelog, re.compile(r"^## \["))
    matcher = difflib.SequenceMatcher(a=main_changelog.split("\n"), b=carrier_changelog.split("\n"), autojunk=False)
    blocks = [{"op": op, "main_lines": [a1 + 1, a2], "carrier_lines": [b1 + 1, b2]} for op, a1, a2, b1, b2 in matcher.get_opcodes() if op != "equal"]
    section = None
    if blocks:
        for number in range(blocks[0]["carrier_lines"][0], 0, -1):
            if _line(carrier_changelog, number).startswith("### "):
                section = {"line": number, "text": _line(carrier_changelog, number)}
                break
    facts["changelog"] = {
        "first_release_headings": headings[:2],
        "blocks_that_differ_from_main": blocks,
        "one_pure_insertion": len(blocks) == 1 and blocks[0]["op"] == "insert",
        "subsection_above_the_insertion": section,
        "insertion_is_under_the_top_heading": bool(blocks) and len(headings) > 1 and headings[0]["line"] < blocks[0]["carrier_lines"][0] < headings[1]["line"],
        "date_strings_in_the_inserted_lines": sorted(set(re.findall(r"20\d\d-\d\d-\d\d|(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, 20\d\d", "\n".join(carrier_changelog.split("\n")[blocks[0]["carrier_lines"][0] - 1 : blocks[0]["carrier_lines"][1]])))) if blocks else [],
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(facts, fh, indent=1)
        fh.write("\n")
    print(json.dumps(facts, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
