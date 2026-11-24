#!/usr/bin/env python3
"""
Carry the juniper-cascor ruling-10 port's ci.yml and CHANGELOG.md onto a main that moved, three-way, never by copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-cascor)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         juniper-cascor#760 (merged while the port was being built: ci.yml's unit-tests job, CHANGELOG.md)

WHY THIS EXISTS
The port was built on juniper-cascor main f97ea0c5; main then gained #760, which edits two of the port's files. The
brief's rule is a three-way rebuild (`git merge-file -p <carrier> <base> <main>`), never the carrier's copy over
main's. ci.yml merges cleanly (the port edits the security job, #760 the unit-tests job). CHANGELOG.md cannot merge
cleanly: both insert a `### Fixed` heading at the same line under `## [Unreleased]`. Main's heading is kept, and the
port's entry, without its own heading, goes BELOW #760's entry (base brief rule 9), so the result has one
`### Fixed`. Every input and output is hashed; nothing is written but the two carrier files and --out.

Usage:
  python3 <this> --carrier <port worktree> --base-tree <checkout at the old base> --main-ref origin/main
      --entry <changelog_entry.txt> --out <dir>

Run AFTER the carrier's HEAD has been moved to the new main (`git reset --mixed`), so `--main-ref` and the carrier
agree. Exit 0 = ci.yml merged with no conflict and CHANGELOG.md holds exactly one `### Fixed` under
`## [Unreleased]` with main's entry first; 1 otherwise (nothing is written then).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv: git show and git merge-file on files this script names
import sys
from pathlib import Path

CI = ".github/workflows/ci.yml"
CHANGELOG = "CHANGELOG.md"
NEXT_RELEASE = "## [0.14.0] - 2026-11-15"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def show(repo: Path, ref: str, rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel}"], capture_output=True, check=True).stdout  # nosec B603 B607


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--carrier", required=True, type=Path)
    ap.add_argument("--base-tree", required=True, type=Path)
    ap.add_argument("--main-ref", default="origin/main")
    ap.add_argument("--entry", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    record: dict = {"main_ref": args.main_ref, "files": {}}

    # ci.yml: a plain three-way merge.
    carrier_ci = (args.carrier / CI).read_bytes()
    base_ci = (args.base_tree / CI).read_bytes()
    main_ci = show(args.carrier, args.main_ref, CI)
    for name, data in (("carrier", carrier_ci), ("base", base_ci), ("main", main_ci)):
        (out / f"ci.{name}.yml").write_bytes(data)
    merged = subprocess.run(["git", "merge-file", "-p", str(out / "ci.carrier.yml"), str(out / "ci.base.yml"), str(out / "ci.main.yml")], capture_output=True, check=False)  # nosec B603 B607
    record["files"][CI] = {"carrier": sha(carrier_ci), "base": sha(base_ci), "main": sha(main_ci), "conflicts": merged.returncode, "merged": sha(merged.stdout)}
    if merged.returncode != 0:
        print(f"{CI}: {merged.returncode} conflict(s); nothing written")
        (out / "rebase.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
        return 1

    # CHANGELOG.md: main's text, with the port's entry (heading dropped) appended to main's own [Unreleased] ### Fixed.
    main_log = show(args.carrier, args.main_ref, CHANGELOG).decode("utf-8")
    entry_lines = args.entry.read_text(encoding="utf-8").splitlines(keepends=True)
    if not entry_lines or entry_lines[0].strip() != "### Fixed":
        print("the entry file does not start with its ### Fixed heading")
        return 1
    body = "".join(entry_lines[1:]).strip("\n") + "\n"
    head, sep, tail = main_log.partition(NEXT_RELEASE)
    unreleased = head.split("## [Unreleased]", 1)
    if not sep or len(unreleased) != 2 or unreleased[1].count("\n### Fixed\n") != 1:
        print("main's CHANGELOG.md does not hold exactly one ### Fixed under ## [Unreleased] before the next release heading")
        return 1
    new_log = head.rstrip("\n") + "\n" + body + "\n" + sep + tail
    record["files"][CHANGELOG] = {"carrier": sha((args.carrier / CHANGELOG).read_bytes()), "main": sha(main_log.encode("utf-8")), "entry": sha(args.entry.read_bytes()), "result": sha(new_log.encode("utf-8"))}

    (args.carrier / CI).write_bytes(merged.stdout)
    (args.carrier / CHANGELOG).write_text(new_log, encoding="utf-8")
    (out / "rebase.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
