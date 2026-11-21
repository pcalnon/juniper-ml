#!/usr/bin/env python3
"""
Write, or re-verify, the manifest of the ml-propose carrier after its carry-over onto a newer main.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (finishing round 3 of the ml-propose carrier, flood-4 session 6)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14;
         util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3_manifest.py (round 3's, which this one adapts)

WHY THIS EXISTS
Round 3's builder died before its final manifest, and its tree was carried onto a newer main in another worktree.
The manifest of the result has to say, per file, HOW it got here, because the assemble helper is run again at the
landing with this manifest as its file list and refuses a file whose sha256 is not the one recorded:

* ``copied``    -- main did not change the file since the predecessor's base (or the predecessor added it);
* ``three-way`` -- main changed it, so it was rebuilt with `git merge-file -p <carrier> <base> <main>`;
* ``new``       -- written in this worktree, after the carry-over.

"How" is read from the assemble helper's own report, never typed. The file list comes from the worktree's status
(the carrier is uncommitted on its base), each sha256 from the bytes on disk, and each file is compared with the
predecessor's bytes and with the bytes the assembly wrote, so an edit made after the carry-over shows. Everything
a person wrote (checks, open questions, what changed) is read from JSON files in the scratch directory.

--verify re-reads a written manifest and compares every file's sha256 with the bytes on disk and the status with
the manifest's list: the last step before the carrier is handed over.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_manifest.py --scratch tmp/flood4r2/ml-propose/r3b
        --assemble-report <assemble_report.json of the carry-over> --status in-progress|final
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_manifest.py --scratch tmp/flood4r2/ml-propose/r3b --verify
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv: read-only plumbing in this script's own worktree
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS = {"M": "modified", "A": "added", "??": "added", "D": "deleted"}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout  # nosec B603 B607


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def status_rows() -> list:
    rows = []
    for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
        code, path = line[:2].strip(), line[3:]
        status = STATUS.get(code)
        if status is None:
            raise SystemExit(f"unexpected status line: {line!r}")
        rows.append({"path": path, "status": status})
    return sorted(rows, key=lambda row: row["path"])


def optional(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def changed_files(assembled: dict) -> list:
    rows = status_rows()
    for row in rows:
        if row["status"] == "deleted":
            continue
        row["sha256"] = sha256(ROOT / row["path"])
        carried = assembled.get(row["path"])
        if carried is None:
            row["how"] = "new"
            row["note"] = "written in this worktree after the carry-over"
            continue
        row["how"] = "three-way" if "three-way" in carried["method"] else "copied"
        row["assemble_method"] = carried["method"]
        if "restamped_to" in carried:
            row["restamped_to"] = carried["restamped_to"]
        row["predecessor_sha256"] = carried["carrier_sha256"]
        row["byte_identical_to_predecessor"] = row["sha256"] == carried["carrier_sha256"]
        row["edited_after_the_carry_over"] = row["sha256"] != carried["assembled_sha256"]
    return rows


def verify(scratch: Path) -> int:
    manifest = json.loads((scratch / "manifest.json").read_text(encoding="utf-8"))
    listed = {row["path"]: row for row in manifest["files"]}
    now = {row["path"]: row["status"] for row in status_rows()}
    problems = []
    for path, row in listed.items():
        target = ROOT / path
        if row["status"] == "deleted":
            if target.exists():
                problems.append(f"{path}: listed as deleted, present")
            continue
        if not target.is_file():
            problems.append(f"{path}: absent")
        elif sha256(target) != row["sha256"]:
            problems.append(f"{path}: sha256 {sha256(target)[:12]} is not the manifest's {row['sha256'][:12]}")
    for path in sorted(set(now) - set(listed)):
        problems.append(f"{path}: changed in the worktree, not in the manifest")
    for path in sorted(set(listed) - set(now)):
        problems.append(f"{path}: in the manifest, unchanged in the worktree")
    head = git("rev-parse", "HEAD").strip()
    if head != manifest["base_sha"]:
        problems.append(f"HEAD {head[:8]} is not the manifest's base {manifest['base_sha'][:8]}")
    for line in problems:
        print("PROBLEM", line)
    print(f"verify: {len(listed)} files, base {manifest['base_sha'][:8]}, status {manifest['status']}: {'OK' if not problems else 'NOT OK'}")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--assemble-report", type=Path)
    parser.add_argument("--status", choices=("in-progress", "final"))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    scratch = args.scratch if args.scratch.is_absolute() else ROOT / args.scratch
    if args.verify:
        return verify(scratch)
    if args.assemble_report is None or args.status is None:
        raise SystemExit("writing wants --assemble-report and --status")
    report = json.loads(args.assemble_report.read_text(encoding="utf-8"))
    assembled = {row["path"]: row for row in report["files"]}
    notes = optional(scratch / "manifest_input.json", {})
    files = changed_files(assembled)
    rel_scratch = scratch.relative_to(ROOT).as_posix()
    manifest = {
        "repo": "juniper-ml",
        "carrier": "ml-propose",
        "round": "3, finished (r3b): round 3's tree carried onto a newer main and re-proved there",
        "status": args.status,
        "base_sha": git("rev-parse", "HEAD").strip(),
        "worktree": str(ROOT),
        "predecessor": {"worktree": report.get("carrier") or notes.get("predecessor_worktree"), "base_sha": report["base_sha"], "assemble_report": str(args.assemble_report.relative_to(ROOT)) if args.assemble_report.is_relative_to(ROOT) else str(args.assemble_report)},
        "files": files,
        "file_counts": {how: sum(row.get("how") == how for row in files) for how in ("copied", "three-way", "new")},
        "carried": notes.get("carried", []),
        "what_changed_since_round_3s_last_state": notes.get("what_changed_since_round_3s_last_state", []),
        "done": notes.get("done", []),
        "remains": notes.get("remains", []),
        "checks": optional(scratch / "checks.json", []),
        "mutations": optional(scratch / "mutations.json", []),
        "mutation_summary": notes.get("mutation_summary"),
        "open_questions": optional(scratch / "open_questions.json", []),
        "stamps": f"{rel_scratch}/stamps.json",
        "dispositions": f"{rel_scratch}/dispositions.json",
        "landing_command": notes.get("landing_command"),
        "scratch_outside_the_worktree": notes.get("scratch_outside_the_worktree", []),
    }
    (scratch / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"manifest.json: status={args.status} base={manifest['base_sha'][:8]} files={len(files)} {manifest['file_counts']} checks={len(manifest['checks'])} mutations={len(manifest['mutations'])} open_questions={len(manifest['open_questions'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
