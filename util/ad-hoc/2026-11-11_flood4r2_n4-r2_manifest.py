#!/usr/bin/env python3
"""
Write the N-4 round-2 build's manifest.json: the base, every changed file with its status and sha256, and the record.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (deliverable assembly for the N-4 fix, round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11)

Usage::

    python3 <this file> --tree <worktree root> --record <json> --out <manifest.json> [--mutants <tag>=<mutants.json> ...]

The file list is not typed in: it is what ``git status --porcelain --untracked-files=all`` reports in the tree
(modified, added, deleted; ignored paths such as ``tmp/`` never appear), each with its sha256. The base is the tree's
``HEAD``. ``--record`` is a JSON object holding everything else (checks, open questions, what changed this round);
every path its ``logs`` list names must exist under the tree, or it is reported in ``missing_logs`` and the exit
status is 1. Each ``--mutants`` file is a ``mutants.json`` written by the round-2 mutation helper: its arms become the
manifest's ``mutations`` list, one row per arm with the verdict under each tag, and an arm whose verdict differs from
its expectation, or between tags, is a problem (exit status 1).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

STATUS = {"M": "modified", "A": "added", "D": "deleted", "??": "added"}


def _git(tree: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=tree, capture_output=True, text=True, check=True).stdout


def _mutations(specs: list[str]) -> tuple[list[dict], list[str]]:
    """One row per arm across the given ``<tag>=<mutants.json>`` files, and what does not add up."""
    rows: dict[str, dict] = {}
    problems: list[str] = []
    for spec in specs:
        tag, path = spec.split("=", 1)
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not data["verdict"]["tree_unchanged"] or not data["verdict"]["control_passes"] or not data["verdict"]["canary_fails_every_suite"]:
            problems.append(f"{tag}: the tree changed, the control arm failed or the canary did not fail every suite")
        for arm in data["arms"]:
            row = rows.setdefault(arm["arm"], {"test_file": "juniper-service-core/tests/test_websocket_broadcast_drop_close.py", "mutant": arm["arm"], "expected": arm.get("expected"), "result": {}, "log": {}})
            row["result"][tag] = arm["verdict"]
            row["log"][tag] = arm["log"]
            if "named_failures" in arm:
                row.setdefault("killed_by", {})[tag] = [name.split("::")[-1] for name in arm["named_failures"]]
            if "why_it_survives" in arm:
                row["why_it_survives"] = arm["why_it_survives"]
            if not arm["as_expected"]:
                problems.append(f"{tag}: {arm['arm']} is {arm['verdict']}, expected {arm.get('expected')}")
    for name, row in rows.items():
        if len(set(row["result"].values())) != 1 or len(row["result"]) != len(specs):
            problems.append(f"{name}: verdicts differ between runs: {row['result']}")
    return list(rows.values()), problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--record", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mutants", action="append", default=[])
    args = parser.parse_args()
    tree = args.tree.resolve()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    mutations, mutation_problems = _mutations(args.mutants)
    files = []
    for line in _git(tree, "status", "--porcelain", "--untracked-files=all").splitlines():
        code, rel = line[:2].strip(), line[3:]
        path = tree / rel
        files.append({"path": rel, "status": STATUS.get(code, code), "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None})
    files.sort(key=lambda entry: entry["path"])
    missing_logs = sorted({log for log in record.get("logs", []) if not (tree / log).exists()})
    manifest = {
        "repo": "pcalnon/juniper-ml",
        "carrier": "n4-r2",
        "base_sha": _git(tree, "rev-parse", "HEAD").strip(),
        "worktree": str(tree),
        "state": "uncommitted working tree on the base; nothing committed, pushed or opened",
        "files": files,
        "file_count": len(files),
        "missing_logs": missing_logs,
        **record,
    }
    if args.mutants:
        manifest["mutations"] = mutations
        manifest["mutation_problems"] = mutation_problems
    args.out.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    summary = {"files": len(files), "by_status": {status: sum(1 for entry in files if entry["status"] == status) for status in sorted({entry["status"] for entry in files})}, "missing_logs": missing_logs, "mutations": len(mutations), "mutation_problems": mutation_problems}
    print(json.dumps(summary))
    return 1 if missing_logs or mutation_problems else 0


if __name__ == "__main__":
    sys.exit(main())
