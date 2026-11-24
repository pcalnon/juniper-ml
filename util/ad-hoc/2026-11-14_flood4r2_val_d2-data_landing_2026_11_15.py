#!/usr/bin/env python3
"""
Build the 2026-11-15 landing of juniper-data's "run the unrun tests" carrier on main 3cf8867c: stage the pre-fix
copies, generate the stamps.json text fixes for the new landing day, and check every stamp site after the fixes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (Cursor flood-4 session 8: finishing the d2-unrun-tests validation after VF was cut off)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_val_d2-data_text_fixes.py (applies and checks the fixes this feeds),
         util/ad-hoc/2026-11-12_flood4r2_val_d2-data_lay_over.py (VF's three-way and stamp-by-rule)

Verbs:
  copies --out <dir>
      The five documents the landing changes, BEFORE the 2026-11-15 fixes: the carrier's AGENTS.md and two testing
      documents, and VF's three-way CHANGELOG.md and docs/REFERENCE.md (stamp 0.4.9 set by rule). Each copy must
      carry the sha256 VF's V1 lay-over recorded (landing/V1_landed.json).
  stamps-fixes --hand <json> --out <json>
      Appends to the hand-written fixes one exact fix per changed region of the carrier's stamps.json, so that the
      fixed file describes a landing on 2026-11-15 on main 3cf8867c. Every old is a slice of the file itself.
  check --fixed <dir> --main-tree <V1>
      Every site of the fixed stamps.json must equal its line in the fixed copy; the Version is main's value plus
      one patch step (main read from the tree's HEAD commit); header equals footer; every date is the landing day.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

WORKTREES = Path.home() / "Development" / "python" / "Juniper" / "worktrees"
CARRIER = WORKTREES / "juniper-data--test--run-the-unrun-tests--20261112-1815--c68e6b4c"
STAMPS = CARRIER / "tmp" / "flood4-fix" / "d2-unrun-tests" / "stamps.json"
SCRATCH = Path(__file__).resolve().parents[2] / "tmp" / "flood4r2-val" / "d2-unrun-tests-s7"
MAIN_SHA = "3cf8867cdbcf487483161cf25f4f084884b17d12"
LANDING_ISO, LANDING_LONG = "2026-11-15", "November 15, 2026"
SOURCES = {
    "AGENTS.md": CARRIER / "AGENTS.md",
    "CHANGELOG.md": SCRATCH / "proposed" / "landing_on_main__VF_2026-11-13" / "CHANGELOG.md",
    "docs/REFERENCE.md": SCRATCH / "proposed" / "landing_on_main__VF_2026-11-13" / "docs" / "REFERENCE.md",
    "docs/testing/TESTING_MANUAL.md": CARRIER / "docs" / "testing" / "TESTING_MANUAL.md",
    "docs/testing/TESTING_REFERENCE.md": CARRIER / "docs" / "testing" / "TESTING_REFERENCE.md",
}
NEW_RE_DERIVE = (
    "Read main's value at the same site when the change is rebuilt on a newer main, add one patch step, and set the date "
    "to the landing day. The Retry-After change has landed (juniper-data#537, main 3cf8867c): docs/REFERENCE.md on main "
    "reads 0.4.8 and this change's value is 0.4.9. The three-way of that file merges without a conflict and keeps main's "
    "0.4.8, so the value is set by this rule, not by the merge. If juniper-data#538 (open on 2026-11-15) lands first, "
    "main reads 0.4.9 dated November 14, 2026 and this change's value becomes 0.4.10."
)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(obj: object) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False) + "\n"


def verb_copies(ns: argparse.Namespace) -> int:
    landed = {row["path"]: row["sha256"] for row in json.loads((SCRATCH / "landing" / "V1_landed.json").read_text(encoding="utf-8"))["applied"]}
    out = Path(ns.out)
    for name, source in SOURCES.items():
        if sha256_of(source) != landed[name]:
            raise SystemExit(f"{source} is {sha256_of(source)}, V1_landed.json says {landed[name]}")
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, out / name)
        print(f"staged {name} sha256 {landed[name][:12]} (= V1_landed.json)")
    return 0


def new_stamps(old: dict) -> dict:
    new = json.loads(json.dumps(old))
    new["landing_date_utc"] = LANDING_ISO
    new["re_derive"] = NEW_RE_DERIVE
    new["base"] = MAIN_SHA
    lines = {"docs/REFERENCE.md": {2708: 2709, 2709: 2710}}
    for document in new["documents"]:
        for site in document["sites"]:
            site["line"] = lines.get(document["path"], {}).get(site["line"], site["line"])
            if document["path"] == "docs/REFERENCE.md" and site["field"] == "Version":
                site.update({"text": "**Version:** 0.4.9", "value": "0.4.9", "main_value": "0.4.8"})
            if site["field"] == "Last Updated" and site["changed"]:
                iso = document["path"] == "AGENTS.md"
                value = LANDING_ISO if iso else LANDING_LONG
                site.update({"text": f"**Last Updated**: {value}" if iso else f"**Last Updated:** {value}", "value": value})
                if document["path"] == "docs/REFERENCE.md":
                    site["main_value"] = "November 13, 2026"
    new["date_sites_outside_stamps"][0] = new["date_sites_outside_stamps"][0].replace("main 'c68e6b4c'", "main '3cf8867c'")
    return new


def verb_stamps_fixes(ns: argparse.Namespace) -> int:
    text = STAMPS.read_text(encoding="utf-8")
    old = json.loads(text)
    if dump(old) != text:
        raise SystemExit("stamps.json is not json.dumps(indent=1): the slices below would not be slices of the file")
    new = new_stamps(old)
    fixes = json.loads(Path(ns.hand).read_text(encoding="utf-8"))
    for key in ("landing_date_utc", "re_derive", "base"):
        fixes.append({"finding": "F7" if key == "landing_date_utc" else "F1" if key == "re_derive" else "F2", "file": "DELIVERABLES/stamps.json", "old": f'"{key}": {json.dumps(old[key], ensure_ascii=False)}', "new": f'"{key}": {json.dumps(new[key], ensure_ascii=False)}'})
    for before, after in zip(old["documents"], new["documents"]):
        if before != after:
            fixes.append({"finding": "F7", "file": "DELIVERABLES/stamps.json", "old": json.dumps(before, indent=1, ensure_ascii=False).replace("\n", "\n  "), "new": json.dumps(after, indent=1, ensure_ascii=False).replace("\n", "\n  ")})
    fixes.append({"finding": "F2", "file": "DELIVERABLES/stamps.json", "old": json.dumps(old["date_sites_outside_stamps"][0], ensure_ascii=False), "new": json.dumps(new["date_sites_outside_stamps"][0], ensure_ascii=False)})
    Path(ns.out).write_text(json.dumps(fixes, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    applied = text
    for fix in fixes:
        if fix["file"] == "DELIVERABLES/stamps.json":
            if applied.count(fix["old"]) != 1:
                raise SystemExit(f"stamps fix does not occur once: {fix['old'][:80]!r}")
            applied = applied.replace(fix["old"], fix["new"])
    if applied != dump(new):
        raise SystemExit("the stamps.json fixes do not reproduce the intended file")
    print(f"{len(fixes)} fixes written; the stamps.json ones reproduce the intended file exactly")
    return 0


def main_value(tree: Path, name: str, line: int) -> str:
    text = subprocess.run(["git", "-C", str(tree), "show", f"HEAD:{name}"], capture_output=True, text=True, check=True).stdout
    return text.splitlines()[line - 1]


def verb_check(ns: argparse.Namespace) -> int:
    fixed, tree = Path(ns.fixed), Path(ns.main_tree)
    stamps = json.loads((fixed / "DELIVERABLES" / "stamps.json").read_text(encoding="utf-8"))
    problems = []
    if stamps["landing_date_utc"] != LANDING_ISO or stamps["base"] != MAIN_SHA:
        problems.append("landing_date_utc or base")
    for document in stamps["documents"]:
        lines = (fixed / "COPY" / document["path"]).read_text(encoding="utf-8").splitlines()
        versions = {site["value"] for site in document["sites"] if site["field"] == "Version"}
        if len(versions) != 1:
            problems.append(f"{document['path']}: header and footer differ: {versions}")
        for site in document["sites"]:
            if lines[site["line"] - 1] != site["text"]:
                problems.append(f"{document['path']}:{site['line']} is {lines[site['line'] - 1]!r}, stamps.json says {site['text']!r}")
            if site["field"] == "Last Updated" and site["value"] not in (LANDING_ISO, LANDING_LONG):
                problems.append(f"{document['path']}:{site['line']} date {site['value']}")
            if site["field"] == "Version" and site["changed"]:
                on_main = main_value(tree, document["path"], 3 if document["path"] == "docs/REFERENCE.md" else 5)
                major, minor, patch = on_main.split()[-1].split(".")
                if site["value"] != f"{major}.{minor}.{int(patch) + 1}":
                    problems.append(f"{document['path']}:{site['line']} {site['value']} is not main's {on_main!r} + one step")
        print(f"{document['path']}: {len(document['sites'])} sites checked against the fixed copy")
    for problem in problems:
        print("PROBLEM:", problem)
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    verbs = parser.add_subparsers(dest="verb", required=True)
    copies = verbs.add_parser("copies")
    copies.add_argument("--out", required=True)
    copies.set_defaults(func=verb_copies)
    stamps = verbs.add_parser("stamps-fixes")
    stamps.add_argument("--hand", required=True)
    stamps.add_argument("--out", required=True)
    stamps.set_defaults(func=verb_stamps_fixes)
    check = verbs.add_parser("check")
    check.add_argument("--fixed", required=True)
    check.add_argument("--main-tree", required=True)
    check.set_defaults(func=verb_check)
    ns = parser.parse_args()
    return ns.func(ns)


if __name__ == "__main__":
    sys.exit(main())
