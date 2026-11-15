#!/usr/bin/env python3
"""
Which release's pins does each row of docs/REFERENCE.md's compatibility matrix hold: the first it covers, or the last?

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (round 3 of the ml-propose carrier, flood-4 session 5; final-check finding F8)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
The co-change checklist's REVIEW note asked the reviewer, on a new series, to "restore the pins that series
published". A series' patches can publish different floors (0.11.0 published juniper-data>=0.17.0 and 0.11.2
>=0.17.1), so the note did not say which release's pins. The code answers it: a patch rewrites its series' row in
place, so the row holds the pins of the last release proposed in the series. This script checks the release
history against that reading. It reads the matrix from docs/REFERENCE.md AT A RELEASE TAG (the newest `v*` tag
unless --reference-ref names another ref, or WORKTREE for the file on disk), so the answer does not move when a
later floor raise rewrites the current row on main. For every `v*` tag it reads pyproject.toml at the tag
(`git show`) and takes each matrix column's spec with propose.meta_reference_pins. A row covers the releases from
its own series up to the next row's series (the 0.6.x row covers 0.7.x: there is no 0.7.x row).

Read-only. Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3_series_row_history.py --out <scratch>/series_row_history.json
                                                                             [--reference-ref <ref>|WORKTREE]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only git plumbing in this script's own worktree
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "util" / "release_train"))

import propose  # noqa: E402 - the worktree's copy, importable only after the path insert

TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
LABEL = re.compile(r"^(\d+)\.(\d+)\.x$")


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)  # nosec B603 B607


def release_tags() -> list:
    """Every ``vN.N.N`` tag as ``((major, minor, patch), name)``, oldest first."""
    found = []
    for name in git("tag", "-l", "v*").stdout.split():
        m = TAG.match(name)
        if m:
            found.append((tuple(int(part) for part in m.groups()), name))
    return sorted(found)


def matrix_rows(reference: str) -> "tuple[list, dict]":
    lines = reference.splitlines(keepends=True)
    located = propose._reference_matrix(lines)
    if located is None:
        raise SystemExit("docs/REFERENCE.md: compatibility matrix not found")
    header_idx, rows = located
    header = propose._table_cells(lines[header_idx])
    table = {}
    for i in rows:
        cells = propose._table_cells(lines[i])
        table[cells[0]] = dict(zip(header[1:], cells[1:]))
    return header[1:], table


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--reference-ref", help="read docs/REFERENCE.md at this ref (default: the newest v* tag; WORKTREE = the file on disk)")
    args = parser.parse_args()
    tags = release_tags()
    if not tags:
        raise SystemExit("no v* release tags in this checkout")
    reference_ref = args.reference_ref or tags[-1][1]
    if reference_ref == "WORKTREE":
        reference = (ROOT / "docs" / "REFERENCE.md").read_text(encoding="utf-8")
    else:
        shown = git("show", f"{reference_ref}:docs/REFERENCE.md")
        if shown.returncode != 0:
            raise SystemExit(f"cannot read docs/REFERENCE.md at {reference_ref}")
        reference = shown.stdout
    columns, table = matrix_rows(reference)
    published = {}
    for _, tag in tags:
        shown = git("show", f"{tag}:pyproject.toml")
        if shown.returncode == 0:
            _, specs, _ = propose.meta_reference_pins(shown.stdout)
            published[tag] = {pkg: specs.get(pkg) for pkg in columns}
    labels = sorted((tuple(int(part) for part in LABEL.match(label).groups()), label) for label in table if LABEL.match(label))
    report = {"reference_ref": reference_ref, "columns": columns, "rows": {}, "published": published}
    for index, (key, label) in enumerate(labels):
        upper = labels[index + 1][0] if index + 1 < len(labels) else None
        covered = [tag for version, tag in tags if tag in published and version[:2] >= key and (upper is None or version[:2] < upper)]
        cells = table[label]
        equal = [tag for tag in covered if published[tag] == cells]
        report["rows"][label] = {
            "cells": cells,
            "releases_covered": covered,
            "releases_the_row_equals": equal,
            "equals_first": bool(covered) and covered[0] in equal,
            "equals_last": bool(covered) and covered[-1] in equal,
            "releases_that_differ": {tag: {pkg: {"published": published[tag].get(pkg), "row": cells[pkg]} for pkg in columns if published[tag].get(pkg) != cells[pkg]} for tag in covered if published[tag] != cells},
        }
    multi = {label: row for label, row in report["rows"].items() if len({json.dumps(published[tag], sort_keys=True) for tag in row["releases_covered"]}) > 1}
    report["rows_whose_releases_published_different_pins"] = sorted(multi)
    report["every_such_row_equals_its_last_release_and_not_its_first"] = bool(multi) and all(row["equals_last"] and not row["equals_first"] for row in multi.values())
    report["every_row_equals_its_last_release"] = all(row["equals_last"] for row in report["rows"].values() if row["releases_covered"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"docs/REFERENCE.md read at {reference_ref}")
    for label, row in report["rows"].items():
        print(f"{label:8s} covers={row['releases_covered']} row==first:{row['equals_first']} row==last:{row['equals_last']} equal_to={row['releases_the_row_equals']}")
        for tag, diff in row["releases_that_differ"].items():
            print(f"          {tag} differs: {diff}")
    print(f"rows whose releases published different pins: {report['rows_whose_releases_published_different_pins']}")
    print(f"every such row equals its last release and not its first: {report['every_such_row_equals_its_last_release_and_not_its_first']}")
    print(f"every row equals its last release: {report['every_row_equals_its_last_release']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
