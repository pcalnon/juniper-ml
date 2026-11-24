#!/usr/bin/env python3
"""
Assemble the stop-then-start carrier's round-2 manifest.json: hand-written facts plus the hashes and mutant results read from disk.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start", carrier round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt DELIVERABLES; tmp/flood4/session6/BRIEF_S6_ADDENDUM.txt
         section 1 (every carrier file's sha256 is recorded and re-verified); the round-1 helper
         util/ad-hoc/2026-11-11_flood4r2_r17-cascor_manifest.py (kept as it ran)

The hand file (``--hand``) carries what only its author knows: the base, the checks with their
commands, exit statuses and logs, what changed this round in each file, and the open questions.
This script adds what can be read from disk, so no hash or mutant verdict is ever typed:

* for every path the porcelain status of the carrier names (run by this script), its status and
  sha256 now, its sha256 at the base commit (``<base>:<path>`` hashed from the object store) and
  its round-1 sha256 when ``--round1-sums`` lists it;
* the mutant campaign's runs from ``--mutants`` (the campaign's own JSON), and the three logs of
  juniper-cascor's paused-fit mutation check from ``--n1-log label=path`` (verdict line, exit
  line, survivors);
* a refusal to write ``"status": "final"`` when the hand file's ``paths_the_pr_changes`` is not
  exactly the set of paths the porcelain status names.

Usage:
  2026-11-12_flood4r2_r17-cascor_manifest.py --tree <carrier> --hand <manifest_hand.json> --out <manifest.json>
      [--round1-sums <SHA256SUMS.txt>] [--mutants <mutants.json>] [--n1-log label=path ...]
Exit: 0 when the manifest was written; 1 when a check above refused it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 -- fixed-argv git reads
import sys
from pathlib import Path

STATUS_WORDS = {"M": "modified", "A": "added", "D": "deleted", "??": "added"}


def _git(tree: Path, *argv: str) -> bytes:
    return subprocess.run(["git", "-C", str(tree), *argv], capture_output=True, check=True).stdout  # nosec B603 B607 -- fixed argv


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _files(tree: Path, base: str, round1: dict, notes: dict) -> list:
    rows = []
    for line in _git(tree, "status", "--porcelain").decode("utf-8").splitlines():
        code, path = line[:2].strip(), line[3:]
        status = STATUS_WORDS.get(code, code)
        row = {"path": path, "status": status, "sha256": _sha256((tree / path).read_bytes())}
        if code != "??":
            row["sha256_at_base"] = _sha256(_git(tree, "show", f"{base}:{path}"))
        if path in round1:
            row["sha256_round1"] = round1[path]
        row["changed_this_round"] = notes.get(path, "NOT STATED")
        rows.append(row)
    return rows


def _n1(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    verdict = re.search(r"^(\d+)/(\d+) mutations caught, (\d+) not caught\.$", text, re.MULTILINE)
    exits = re.findall(r"^exit=(\d+)$", text, re.MULTILINE)
    return {
        "log": str(path),
        "control_green": "CONTROL  exit 0, 0 failed, provenance ok" in text,
        "caught": int(verdict.group(1)) if verdict else None,
        "of": int(verdict.group(2)) if verdict else None,
        "exit": int(exits[-1]) if exits else None,
        "survivors": re.findall(r"^(M\d+) SURVIVED", text, re.MULTILINE),
        "caught_by_one_test_only": re.findall(r"^(M\d+) CAUGHT .*\[exit 1; 1 failed\]$", text, re.MULTILINE),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--hand", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--round1-sums", type=Path)
    parser.add_argument("--mutants", type=Path)
    parser.add_argument("--n1-log", action="append", default=[], help="label=path of one paused-fit mutation-check log")
    args = parser.parse_args()
    tree = args.tree.resolve()
    hand = json.loads(args.hand.read_text(encoding="utf-8"))
    base = hand["base_sha"]

    round1 = {}
    if args.round1_sums:
        for line in args.round1_sums.read_text(encoding="utf-8").splitlines():
            digest, _, path = line.partition("  ")
            round1[path] = digest
    head = _git(tree, "rev-parse", "HEAD").decode("utf-8").strip()
    files = _files(tree, base, round1, hand.get("changed_this_round", {}))
    problems = []
    if head != base:
        problems.append(f"the carrier's HEAD is {head}, not the base {base}")
    named = sorted(hand.get("paths_the_pr_changes", []))
    on_disk = sorted(row["path"] for row in files)
    if named != on_disk:
        problems.append(f"paths_the_pr_changes names {named}, the porcelain status names {on_disk}")
    unstated = [row["path"] for row in files if row["changed_this_round"] == "NOT STATED"]
    if unstated:
        problems.append(f"changed_this_round says nothing about {unstated}")

    manifest = {key: value for key, value in hand.items() if key != "changed_this_round"}
    manifest["head_sha"] = head
    manifest["head_is_base"] = head == base
    manifest["files"] = files
    if args.mutants:
        campaign = json.loads(args.mutants.read_text(encoding="utf-8"))
        manifest["mutations"] = [
            {
                "campaign": str(args.mutants),
                "id": run["id"],
                "group": run.get("group"),
                "mutant": run.get("description"),
                "tests_run": run.get("tests_run"),
                "result": run.get("verdict"),
                "tests": run.get("tests"),
                "failed": len(run.get("failed", [])),
                "checkout_unchanged_after_the_run": run.get("checkout_unchanged"),
                "log": run.get("log"),
            }
            for run in campaign["results"]
        ]
        manifest["mutation_campaign_checkout"] = {"sha256_before": campaign["sha256_before"], "sha256_after": campaign["sha256_after"], "unchanged_after_every_run": campaign.get("unchanged_after_every_run")}
    manifest["paused_fit_mutation_check"] = {}
    for item in args.n1_log:
        label, _, path = item.partition("=")
        manifest["paused_fit_mutation_check"][label] = _n1(Path(path))
    if problems and manifest.get("status") == "final":
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    manifest["manifest_problems"] = problems
    args.out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.out}: status {manifest.get('status')}, {len(files)} files, {len(manifest.get('checks', []))} checks, {len(manifest.get('mutations', []))} mutation runs, {len(manifest.get('open_questions', []))} open questions; problems: {problems}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
