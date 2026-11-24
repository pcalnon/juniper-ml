#!/usr/bin/env python3
"""
Assemble manifest.json and stamps.json for the juniper-data unrun-tests change from the tree and its evidence files.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (the builder's deliverables; re-run after any edit, it re-hashes every file)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#529 (the precedent)

Usage:
    python3 <this> --worktree <juniper-data tree> --scratch <its tmp/flood4-fix/d2-unrun-tests> --fragments <json>
                   [--verify <sha256 list>]

WHAT IT DOES
- files: every uncommitted path from ``status --porcelain`` with its status and sha256 (a deleted path carries the
  sha256 of main's blob instead), and whether main's copy also changes in the Retry-After change that lands first.
- census: the per-lane selections before and after, from the collect helper's JSON files, and the tests no lane
  selects, by file and class, with the reason.
- mutations: from the mutants helper's JSON files, one row per mutant with both verdicts.
- checks, open_questions, notes, helpers: copied from --fragments, a hand-written JSON file.
- stamps.json: for every document the change touches, each ``Version`` / ``Last Updated`` / ``Date`` line with its
  line number, main's value at that site and the value the tree holds, plus the rule that re-derives it.
With --verify it re-hashes the listed files and fails on any difference: the last step before the final message.
It calls the version-control client read-only (status, show, rev-parse) and writes only the two JSON files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only queries of the version-control client
import sys
from pathlib import Path

VCS = "git"
RETRY_AFTER_ALSO_CHANGES = ("CHANGELOG.md", "docs/REFERENCE.md", "docs/DEVELOPER_CHEATSHEET.md", "juniper_data/api/security.py")
STAMP_RE = re.compile(r"^\*\*(Version|Last Updated)\*?\*?:?\*?\*?:?\s*(.+?)\s*$")
RENAME = {"juniper_data/tests/api/test_batch_operations.py": "juniper_data/tests/unit/test_batch_operations.py"}


def _out(argv: list[str], cwd: Path) -> str:
    done = subprocess.run(argv, cwd=str(cwd), capture_output=True, check=False)  # nosec B603
    if done.returncode != 0:
        raise SystemExit(f"command failed ({done.returncode}): {' '.join(argv)}\n{done.stderr.decode('utf-8', 'replace')}")
    return done.stdout.decode("utf-8", "replace")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _files(wt: Path, base: str) -> list[dict]:
    rows = []
    for entry in [e for e in _out([VCS, "status", "--porcelain", "-z", "--untracked-files=all"], wt).split("\0") if e]:
        code, path = entry[:2], entry[3:]
        target = wt / path
        if "D" in code:
            blob = subprocess.run([VCS, "show", f"{base}:{path}"], cwd=str(wt), capture_output=True, check=False).stdout  # nosec B603
            rows.append({"path": path, "status": "deleted", "sha256_of_main_blob": _sha(blob)})
            continue
        with open(target, "rb") as fh:
            data = fh.read()
        row = {"path": path, "status": "added" if code == "??" or "A" in code else "modified", "sha256": _sha(data), "bytes": len(data)}
        if path in RENAME.values():
            origin = next(old for old, new in RENAME.items() if new == path)
            row["moved_from"] = origin
        row["main_also_changes_in_the_retry_after_change"] = path in RETRY_AFTER_ALSO_CHANGES
        rows.append(row)
    return sorted(rows, key=lambda r: r["path"])


def _census(scratch: Path, before_tag: str, after_tag: str) -> dict:
    before = _load(scratch / "collect" / f"collect_{before_tag}.json")
    after = _load(scratch / "collect" / f"collect_{after_tag}.json")
    compare = _load(scratch / "collect" / f"compare_{before_tag}_{after_tag}.json")
    lanes = {}
    for name in ("unit", "integration", "gitleaks", "slow", "scheduled", "all"):
        b, a = before["selections"][name], after["selections"][name]
        lanes[name] = {
            "kind": before["lane_kinds"].get(name, "no selection: every test pytest collects from testpaths"),
            "pytest_arguments": [x for x in b["argv"][b["argv"].index("no:cacheprovider") + 1 :]],
            "before": {"selected": b["count"], "summary": b["summary"]},
            "after": {"selected": a["count"], "summary": a["summary"]},
            "delta": a["count"] - b["count"],
            "added_by_file": compare["per_selection"][name]["added_by_file"],
            "removed_by_file": compare["per_selection"][name]["removed_by_file"],
        }
    return {
        "collected_on": {"before": before["worktree"], "after": after["worktree"], "interpreter": before["interpreter"], "python_version": before["python_version"]},
        "lanes": lanes,
        "lane_combinations_before": before["lane_combinations"],
        "lane_combinations_after": after["lane_combinations"],
        "no_lane_before": before["no_lane"],
        "no_lane_after": after["no_lane"],
        "scheduled_only_before": before["scheduled_only"],
        "scheduled_only_after": after["scheduled_only"],
        "moved_out_of_no_lane": {"count": compare["no_lane"]["left_no_lane"], "into": compare["moved_into"], "by_file": compare["moved_by_file"], "newly_selected_equals_moved": compare["newly_selected_equals_moved"], "any_lane_lost_a_node": compare["any_lane_lost_a_node"], "entered_no_lane": compare["no_lane"]["entered_no_lane"], "renames_applied": compare.get("renames_applied_to_a", {})},
        "evidence": [f"collect/collect_{before_tag}.json", f"collect/collect_{after_tag}.json", f"collect/compare_{before_tag}_{after_tag}.json"],
    }


def _mutations(scratch: Path) -> list[dict]:
    rows: dict[str, dict] = {}
    for path in sorted((scratch / "mutants").rglob("mutants_*.json")):
        data = _load(path)
        for m in data["mutants"]:
            row = rows.setdefault(m["id"], {"id": m["id"], "test_file": m["test_file"], "mutant": m.get("mutant"), "what": m["what"]})
            key = {"new-tests": "newly_selected_tests", "main-lane": "main_unit_lane", "main-integration-lane": "main_integration_lane"}[data["mode"]]
            row[key] = {k: m.get(k) for k in ("result", "exit", "summary", "failed_count", "failed_tests", "restored_byte_for_byte", "sha256_before", "sha256_after", "tree", "log", "reason") if k in m}
            row[key]["interpreter"] = data["python"]
    return [rows[k] for k in sorted(rows)]


def _stamps(wt: Path, base: str, files: list[dict], landing_date: str) -> dict:
    docs = []
    for row in files:
        path = row["path"]
        if row["status"] == "deleted" or not path.endswith(".md") or path == "CHANGELOG.md":
            continue
        with open(wt / path, encoding="utf-8") as fh:
            mine = fh.read().splitlines()
        main_lines = _out([VCS, "show", f"{base}:{path}"], wt).splitlines()
        main_sites = [(n, m.group(1), m.group(2)) for n, ln in enumerate(main_lines, 1) if (m := STAMP_RE.match(ln))]
        sites = []
        for n, ln in enumerate(mine, 1):
            hit = STAMP_RE.match(ln)
            if not hit:
                continue
            same_kind = [s for s in main_sites if s[1] == hit.group(1)]
            order = sum(1 for s in sites if s["field"] == hit.group(1))
            main_value = same_kind[order][2] if order < len(same_kind) else None
            sites.append({"line": n, "field": hit.group(1), "text": ln, "value": hit.group(2), "main_value": main_value, "changed": main_value != hit.group(2)})
        versions = sorted({s["value"] for s in sites if s["field"] == "Version"})
        dates = sorted({s["value"] for s in sites if s["field"] == "Last Updated"})
        docs.append({
            "path": path,
            "sites": sites,
            "header_equals_footer": len(versions) <= 1 and len(dates) <= 1,
            "footer_present": sum(1 for s in sites if s["field"] == "Version") > 1,
            "main_also_changes_in_the_retry_after_change": path in RETRY_AFTER_ALSO_CHANGES,
        })
    return {
        "landing_date_utc": landing_date,
        "rule": "A document's Version is main's value plus one patch step, taken once; header and footer agree; every Last Updated site carries the UTC date of the day the change lands. AGENTS.md's Version is the package version and does not move; its Last Updated is the landing date in ISO form.",
        "re_derive": "Read main's value at the same site when the change is rebuilt on a newer main, add one patch step, and set the date to the landing day. If the Retry-After change has landed, docs/REFERENCE.md on main reads 0.4.8 and this change's value becomes 0.4.9.",
        "base": base,
        "documents": docs,
        "date_sites_outside_stamps": [
            "CHANGELOG.md: the entry names '2026-11-12', the date of the Overtoad's ruling, and main 'c68e6b4c'; neither is a landing date",
            "No test file, docstring or comment added by this change carries a date",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--scratch", type=Path, required=True)
    ap.add_argument("--fragments", type=Path)
    ap.add_argument("--before-tag", default="before_py314")
    ap.add_argument("--after-tag", default="final_py314")
    ap.add_argument("--landing-date", default="2026-11-13")
    ap.add_argument("--verify", type=Path)
    args = ap.parse_args()
    wt, scratch = args.worktree.resolve(), args.scratch.resolve()
    if args.verify:
        bad = 0
        with open(args.verify, encoding="utf-8") as fh:
            for line in fh:
                want, _, rel = line.strip().partition("  ")
                with open(wt / rel, "rb") as src:
                    got = _sha(src.read())
                if got != want:
                    bad += 1
                    print(f"DIFFERS: {rel} {got} != {want}")
        print(f"verified {args.verify}: {bad} file(s) differ")
        return 1 if bad else 0
    base = _out([VCS, "rev-parse", "origin/main"], wt).strip()
    head = _out([VCS, "rev-parse", "HEAD"], wt).strip()
    branch = _out([VCS, "rev-parse", "--abbrev-ref", "HEAD"], wt).strip()
    files = _files(wt, base)
    fragments = _load(args.fragments) if args.fragments else {}
    manifest = {
        "repo": "pcalnon/juniper-data",
        "change": "d2-unrun-tests",
        "ruling": "the Overtoad's ruling of 2026-11-12, option 'A follow-up PR now (Recommended)' (the record's next update adds it to its section 8)",
        "base_sha": base,
        "worktree_head": head,
        "worktree": str(wt),
        "branch": branch,
        "state": "uncommitted working tree; nothing staged, nothing pushed",
        "files": files,
        "census": _census(scratch, args.before_tag, args.after_tag),
        "checks": fragments.get("checks", []),
        "mutations": _mutations(scratch),
        "open_questions": fragments.get("open_questions", []),
        "notes": fragments.get("notes", []),
        "helpers": fragments.get("helpers", []),
        "side_effects": fragments.get("side_effects", []),
    }
    with open(scratch / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
        fh.write("\n")
    with open(scratch / "stamps.json", "w", encoding="utf-8") as fh:
        json.dump(_stamps(wt, base, files, args.landing_date), fh, indent=1)
        fh.write("\n")
    with open(scratch / "sha256_final.txt", "w", encoding="utf-8") as fh:
        for row in files:
            if row["status"] != "deleted":
                fh.write(f"{row['sha256']}  {row['path']}\n")
    print(json.dumps({"base_sha": base, "files": [(r["path"], r["status"]) for r in files], "mutations": [(m["id"], (m.get("newly_selected_tests") or {}).get("result"), (m.get("main_unit_lane") or {}).get("result"), (m.get("main_integration_lane") or {}).get("result")) for m in manifest["mutations"]], "checks": len(manifest["checks"]), "open_questions": len(manifest["open_questions"])}, indent=1))
    print(f"wrote {scratch / 'manifest.json'}, {scratch / 'stamps.json'} and {scratch / 'sha256_final.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
