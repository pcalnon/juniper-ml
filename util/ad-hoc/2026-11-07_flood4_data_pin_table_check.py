#!/usr/bin/env python3
"""
Compare juniper-data's CICD_REFERENCE.md "GitHub Actions Pinned Versions" table with the workflows' real pins.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data docs carrier)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#509 (left a stale setup-python v7.0.0 row); flood-4 common brief

juniper-data#509 set the claude-code-action row to v1.0.265 and wrote "the other rows are unchanged from that
2026-10-29 derivation", leaving `actions/setup-python` at v7.0.0 although #507 moved every workflow to v7.1.0.
This re-derives every row from `.github/workflows/*.yml` (the `uses: owner/repo@<sha> # vX.Y.Z` lines) and
prints each disagreement: version, SHA, or the set of workflow files.

    python3 2026-11-07_flood4_data_pin_table_check.py <juniper-data worktree>

Exit 0 when the table matches, 1 when any row disagrees or an action is missing from either side.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

USES = re.compile(r"uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+)@([0-9a-f]{40})\s*#\s*(v[0-9][^\s]*)")
ROW = re.compile(r"^\|\s*`([^`]+)`(?:\s*\(([^)]*)\))?\s*\|\s*(v[^|\s]+)\s*\|\s*`([0-9a-f]{40})`\s*\|\s*(.+?)\s*\|\s*$")
# A combined row such as `github/codeql-action/*` (`init`, `autobuild`, `analyze`, `upload-sarif`) names its
# sub-actions in parentheses, and its "Used in" cell says which file each sits in ("`codeql.yml`; `upload-sarif`
# in `ci.yml`"). Each sub-action is compared on version and SHA; the files are compared as the union.


def workflow_pins(root: Path) -> dict[str, dict[str, set[str]]]:
    pins: dict[str, dict[str, set[str]]] = {}
    for path in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        for line in path.read_text(encoding="utf-8").splitlines():
            m = USES.search(line)
            if not m:
                continue
            action, sha, version = m.groups()
            entry = pins.setdefault(action, {"versions": set(), "shas": set(), "files": set()})
            entry["versions"].add(version)
            entry["shas"].add(sha)
            entry["files"].add(path.name)
    return pins


def table_rows(root: Path) -> tuple[dict[str, tuple[str, str, set[str]]], list[tuple[list[str], set[str]]]]:
    text = (root / "docs" / "ci_cd" / "CICD_REFERENCE.md").read_text(encoding="utf-8")
    section = text.split("## GitHub Actions Pinned Versions", 1)[1].split("\n## ", 1)[0]
    rows: dict[str, tuple[str, str, set[str]]] = {}
    combined: list[tuple[list[str], set[str]]] = []
    for line in section.splitlines():
        m = ROW.match(line)
        if not m:
            continue
        action, subs, version, sha, used = m.groups()
        files = set(re.findall(r"`([^`]+\.ya?ml)`", used))
        if action.endswith("/*") and subs:
            names = [f"{action[:-2]}/{sub}" for sub in re.findall(r"`([^`]+)`", subs)]
            for name in names:
                rows[name] = (version, sha, set())
            combined.append((names, files))
        else:
            rows[action] = (version, sha, files)
    return rows, combined


def main(argv: list[str]) -> int:
    root = Path(argv[1])
    pins = workflow_pins(root)
    rows, combined = table_rows(root)
    bad = 0
    for names, files in combined:
        union = set().union(*(pins.get(name, {"files": set()})["files"] for name in names))
        if union != files:
            bad += 1
            print(f"DIFF {names}: files table={sorted(files)} workflows={sorted(union)}")
        else:
            print(f"OK   combined row {names}: files {sorted(files)}")
    combined_names = {name for names, _files in combined for name in names}
    for action in sorted(set(pins) | set(rows)):
        if action not in rows:
            print(f"MISSING-ROW {action}: workflows pin {sorted(pins[action]['versions'])} {sorted(pins[action]['shas'])} in {sorted(pins[action]['files'])}")
            bad += 1
            continue
        if action not in pins:
            print(f"STALE-ROW {action}: no workflow pins it")
            bad += 1
            continue
        version, sha, files = rows[action]
        p = pins[action]
        problems = []
        if p["versions"] != {version}:
            problems.append(f"version table={version} workflows={sorted(p['versions'])}")
        if p["shas"] != {sha}:
            problems.append(f"sha table={sha} workflows={sorted(p['shas'])}")
        if action not in combined_names and p["files"] != files:
            problems.append(f"files table={sorted(files)} workflows={sorted(p['files'])}")
        if problems:
            bad += 1
            print(f"DIFF {action}: " + "; ".join(problems))
        else:
            print(f"OK   {action} {version} {sha[:12]} {sorted(files)}")
    print(f"rows={len(rows)} pinned_actions={len(pins)} disagreements={bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
