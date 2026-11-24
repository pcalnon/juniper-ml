#!/usr/bin/env python3
"""
Build a carrier's refreshed manifest.json from a hand-written skeleton, with sha256s, and check its deliverables.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: refreshed carrier deliverables after the validators' fixes)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt DELIVERABLES

Usage:
  2026-11-08_flood4r2_fix_manifest.py <skeleton.json> <carrier scratch dir>

The skeleton holds everything a reader must judge (carried, checks, mutations, stamps, open questions). This script
adds what a script can measure, so none of it is typed by hand:

- ``files``: every path ``git status --porcelain --untracked-files=all`` lists in the carrier worktree, its status
  and its sha256;
- ``deliverables``: the sha256 of each deliverable in the scratch dir (pr_body.txt, commit_body.txt,
  changelog_entry.txt, dispositions.json, and any other file the skeleton names);
- ``deliverable_checks``: pr_body.txt's first line is ``TITLE: ``; changelog_entry.txt occurs in the worktree's
  CHANGELOG.md, after the top ``## [Unreleased]`` and before the next release heading; neither body carries a CI-skip
  marker; commit_body.txt has no trailer lines.

Writes <scratch dir>/manifest.json. Exit 1 if a deliverable check fails.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

STATUS = {"M": "modified", "A": "added", "D": "deleted", "??": "added"}
SKIP_MARKERS = re.compile(r"\[(skip ci|ci skip|no ci|skip actions|actions skip)\]", re.IGNORECASE)
TRAILER = re.compile(r"^(Co-Authored-By|Signed-off-by|Claude-Session|Reviewed-by):", re.IGNORECASE | re.MULTILINE)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str]) -> int:
    skeleton = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    scratch = Path(argv[2]).resolve()
    wt = Path(skeleton["worktree"])
    porcelain = subprocess.run(["git", "-C", str(wt), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout
    files = []
    for line in porcelain.splitlines():
        code, path = line[:2].strip(), line[3:]
        files.append({"path": path, "status": STATUS.get(code, code), "sha256": _sha(wt / path) if (wt / path).exists() else None})
    names = ["pr_body.txt", "commit_body.txt", "changelog_entry.txt", "dispositions.json", *skeleton.get("extra_deliverables", [])]
    deliverables = {name: _sha(scratch / name) for name in names if (scratch / name).exists()}
    missing = [name for name in names if not (scratch / name).exists()]
    checks = {}
    pr_body = (scratch / "pr_body.txt").read_text(encoding="utf-8")
    commit_body = (scratch / "commit_body.txt").read_text(encoding="utf-8")
    entry = (scratch / "changelog_entry.txt").read_text(encoding="utf-8")
    changelog = (wt / "CHANGELOG.md").read_text(encoding="utf-8")
    checks["pr_body_title_line"] = pr_body.splitlines()[0].startswith("TITLE: ")
    position = changelog.find(entry)
    unreleased = changelog.find("## [Unreleased]")
    next_release = changelog.find("\n## [", unreleased + 1)
    checks["changelog_entry_in_tree"] = position >= 0
    checks["changelog_entry_under_top_unreleased"] = position > unreleased >= 0 and (next_release < 0 or position < next_release)
    checks["no_ci_skip_marker"] = not SKIP_MARKERS.search(pr_body) and not SKIP_MARKERS.search(commit_body)
    checks["commit_body_has_no_trailers"] = not TRAILER.search(commit_body)
    checks["deliverables_missing"] = missing
    ok = all(value for key, value in checks.items() if key != "deliverables_missing") and not missing
    manifest = {
        "repo": skeleton["repo"],
        "carrier": skeleton["carrier"],
        "base_sha": skeleton["base_sha"],
        "worktree": str(wt),
        "files": files,
        **{key: value for key, value in skeleton.items() if key not in ("repo", "carrier", "base_sha", "worktree", "extra_deliverables")},
        "deliverables": deliverables,
        "deliverable_checks": checks,
    }
    (scratch / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{skeleton['carrier']}: {len(files)} files; deliverable checks {'pass' if ok else 'FAIL'} {checks}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
