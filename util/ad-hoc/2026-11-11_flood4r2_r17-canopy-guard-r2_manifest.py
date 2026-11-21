"""
Assemble the round-2 manifest and stamps for the ruling-17 guard carrier, and mirror the deliverables.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round 2 of the Overtoad's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt)

Usage:
    python3 <this file> --carrier <carrier worktree> --body <manifest body json> --stamp-file <repo-relative doc> \
        --main-copy <that doc as it is on main> --deliverables <dir> --mirror <dir> [--mirror ...]

manifest.json = the hand-written body (checks, mutations, dispositions summary, open questions, what changed this
round) plus what is read from the tree at the moment of the call: the base sha (HEAD), and each file of the
uncommitted change set with its status and sha256. stamps.json holds the stamped document's `**Last Updated:**`
and `**Version:**` lines on main and in the carrier, every other line of the document that carries either label
(a footer stamp would show there), and whether the version moved by exactly one patch step.

Every file in --deliverables is then copied to each --mirror directory and its sha256 compared.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(tree: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(tree), *args], check=True, capture_output=True, text=True).stdout  # nosec B603 B607 - fixed argv


def stamp_lines(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    hits = [(number, line.rstrip()) for number, line in enumerate(lines, start=1) if re.match(r"\*\*(Last Updated|Version):\*\*", line)]
    updated = next((line for _, line in hits if line.startswith("**Last Updated:**")), None)
    version = next((line for _, line in hits if line.startswith("**Version:**")), None)
    return {"last_updated": updated, "version": version, "stamp_lines": [f"{number}: {line}" for number, line in hits], "line_count": len(lines)}


def patch_step(before: str | None, after: str | None) -> bool:
    old, new = (re.search(r"v(\d+)\.(\d+)\.(\d+)", text or "") for text in (before, after))
    return bool(old and new and old.groups()[:2] == new.groups()[:2] and int(new.group(3)) == int(old.group(3)) + 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble the round-2 manifest and stamps, and mirror the deliverables.")
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--body", required=True, type=Path)
    parser.add_argument("--stamp-file", required=True)
    parser.add_argument("--main-copy", required=True, type=Path)
    parser.add_argument("--deliverables", required=True, type=Path)
    parser.add_argument("--mirror", required=True, type=Path, action="append")
    args = parser.parse_args()
    carrier = args.carrier.resolve()
    files = []
    for entry in [item for item in git(carrier, "status", "--porcelain=v1", "--untracked-files=all", "-z").split("\0") if item]:
        if entry[:2] not in (" M", "??"):
            raise SystemExit(f"[manifest] unexpected status {entry[:2]!r} for {entry[3:]}")
        files.append({"path": entry[3:], "status": "modified" if entry[:2] == " M" else "added", "sha256": sha256(carrier / entry[3:])})
    body = json.loads(args.body.read_text(encoding="utf-8"))
    manifest = {"repo": body.pop("repo"), "carrier": body.pop("carrier"), "base_sha": git(carrier, "rev-parse", "HEAD").strip(), "worktree": str(carrier), "branch": git(carrier, "rev-parse", "--abbrev-ref", "HEAD").strip(), "files": sorted(files, key=lambda item: item["path"])} | body
    on_main, in_carrier = stamp_lines(args.main_copy), stamp_lines(carrier / args.stamp_file)
    stamps = {
        "base_sha": manifest["base_sha"],
        "documents": [
            {
                "path": args.stamp_file,
                "main": on_main,
                "carrier": in_carrier,
                "version_moved_one_patch_step": patch_step(on_main["version"], in_carrier["version"]),
                "footer_stamp": "none: the document's only stamp is its header" if len(in_carrier["stamp_lines"]) == 2 else "check stamp_lines",
            }
        ],
    }
    deliverables = args.deliverables.resolve()
    (deliverables / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    (deliverables / "stamps.json").write_text(json.dumps(stamps, indent=1) + "\n", encoding="utf-8")
    ok = stamps["documents"][0]["version_moved_one_patch_step"]
    for mirror in [entry.resolve() for entry in args.mirror]:
        mirror.mkdir(parents=True, exist_ok=True)
        for source in sorted(path for path in deliverables.iterdir() if path.is_file()):
            shutil.copyfile(source, mirror / source.name)
            ok = ok and sha256(mirror / source.name) == sha256(source)
        print(f"[manifest] mirrored {len([path for path in deliverables.iterdir() if path.is_file()])} files to {mirror}")
    print(f"[manifest] base {manifest['base_sha']}; {len(files)} files; stamp {in_carrier['last_updated']} / {in_carrier['version']} (main: {on_main['last_updated']} / {on_main['version']}); ok={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
