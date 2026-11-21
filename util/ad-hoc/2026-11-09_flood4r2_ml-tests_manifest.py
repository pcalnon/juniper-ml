#!/usr/bin/env python3
"""
Write the ml-tests carrier's manifest.json (BRIEF_COMMON_R2's schema) from the build's recorded artifacts.

Inputs, all under the scratch dir: own/summary.json (2026-11-09_flood4r2_ml-tests_survey.py: each draft's head and
own-diff base), carried_input.json (the per-draft taken / fixes / dropped / outcome / reason, written by hand as the
drafts were carried), mutation/mutation_results.json (2026-11-09_flood4r2_ml-tests_mutation_check.py) and
checks_input.json (each check's command, interpreter, exit status and log). The file list is read from the worktree
(`git diff --name-status` against the base plus untracked files), each with its sha256, so the manifest describes
the tree as it stands when this runs. Titles come from ml-prs.json of the round-2 triage when given.

Usage: python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_manifest.py --scratch <dir> --base <sha> --worktree <abs>
       [--triage-prs <ml-prs.json>]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt (DELIVERABLES: the manifest schema)
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _files(base: str) -> list:
    rows = []
    status = {"A": "added", "M": "modified", "D": "deleted"}
    out = subprocess.run(["git", "diff", "--name-status", base], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        code, path = line.split("\t", 1)
        rows.append({"path": path, "status": status.get(code[0], code)})
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True, check=True).stdout.split()
    rows += [{"path": p, "status": "added"} for p in untracked]
    for row in rows:
        p = Path(row["path"])
        row["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    return sorted(rows, key=lambda r: r["path"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--triage-prs")
    ap.add_argument("--mutation-reruns", nargs="*", default=[], help="dirs holding a later mutation_results.json for some mutants")
    args = ap.parse_args()
    scratch = Path(args.scratch)
    heads = {r["pr"]: r for r in _load(scratch / "own" / "summary.json") if "head" in r}
    titles = {}
    if args.triage_prs:
        titles = {p["number"]: p.get("title", "") for p in _load(Path(args.triage_prs))}
    carried = []
    for row in _load(scratch / "carried_input.json"):
        pr = row["pr"]
        carried.append({"pr": pr, "head_sha": heads.get(pr, {}).get("head"), "title": titles.get(pr, ""), **{k: row[k] for k in ("taken", "fixes", "dropped", "outcome", "reason")}})
    results = _load(scratch / "mutation" / "mutation_results.json")
    # A re-run after a test file changed replaces that mutant's first result (same draft, target and mutant).
    for rerun_dir in args.mutation_reruns:
        for again in _load(Path(rerun_dir) / "mutation_results.json"):
            for i, first in enumerate(results):
                if (first["pr"], first["target"], first["old"], first["new"]) == (again["pr"], again["target"], again["old"], again["new"]):
                    results[i] = {**again, "rerun_of": first["log"]}
    mutations = []
    for m in results:
        entry = {"test_file": m["test_file"], "mutant": f"{m['target']}: {m['old'].strip()!r} -> {m['new'].strip()!r}", "result": m.get("result"), "log": m["log"], "pr": m["pr"], "selection_size": len(m.get("selection", [])), "restored_byte_for_byte": m.get("mutant_restored")}
        if "control_result" in m:
            entry["control_on_mains_test_file"] = m["control_result"]
        if "rerun_of" in m:
            entry["rerun_of"] = m["rerun_of"]
        mutations.append(entry)
    checks_path = scratch / "checks_input.json"
    manifest = {
        "repo": "juniper-ml",
        "carrier": "ml-tests",
        "base_sha": args.base,
        "worktree": args.worktree,
        "files": _files(args.base),
        "carried": carried,
        "checks": _load(checks_path) if checks_path.is_file() else [],
        "mutations": mutations,
        "open_questions": _load(scratch / "open_questions.json") if (scratch / "open_questions.json").is_file() else [],
    }
    with open(scratch / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    killed = sum(1 for m in mutations if m["result"] == "killed")
    print(f"manifest: {len(manifest['files'])} files, {len(carried)} drafts, {killed}/{len(mutations)} mutants killed, {len(manifest['checks'])} checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
