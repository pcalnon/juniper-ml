#!/usr/bin/env python3
"""
Write the round-3 manifest of the ml-code carrier from the worktree, round 2's manifest and the round-3 run outputs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3: the manifest)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt (the manifest's shape) and tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt in the
         orchestrator's worktree; util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_snapshot.py (the file list).

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_manifest.py <round-2 manifest.json> <checks.json> <scratch dir>

``files`` is what the worktree changes against HEAD, with sha256 (``git status``; tmp/ is ignored). ``carried`` is
round 2's list, unchanged: round 3 took nothing new from a draft. ``checks`` is read from <checks.json>, a list
written by hand from the round's logs ({what, command, result, log, detail}). ``mutations`` is read from
<scratch dir>/mutants_baselines/mutants.json, <scratch dir>/mutants/mutants.json and
<scratch dir>/mutants_launcher_187e3258/mutants.json (the launcher's rows, run again after main moved). Writes
<scratch dir>/manifest.json and prints its sha256.
"""
import hashlib
import json
import subprocess  # nosec B404 -- fixed git argv, run in this worktree
import sys
from pathlib import Path


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout  # nosec B603 B607


def files() -> list:
    rows = []
    for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
        code, rel = line[:2], line[3:]
        status = {"??": "added", " M": "modified"}.get(code)
        if status is None:
            raise SystemExit("unexpected git status line: %r" % line)
        rows.append({"path": rel, "status": status, "sha256": hashlib.sha256(Path(rel).read_bytes()).hexdigest()})
    return sorted(rows, key=lambda row: (row["status"] != "modified", row["path"]))


def mutations(scratch: Path) -> list:
    rows = []
    for name in ("mutants_baselines", "mutants", "mutants_launcher_187e3258"):
        path = scratch / name / "mutants.json"
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as fh:
            report = json.load(fh)
        for m in report["mutants"]:
            runs = m.get("runs", [])
            change = "HEAD's whole file in place of the carrier's" if m["old"] is None else "%r -> %r" % (m["old"], m["new"])
            rows.append({"id": m["id"], "family": m["family"], "intent": m["intent"], "test_file": (m.get("killed_by") or (runs[-1]["target"] if runs else "")), "mutant": "%s: %s" % (m["file"], change), "result": m["verdict"], "summary": runs[-1]["summary"] if runs else "", "log": str(path)})
    return rows


def main() -> int:
    with open(sys.argv[1], encoding="utf-8") as fh:
        round2 = json.load(fh)
    with open(sys.argv[2], encoding="utf-8") as fh:
        extra = json.load(fh)
    scratch = Path(sys.argv[3]).resolve()
    listed = files()
    manifest = {
        "repo": "pcalnon/juniper-ml",
        "carrier": "ml-code",
        "round": 3,
        "base_sha": git("rev-parse", "HEAD").strip(),
        "worktree": str(Path.cwd()),
        "supersedes": {"worktree": round2["worktree"], "base_sha": round2["base_sha"], "note": "the round-2 carrier, left as it was"},
        "files": listed,
        "file_count": {"modified": sum(1 for row in listed if row["status"] == "modified"), "added": sum(1 for row in listed if row["status"] == "added")},
        "what_changed_in_round_3": extra["what_changed_in_round_3"],
        "carried": round2["carried"],
        "checks": extra["checks"],
        "mutations": mutations(scratch),
        "open_questions": extra["open_questions"],
        "cleanup": extra.get("cleanup", []),
    }
    out = scratch / "manifest.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print("%s: %d files (%d modified, %d added), %d checks, %d mutations; sha256 %s" % (out, len(listed), manifest["file_count"]["modified"], manifest["file_count"]["added"], len(manifest["checks"]), len(manifest["mutations"]), hashlib.sha256(out.read_bytes()).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
