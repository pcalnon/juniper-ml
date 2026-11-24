#!/usr/bin/env python3
"""
Apply recorded amendments to a built landing stage, and re-prove what the build proved about the files they touch.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (stage 3 gained one test after its build; the build record must follow the tree)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: 2026-11-11_flood4r2_data-landing_build_stage.py (run first; this runs on its output);
         notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    python3 <this> --stage-dir <scratch>/stage<N> --amend <amend.json> --validated-entry <carrier's changelog_entry.txt>
                   [--parent-wt <previous stage's worktree>] [--as-built <repo-relative path>=<file> ...]

amend.json:
    {"why": "...", "edits": [{"id": "...", "file": "<repo-relative>", "old": "<exact text>", "new": "<exact text>",
                              "why": "..."}]}

Each edit is applied to the stage worktree named in <stage-dir>/build.json. It is idempotent: an edit whose ``new``
text already stands in the file exactly once is recorded as already applied; otherwise ``old`` must occur exactly
once and is replaced. An ``old`` that is a prefix of its ``new`` is an insertion after an anchor.

``--as-built PATH=FILE`` is for a SECOND round of amendments, when the edits in amend.json have changed and the stage
file holds the first round's text. FILE must have the sha256 the build recorded for PATH before any amendment; its
bytes are written over the stage file first, so every edit then applies from the as-built text and the stage file is,
by construction, the as-built file plus exactly the recorded edits.

Then, for every file an edit touched: its sha256 in build.json is refreshed, its ``how`` becomes ``hand`` (the build's
value is kept as ``built_how``), and its parent -> stage diff under diffs/ is rewritten. For CHANGELOG.md the build's
proof is redone against the LANDED entry: the validated entry with the same CHANGELOG edits applied must occur once in
the stage's file, the file minus it must equal the parent tree's byte for byte, and the lines on which it differs from
the validated entry are listed. changelog_entry.txt is rewritten to the landed entry. Nothing is committed or staged.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import subprocess  # nosec B404 - fixed argv: a read-only git show of the stage worktree's HEAD
import sys
from pathlib import Path


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parent_text(worktree: Path, parent_wt: Path | None, path: str) -> str | None:
    if parent_wt is not None:
        target = parent_wt / path
        return target.read_text(encoding="utf-8") if target.is_file() else None
    shown = subprocess.run(["git", "-C", str(worktree), "show", f"HEAD:{path}"], capture_output=True, check=False)  # nosec B603 B607
    return shown.stdout.decode("utf-8") if shown.returncode == 0 else None


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--stage-dir", type=Path, required=True)
    ap.add_argument("--amend", type=Path, required=True)
    ap.add_argument("--validated-entry", type=Path, required=True)
    ap.add_argument("--parent-wt", type=Path)
    ap.add_argument("--as-built", action="append", default=[], metavar="PATH=FILE")
    args = ap.parse_args()
    stage_dir = args.stage_dir.resolve()
    with open(stage_dir / "build.json", encoding="utf-8") as fh:
        build = json.load(fh)
    with open(args.amend, encoding="utf-8") as fh:
        amend = json.load(fh)
    worktree = Path(build["worktree"])
    parent_wt = args.parent_wt.resolve() if args.parent_wt else None
    by_path = {entry["path"]: entry for entry in build["files"]}
    problems: list[str] = []
    records: list[dict] = []
    touched: list[str] = []

    rebuilt_from: dict[str, str] = {}
    for item in args.as_built:
        built_path, source = item.split("=", 1)
        if built_path not in by_path:
            raise SystemExit(f"--as-built {built_path}: not one of this stage's files")
        built_bytes = Path(source).read_bytes()
        recorded = by_path[built_path].get("sha256_as_built") or by_path[built_path]["sha256"]
        if _sha(built_bytes) != recorded:
            raise SystemExit(f"--as-built {built_path}: {source} has sha256 {_sha(built_bytes)}, the build recorded {recorded}")
        (worktree / built_path).write_bytes(built_bytes)
        rebuilt_from[built_path] = str(Path(source).resolve())

    for edit in amend["edits"]:
        path = edit["file"]
        if path not in by_path:
            raise SystemExit(f"{edit['id']}: {path} is not one of this stage's files")
        target = worktree / path
        text = target.read_text(encoding="utf-8")
        if text.count(edit["new"]) == 1:
            state = "already applied"
            at = text.index(edit["new"])
        elif text.count(edit["old"]) == 1 and text.count(edit["new"]) == 0:
            state = "applied"
            at = text.index(edit["old"])
            target.write_text(text.replace(edit["old"], edit["new"]), encoding="utf-8")
        else:
            raise SystemExit(f"{edit['id']}: old occurs {text.count(edit['old'])} times and new {text.count(edit['new'])} times in {path}")
        if path not in touched:
            touched.append(path)
        records.append({"id": edit["id"], "file": path, "state": state, "first_line": text[:at].count("\n") + 1, "an_insertion_after_its_anchor": edit["new"].startswith(edit["old"]), "net_lines_added": edit["new"].count("\n") - edit["old"].count("\n"), "why": edit.get("why")})

    for path in touched:
        entry = by_path[path]
        data = (worktree / path).read_bytes()
        entry["sha256_as_built"] = entry.get("sha256_as_built", entry["sha256"])
        entry["sha256"] = _sha(data)
        entry["built_how"] = entry.get("built_how", entry["how"])
        entry["how"] = "hand"
        entry["amended_by"] = [r["id"] for r in records if r["file"] == path]
        before = _parent_text(worktree, parent_wt, path) or ""
        diff = "".join(difflib.unified_diff(before.splitlines(keepends=True), data.decode("utf-8").splitlines(keepends=True), f"parent/{path}", f"stage/{path}"))
        (stage_dir / "diffs" / (path.replace("/", "__") + ".diff")).write_text(diff, encoding="utf-8")
    for check in build.get("file_checks", []):
        if check["path"] in touched:
            check["amended_after_build"] = True
            check["how"] = "hand"

    validated = args.validated_entry.read_text(encoding="utf-8")
    landed = validated
    for edit in amend["edits"]:
        if edit["file"] == "CHANGELOG.md":
            if landed.count(edit["old"]) != 1:
                problems.append(f"{edit['id']}: its old text does not occur exactly once in the validated entry")
            landed = landed.replace(edit["old"], edit["new"])
    if "CHANGELOG.md" in touched:
        stage_changelog = (worktree / "CHANGELOG.md").read_text(encoding="utf-8")
        parent_changelog = _parent_text(worktree, parent_wt, "CHANGELOG.md") or ""
        at = stage_changelog.find(landed)
        without = stage_changelog[:at] + stage_changelog[at + len(landed) :] if at >= 0 else None
        differing = [{"entry_line": n + 1, "validated": a, "landed": b} for n, (a, b) in enumerate(zip(validated.split("\n"), landed.split("\n"))) if a != b]
        changelog = build["changelog"]
        changelog.update(
            {
                "landed_entry_sha256": _sha(landed.encode("utf-8")),
                "landed_entry_lines": landed.count("\n"),
                "landed_entry_occurs_in_stage": stage_changelog.count(landed),
                "validated_entry_occurs_in_stage": stage_changelog.count(validated),
                "entry_occurs_in_stage": stage_changelog.count(landed),
                "entry_occurs_in_parent": parent_changelog.count(landed),
                "stage_minus_entry_is_the_parent_byte_for_byte": without == parent_changelog,
                "entry_is_the_validated_entry_byte_for_byte": landed == validated,
                "landed_entry_differs_from_validated_on": differing,
                "same_line_count_as_validated": landed.count("\n") == validated.count("\n"),
            }
        )
        for key in ("difflib_added_lines", "difflib_removed_lines", "difflib_added_equals_entry"):
            changelog.pop(key, None)
        if changelog["landed_entry_occurs_in_stage"] != 1 or changelog["entry_occurs_in_parent"] != 0 or not changelog["stage_minus_entry_is_the_parent_byte_for_byte"] or not changelog["same_line_count_as_validated"]:
            problems.append("CHANGELOG.md: the landed entry is not exactly the stage's insertion over its parent")
        (stage_dir / "changelog_entry.txt").write_text(landed, encoding="utf-8")

    build["amendments"] = {"why": amend.get("why"), "spec": str(args.amend.resolve()), "rebuilt_from_as_built": rebuilt_from, "edits": records}
    build["status"] = "ok" if not problems and build.get("status") == "ok" else "PROBLEMS"
    build["problems"] = build.get("problems", []) + problems
    with open(stage_dir / "build.json", "w", encoding="utf-8") as fh:
        json.dump(build, fh, indent=1)
        fh.write("\n")
    print(json.dumps({"status": build["status"], "problems": problems, "edits": records, "files": [(p, by_path[p]["sha256"], by_path[p]["built_how"], "->", by_path[p]["how"]) for p in touched], "changelog": {k: build["changelog"][k] for k in build["changelog"] if k.startswith(("landed", "entry_", "stage_minus", "same_line", "validated_entry_occurs"))}}, indent=1))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
