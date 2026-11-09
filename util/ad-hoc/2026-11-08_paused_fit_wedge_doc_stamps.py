#!/usr/bin/env python3
"""Re-derive the paused-fit wedge fix's four doc stamps from main's values, check them, or apply them.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use rebase aid)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-08
Status:      ad-hoc -- one-off rebase aid
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     the "paused-fit wedge", §4 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

The fix bumps the header and footer stamps of ``docs/REFERENCE.md``,
``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md``, ``docs/QUICK_START.md`` and
``docs/DOCUMENTATION_OVERVIEW.md``: each ``**Version**`` line gets main's patch number plus one,
and each ``**Last Updated**`` / ``**Date**`` line gets ``--date``. A rebase onto a newer main
conflicts on exactly those lines; take main's side there, then run this with ``--apply`` to redo
the bump from main's new values. Main's copies come from ``--main-dir`` (one file per doc,
named by its basename) or from ``git show <--main-ref>:<doc>``.

Exit status: 0 when every stamp equals its re-derived value (after ``--apply``, if given), 1 when
one does not, 2 on a usage or setup error (a doc whose stamp lines differ in kind or number from
main's, a ref or file that cannot be read).

Usage (from the juniper-ml worktree root):
    python3 util/ad-hoc/2026-11-08_paused_fit_wedge_doc_stamps.py --main-ref origin/main --date 2026-11-08 [--apply] [--json-out <file>]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = ("docs/REFERENCE.md", "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "docs/QUICK_START.md", "docs/DOCUMENTATION_OVERVIEW.md")
# Both stamp spellings the four docs use: ``**Version:** 0.6.64`` and ``**Version**: 1.0.64``.
STAMP = re.compile(r"^(\*\*(Version|Last Updated|Date)(?::\*\*|\*\*:) )(\S+)(\s*)$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class SetupError(Exception):
    """The stamps could not be derived; nothing below would mean anything."""


def _main_text(doc: str, main_dir: Path | None, main_ref: str | None) -> str:
    if main_dir is not None:
        path = main_dir / Path(doc).name
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise SetupError(f"cannot read {path}: {exc}") from exc
    result = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{main_ref}:{doc}"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SetupError(f"git show {main_ref}:{doc} failed: {result.stderr.strip()}")
    return result.stdout


def _stamps(lines: list[str]) -> list[tuple[int, str, str]]:
    """(0-based line index, field, value) for every stamp line, in file order."""
    return [(i, m.group(2), m.group(3)) for i, line in enumerate(lines) if (m := STAMP.match(line))]


def _rederive(field: str, main_value: str, date: str) -> str:
    if field != "Version":
        return date
    parts = main_value.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise SetupError(f"main's version {main_value!r} is not MAJOR.MINOR.PATCH")
    return f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"


def _sites(args: argparse.Namespace) -> list[dict]:
    sites = []
    for doc in DOCS:
        main_stamps = _stamps(_main_text(doc, args.main_dir, args.main_ref).splitlines())
        path = REPO_ROOT / doc
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        here = _stamps([line.rstrip("\n") for line in lines])
        if [field for _, field, _ in main_stamps] != [field for _, field, _ in here]:
            raise SetupError(f"{doc}: stamp lines {[f for _, f, _ in here]} differ from main's {[f for _, f, _ in main_stamps]}")
        changed = False
        for (main_index, field, main_value), (index, _, value) in zip(main_stamps, here, strict=True):
            new = _rederive(field, main_value, args.date)
            if args.apply and value != new:
                match = STAMP.match(lines[index].rstrip("\n"))
                lines[index] = f"{match.group(1)}{new}{match.group(4)}\n"
                value, changed = new, True
            sites.append({"file": doc, "field": field, "main_line": main_index + 1, "line": index + 1, "old": main_value, "new": new, "in_file": value, "matches": value == new})
        if changed:
            path.write_text("".join(lines), encoding="utf-8")
    return sites


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--main-dir", type=Path, help="a directory holding main's copy of each doc, named by its basename")
    source.add_argument("--main-ref", help="a ref to read main's docs from with git show (e.g. origin/main)")
    parser.add_argument("--date", required=True, help="the date the stamps carry, YYYY-MM-DD")
    parser.add_argument("--apply", action="store_true", help="rewrite each stamp line that differs from its re-derived value")
    parser.add_argument("--json-out", type=Path, help="also write every stamp site to this JSON file")
    args = parser.parse_args(argv)
    if not DATE.match(args.date):
        parser.error("--date takes YYYY-MM-DD")

    try:
        sites = _sites(args)
    except SetupError as exc:
        print(f"setup error: {exc}", file=sys.stderr)
        return 2

    for site in sites:
        verdict = "OK" if site["matches"] else "MISMATCH"
        print(f"{site['file']}:{site['line']}\t{site['field']}\t{site['old']} -> {site['new']}\t{verdict}")
    if args.json_out is not None:
        reference_version = next(site["new"] for site in sites if site["file"] == "docs/REFERENCE.md" and site["field"] == "Version")
        payload = {
            "rule": "a Version gets main's patch number plus one; a Last Updated / Date gets --date",
            "main": str(args.main_dir) if args.main_dir is not None else args.main_ref,
            "date": args.date,
            "sites": sites,
            "not_a_stamp_but_renumber_too": f"docs/REFERENCE.md's version-history table has a row for this change; its version must equal the re-derived header Version ({reference_version} here)",
        }
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1)
            fh.write("\n")
    mismatches = sum(1 for site in sites if not site["matches"])
    print(f"RESULT: {len(sites) - mismatches}/{len(sites)} stamps as re-derived")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
