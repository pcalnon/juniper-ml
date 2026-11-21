#!/usr/bin/env python3
"""
Assemble a landing stage's manifest.json from its build record, the carrier's validated manifest and the check records.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (a builder keeps its manifest current, so a killed agent leaves a true record)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt (CHECKPOINT AS YOU GO); 2026-11-11_flood4r2_data-landing_build_stage.py

Usage:
    python3 <this> --stage-dir <scratch>/stage<N> --carrier-manifest <carrier's manifest.json> --status in-progress|final
                   [--parent-wt <previous stage's worktree>]

Reads <stage-dir>/build.json (written by the build script) and, when present, the fragments text_changes.json,
checks.json, mutations.json, open_questions.json and if_main_moves.json. Re-hashes every file the stage changes in its
worktree and refuses to write when one no longer has the sha256 the build recorded, or when the worktree's changed
paths are no longer the build's. Adds ``parent_sha256`` to each file: the sha256 of that path in the tree the stage
lands on (M0, or the previous stage), so a later reader can tell whether the live main still is that tree. Checks the stage's title.txt, pr_body.md and commit_body.txt when they exist: no
CI-skip marker, no trailer, no attribution footer, and the CHANGELOG entry file equals the text in the tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only git status in the stage worktree
import sys
from pathlib import Path

FRAGMENTS = ("text_changes", "checks", "mutations", "open_questions")
SKIP_MARKER = re.compile(r"\[(?:skip ci|ci skip|no ci|skip actions|actions skip)\]|\*\*\*NO_CI\*\*\*|skip-checks:", re.IGNORECASE)
TRAILER = re.compile(r"^(?:Co-Authored-By|Signed-off-by|Claude-Session|Allow-Symbol-Loss):", re.IGNORECASE | re.MULTILINE)


def _load(path: Path, default):
    if not path.is_file():
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--stage-dir", type=Path, required=True)
    ap.add_argument("--carrier-manifest", type=Path, required=True)
    ap.add_argument("--status", required=True, choices=["in-progress", "final"])
    ap.add_argument("--parent-wt", type=Path, help="the previous stage's worktree (omit when the parent is M0)")
    args = ap.parse_args()
    stage_dir = args.stage_dir.resolve()
    build = _load(stage_dir / "build.json", None)
    if build is None or build.get("status") != "ok":
        raise SystemExit(f"{stage_dir / 'build.json'} is missing or not ok")
    carrier = _load(args.carrier_manifest, {})
    worktree = Path(build["worktree"])
    drift = []
    for entry in build["files"]:
        actual = hashlib.sha256((worktree / entry["path"]).read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            drift.append(f"{entry['path']}: {actual} != {entry['sha256']}")
    status_out = subprocess.run(["git", "-C", str(worktree), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout  # nosec B603 B607
    now_changed = sorted(line[3:] for line in status_out.splitlines())
    if now_changed != sorted(build["worktree_changed_paths"]):
        drift.append(f"changed paths are now {now_changed}")
    if drift:
        raise SystemExit("the stage worktree no longer matches its build record: " + "; ".join(drift))

    # What each path holds in the tree this stage lands on: M0's blob, or the previous stage's file. When the live main's
    # blob has this sha256 the stage's file can be copied verbatim; otherwise the path must be rebuilt.
    files = []
    for entry in build["files"]:
        if args.parent_wt is not None:
            parent_file = args.parent_wt.resolve() / entry["path"]
            parent_bytes = parent_file.read_bytes() if parent_file.is_file() else None
        else:
            shown = subprocess.run(["git", "-C", str(worktree), "show", f"HEAD:{entry['path']}"], capture_output=True, check=False)  # nosec B603 B607
            parent_bytes = shown.stdout if shown.returncode == 0 else None
        files.append({**entry, "parent_sha256": hashlib.sha256(parent_bytes).hexdigest() if parent_bytes is not None else None})

    deliverables: dict = {}
    text_checks: dict = {}
    for name in ("title.txt", "pr_body.md", "commit_body.txt", "changelog_entry.txt", "stamps.json"):
        path = stage_dir / name
        if path.is_file():
            data = path.read_bytes()
            deliverables[name] = hashlib.sha256(data).hexdigest()
            text = data.decode("utf-8")
            if name in ("title.txt", "pr_body.md", "commit_body.txt"):
                text_checks[name] = {"no_ci_skip_marker": SKIP_MARKER.search(text) is None, "no_trailer": TRAILER.search(text) is None, "no_attribution_footer": "Generated with" not in text and "claude.ai/code/session" not in text}
    if (stage_dir / "changelog_entry.txt").is_file():
        entry = (stage_dir / "changelog_entry.txt").read_text(encoding="utf-8")
        text_checks["changelog_entry.txt"] = {"occurs_once_in_the_tree": (worktree / "CHANGELOG.md").read_text(encoding="utf-8").count(entry) == 1}
    if (stage_dir / "title.txt").is_file():
        title = (stage_dir / "title.txt").read_text(encoding="utf-8")
        text_checks["title.txt"]["one_line"] = title.count("\n") == 1 and title.endswith("\n")
        text_checks["title.txt"]["length"] = len(title.strip())

    manifest = {
        "status": args.status,
        "repo": build["repo"],
        "carrier": build["carrier"],
        "stage": build["stage"],
        "base_sha": build["base_sha"],
        "carrier_base_sha": build["carrier_base_sha"],
        "worktree": build["worktree"],
        "parent": build["parent"],
        "files": files,
        "carried": carrier.get("carried", []),
        "carried_note": carrier.get("carried_note"),
        "carrier_manifest": str(args.carrier_manifest.resolve()),
        "stamp_date_utc": build["stamp_date_utc"],
        "stamps": "see stamps.json beside this file",
        "merges": build["merges"],
        "file_checks": build["file_checks"],
        "applied_after": build["applied_after"],
        "amendments": build.get("amendments"),
        "changelog": build["changelog"],
        "if_main_moves": _load(stage_dir / "if_main_moves.json", {}),
        "deliverables_sha256": deliverables,
        "deliverable_checks": text_checks,
    }
    for name in FRAGMENTS:
        manifest[name] = _load(stage_dir / f"{name}.json", [])
    with open(stage_dir / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
        fh.write("\n")
    bad = [f"{name}.{key}" for name, checks in text_checks.items() for key, value in checks.items() if value is False]
    print(json.dumps({"wrote": str(stage_dir / "manifest.json"), "status": args.status, "files": len(manifest["files"]), "checks": len(manifest["checks"]), "mutations": len(manifest["mutations"]), "text_changes": len(manifest["text_changes"]), "failed_text_checks": bad}))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
