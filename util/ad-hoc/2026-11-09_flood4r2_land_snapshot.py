#!/usr/bin/env python3
"""
Freeze a carrier's landing snapshot on the CURRENT main: copy its files, rebuild the shared ones three-way, and
refuse any other file that main has moved since the carrier's base.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 session 4: landing the fix carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/push_signed_commit.py, util/open_signed_pr.py (push what this freezes)

Usage:
  2026-11-09_flood4r2_land_snapshot.py --tree <carrier worktree> --base <sha> --out <dir>
      (--manifest <manifest.json> | --path <repo path> ... | --paths-file <file>) [--three-way <repo path> ...]
      [--prebuilt REPO_PATH=LOCAL_FILE ...] [--main-ref origin/main]

Run it from a checkout of the carrier's repository whose ``--main-ref`` is fetched: every ``git`` call here reads
THIS checkout's object store (``git rev-parse`` / ``git cat-file`` / ``git merge-file``), never the carrier's.

For each path (from the manifest's ``changed`` list, or ``--path``):
  * a ``--prebuilt REPO_PATH=LOCAL_FILE`` path: taken from LOCAL_FILE, already rebuilt on the current main by a
    dedicated tool (its own checks are the gate);
  * a ``--three-way`` path: ``git merge-file -p <carrier> <base> <main>``; any conflict refuses;
  * any other path: main's blob must equal the base's (both absent for an added file); the carrier's copy is taken.
  * a path whose manifest ``status`` is ``deleted`` (or that is absent from the carrier) is recorded as a delete,
    under the same base == main rule.
Writes <out>/snapshot/<path>, <out>/paths.txt (``add <path>`` / ``delete <path>``), <out>/snapshot.sha256,
<out>/plan.json (main sha, base sha, per-path action) and <out>/main/<path> (main's copy of every path main has: the
secret scan's baseline). Exit 0 = frozen, 1 = refused (nothing is trusted then).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def git(*args: str, check: bool = True, data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], input=data, capture_output=True, check=check)


def blob(ref: str, path: str) -> bytes | None:
    probe = git("cat-file", "-e", f"{ref}:{path}", check=False)
    if probe.returncode != 0:
        return None
    return git("cat-file", "blob", f"{ref}:{path}").stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--paths-file", help="a file listing one repository path per line, read as repeated --path")
    parser.add_argument("--three-way", action="append", default=[])
    parser.add_argument("--prebuilt", action="append", default=[], help="REPO_PATH=LOCAL_FILE: take this path's content from a file already rebuilt on the current main")
    parser.add_argument("--main-ref", default="origin/main")
    args = parser.parse_args()

    tree = Path(args.tree).resolve()
    out = Path(args.out)
    prebuilt = {}
    for spec in args.prebuilt:
        repo_path, _, local = spec.partition("=")
        prebuilt[repo_path] = Path(local).resolve()
    entries: list[tuple[str, str]] = []
    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        listed = manifest.get("changed") or manifest.get("files") or []
        entries = [(item["path"], item.get("status", "modified")) for item in listed]
    if args.paths_file:
        args.path += [line.strip() for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    entries += [(path, "deleted" if not (tree / path).exists() else "modified") for path in args.path]
    if not entries:
        print("REFUSED: no paths")
        return 1
    main_sha = git("rev-parse", args.main_ref).stdout.decode().strip()
    base_sha = git("rev-parse", args.base).stdout.decode().strip()
    snapshot = out / "snapshot"
    if snapshot.exists():
        shutil.rmtree(snapshot)
    snapshot.mkdir(parents=True)
    plan = {"main_ref": args.main_ref, "main_sha": main_sha, "base_sha": base_sha, "tree": str(tree), "paths": []}
    refused = []
    lines = []
    sums = []
    scratch = out / "three-way"
    scratch.mkdir(parents=True, exist_ok=True)
    main_copies = out / "main"
    if main_copies.exists():
        shutil.rmtree(main_copies)
    for path, status in entries:
        base_blob = blob(base_sha, path)
        main_blob = blob(main_sha, path)
        if main_blob is not None:
            (main_copies / path).parent.mkdir(parents=True, exist_ok=True)
            (main_copies / path).write_bytes(main_blob)
        if status == "deleted" or not (tree / path).exists():
            if base_blob != main_blob:
                refused.append(f"{path}: delete, but main moved it since the base")
            plan["paths"].append({"path": path, "action": "delete"})
            lines.append(f"delete {path}")
            continue
        target = snapshot / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if path in prebuilt:
            shutil.copy2(prebuilt[path], target)
            action = "prebuilt (rebuilt on main)"
        elif path in args.three_way:
            if base_blob is None or main_blob is None:
                refused.append(f"{path}: three-way needs the file in both the base and main")
                continue
            stem = path.replace("/", "__")
            (scratch / f"{stem}.base").write_bytes(base_blob)
            (scratch / f"{stem}.main").write_bytes(main_blob)
            shutil.copy2(tree / path, scratch / f"{stem}.carrier")
            merged = git("merge-file", "-p", str(scratch / f"{stem}.carrier"), str(scratch / f"{stem}.base"), str(scratch / f"{stem}.main"), check=False)
            if merged.returncode != 0:
                refused.append(f"{path}: git merge-file reported {merged.returncode} conflict(s)")
                continue
            target.write_bytes(merged.stdout)
            action = "three-way" if base_blob != main_blob else "three-way (main unchanged)"
        else:
            if base_blob != main_blob:
                refused.append(f"{path}: main moved it since the base; rebuild it three-way or re-derive it")
                continue
            shutil.copy2(tree / path, target)
            action = "carrier" if base_blob is not None else "carrier (added)"
        data = target.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        sums.append(f"{digest}  {path}")
        lines.append(f"add {path}")
        plan["paths"].append({"path": path, "action": action, "sha256": digest, "bytes": len(data)})
    plan["refused"] = refused
    (out / "plan.json").write_text(json.dumps(plan, indent=1) + "\n", encoding="utf-8")
    if refused:
        for reason in refused:
            print(f"REFUSED: {reason}")
        return 1
    (out / "paths.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "snapshot.sha256").write_text("\n".join(sums) + "\n", encoding="utf-8")
    for row in plan["paths"]:
        print(f"{row['action']:<28} {row['path']}")
    print(f"FROZEN on {args.main_ref} = {main_sha[:8]} (base {base_sha[:8]}): {len(lines)} paths -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
