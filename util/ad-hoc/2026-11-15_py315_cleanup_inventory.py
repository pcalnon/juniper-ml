#!/usr/bin/env python3
"""Inventory cleanup targets before removal: branch, merge signal, dirt, and what `git worktree remove` would delete.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-11-15
Status:      ad-hoc -- one-off (cleanup of the Python 3.15 migration arc's worktrees)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md (Phase 4);
             util/ad-hoc/2026-10-30_worktree_cleanup_keep_evidence.py (the owner's "evidence only" ruling of
             2026-10-30: keep tmp/ minus its regenerable parts);
             juniper-ml memory reference_worktree_remove_deletes_ignored_files.md

Why this exists
---------------
`git worktree remove` deletes ignored files without `--force`, and `git status --porcelain` cannot see them, so
"clean" does not mean "nothing is lost". Before any removal this reports, per target:

* the repository, branch and HEAD, and the pull request(s) whose head is that branch, with their state;
* the NON-ignored status lines. A dirty file is compared with the same path at the merged PR's head commit (blob
  SHA through the contents API), because the arc's signed API commits left some edits uncommitted in the tree that
  made them: a file identical to the merged head is work that already landed;
* every IGNORED entry with its size, classed REGEN (virtualenvs, bytecode and tool caches, build output: safe to
  lose) or KEEP (everything else: evidence, copied before removal under the 2026-10-30 ruling);
* for cascor, the count of `.h5` snapshots, which a removal would also delete.

It fails CLOSED: a git command that errors marks the target `ERROR`, never clean. Read-only: git and `gh` reads.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_cleanup_inventory.py --targets <file> --json <out.json>

Exit 0 when every target was inventoried, 1 when any target errored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess  # nosec B404
import sys
from pathlib import Path

OWNER = "pcalnon"
REGEN_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox", "node_modules", "htmlcov", ".hypothesis", "build", "dist", ".coverage"}
REGEN_SUFFIXES = (".egg-info", ".pyc")


def run(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)  # nosec B603
    return proc.returncode, proc.stdout, proc.stderr


def git(wt: Path, *args: str) -> str:
    rc, out, err = run(["git", "-C", str(wt), *args])
    if rc != 0:
        raise RuntimeError(f"git {' '.join(args)}: rc={rc}: {err.strip()}")
    return out


def size_of(path: Path) -> tuple[int, int]:
    if path.is_symlink() or path.is_file():
        try:
            return 1, path.lstat().st_size
        except OSError:
            return 1, 0
    files = total = 0
    for root, dirs, names in os.walk(path, followlinks=False):
        for n in names:
            files += 1
            try:
                total += (Path(root) / n).lstat().st_size
            except OSError:
                # The file vanished or is unreadable between the walk and the lstat. It still counts as a file;
                # its size is unknown, so it adds nothing to the byte total (a size, not a safety decision).
                pass
    return files, total


def is_regen(path: Path) -> bool:
    name = path.name.rstrip("/")
    if name in REGEN_NAMES or name.startswith(".coverage") or name.endswith(REGEN_SUFFIXES):
        return True
    if path.is_dir() and ((path / "pyvenv.cfg").exists() or (path / "conda-meta").is_dir()):
        return True
    return False


def classify_ignored(wt: Path, rel: str) -> list[dict]:
    """Split an ignored entry into REGEN and KEEP parts (one level down inside tmp/, logs/ and reports/)."""
    path = wt / rel.rstrip("/")
    rows = []
    if path.is_dir() and not is_regen(path) and path.name in {"tmp", "logs", "reports"}:
        for child in sorted(path.iterdir()):
            rows.extend(classify_ignored(wt, str(child.relative_to(wt)) + ("/" if child.is_dir() else "")))
        if not rows:
            rows.append({"path": rel, "class": "KEEP", "files": 0, "bytes": 0, "note": "empty directory"})
        return rows
    files, total = size_of(path)
    rows.append({"path": rel, "class": "REGEN" if is_regen(path) else "KEEP", "files": files, "bytes": total})
    return rows


def blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()


def remote_blob(repo: str, rel: str, ref: str) -> str | None:
    rc, out, _ = run(["gh", "api", f"repos/{OWNER}/{repo}/contents/{rel}?ref={ref}", "--jq", ".sha"])
    return out.strip() if rc == 0 and out.strip() else None


def inventory(wt: Path) -> dict:
    rec: dict = {"worktree": str(wt), "name": wt.name}
    try:
        url = git(wt, "remote", "get-url", "origin").strip()
        rec["repo"] = re.sub(r"\.git$", "", url.rsplit("/", 1)[-1].rsplit(":", 1)[-1])
        rec["branch"] = git(wt, "rev-parse", "--abbrev-ref", "HEAD").strip()
        rec["head"] = git(wt, "rev-parse", "HEAD").strip()
        status = git(wt, "status", "--porcelain=v1", "--untracked-files=all")
        ignored = git(wt, "status", "--porcelain=v1", "--ignored=matching", "--untracked-files=normal")
    except RuntimeError as exc:
        rec["state"] = f"ERROR: {exc}"
        return rec
    rc, out, err = run(["gh", "pr", "list", "--repo", f"{OWNER}/{rec['repo']}", "--head", rec["branch"], "--state", "all", "--json", "number,state,mergedAt,headRefOid"])
    rec["prs"] = json.loads(out) if rc == 0 else f"ERROR: {err.strip()}"
    merged = [p for p in rec["prs"] if isinstance(p, dict) and p.get("state") == "MERGED"] if isinstance(rec["prs"], list) else []
    merged_head = merged[0]["headRefOid"] if merged else None
    dirty = []
    for line in status.splitlines():
        code, rel = line[:2], line[3:]
        entry = {"code": code, "path": rel}
        if merged_head and code.strip() in {"M", "A", "??"} and (wt / rel).is_file():
            local, remote = blob_sha(wt / rel), remote_blob(rec["repo"], rel, merged_head)
            entry["equals_merged_head"] = remote is not None and local == remote
        dirty.append(entry)
    rec["dirty"] = dirty
    rows = []
    for line in ignored.splitlines():
        if line.startswith("!! "):
            rows.extend(classify_ignored(wt, line[3:]))
    rec["ignored"] = rows
    snaps = wt / "cascor-snapshots"
    rec["h5_snapshots"] = sum(1 for _ in snaps.rglob("*.h5")) if snaps.is_dir() else 0
    rec["state"] = "ok"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--targets", required=True, type=Path, help="one worktree path per line")
    ap.add_argument("--json", required=True, type=Path, help="where the full inventory is written")
    args = ap.parse_args()
    targets = [Path(t.strip()) for t in args.targets.read_text(encoding="utf-8").splitlines() if t.strip()]
    if not targets:
        print("REFUSED: the targets file is empty")
        return 1
    recs = [inventory(t) for t in targets]
    args.json.write_text(json.dumps(recs, indent=2) + "\n", encoding="utf-8")
    bad = 0
    for r in recs:
        if r["state"] != "ok":
            bad += 1
            print(f"ERROR  {r['name']}: {r['state']}")
            continue
        prs = ", ".join(f"#{p['number']} {p['state']}" for p in r["prs"]) if isinstance(r["prs"], list) else r["prs"]
        keep = [x for x in r["ignored"] if x["class"] == "KEEP"]
        regen_bytes = sum(x["bytes"] for x in r["ignored"] if x["class"] == "REGEN")
        keep_bytes = sum(x["bytes"] for x in keep)
        print(f"{r['repo']:22s} {r['branch']:40s} head={r['head'][:8]} PR: {prs or 'none'}")
        print(f"    dirty={len(r['dirty'])} {[(d['code'], d['path'], d.get('equals_merged_head')) for d in r['dirty']]}")
        print(f"    ignored: REGEN {regen_bytes / 1e6:.1f} MB; KEEP {len(keep)} entries, {keep_bytes / 1e6:.2f} MB; h5={r['h5_snapshots']}")
        for x in keep:
            print(f"      KEEP {x['path']}  ({x['files']} files, {x['bytes']} B){'  ' + x['note'] if x.get('note') else ''}")
    print(f"\n{len(recs)} targets, {bad} errored")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
