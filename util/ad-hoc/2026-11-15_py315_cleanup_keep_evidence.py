#!/usr/bin/env python3
"""Copy the KEEP (evidence) entries of each cleanup target to a non-worktree root, verified, with a MANIFEST.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-11-15
Status:      ad-hoc -- one-off (cleanup of the Python 3.15 migration arc's worktrees)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     util/ad-hoc/2026-11-15_py315_cleanup_inventory.py (whose --json output this reads);
             util/ad-hoc/2026-10-30_worktree_cleanup_keep_evidence.py (the Overtoad's "evidence only" ruling of
             2026-10-30, which this applies to targets whose tracked edits are all proven landed)

Why this exists
---------------
`git worktree remove` deletes every ignored file. The Overtoad ruled on 2026-10-30 that a cleanup keeps "evidence
only": a target's `tmp/` (and any other ignored, non-regenerable output) is copied out first, without its
regenerable parts, and a MANIFEST names what was copied and what was skipped. The 2026-10-30 tool also classifies
tracked-but-modified files against the base and `main`; here the inventory already proved every modified file
equal to the merged pull request's head (or, for two CHANGELOGs, every added line present in it), so only the
ignored KEEP entries carry anything unique.

Regenerable, skipped and counted: any directory holding `pyvenv.cfg` or `conda-meta/` (a virtualenv or conda env),
`pre-commit-home` (a PRE_COMMIT_HOME cache), and any path with a `.mypy_cache`, `__pycache__`, `.pytest_cache` or
`.ruff_cache` component.

Every copied file is re-hashed (sha256) after the copy; a mismatch fails the run. MANIFEST rows
(`<dest>/MANIFEST.tsv`, appended): `worktree, verdict, path, sha256 | files/bytes`, verdict one of COPIED,
SKIPPED-REGEN, EMPTY-DIR.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_cleanup_keep_evidence.py --inventory <inventory.json> --dest <root>

Exit 0 when every copy verified; 1 on a mismatch or an unreadable file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

REGEN_COMPONENTS = {".mypy_cache", "__pycache__", ".pytest_cache", ".ruff_cache", "pre-commit-home"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_regen_dir(path: Path) -> bool:
    return path.name in REGEN_COMPONENTS or (path / "pyvenv.cfg").exists() or (path / "conda-meta").is_dir()


def tally(path: Path) -> tuple[int, int]:
    files = total = 0
    for root, _dirs, names in os.walk(path, followlinks=False):
        for n in names:
            files += 1
            try:
                total += (Path(root) / n).lstat().st_size
            except OSError:
                # The file vanished or is unreadable between the walk and the lstat. It is skipped either way (a
                # regenerable tree); only the MANIFEST's byte count loses its size.
                pass
    return files, total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", required=True, type=Path)
    ap.add_argument("--dest", required=True, type=Path)
    args = ap.parse_args()
    recs = json.loads(args.inventory.read_text(encoding="utf-8"))
    args.dest.mkdir(parents=True, exist_ok=True)
    manifest = args.dest / "MANIFEST.tsv"
    rows: list[tuple[str, str, str, str]] = []
    failures = 0
    for rec in recs:
        wt = Path(rec["worktree"])
        for entry in rec.get("ignored", []):
            if entry["class"] != "KEEP":
                continue
            top = wt / entry["path"].rstrip("/")
            if top.is_dir() and is_regen_dir(top) or any(part in REGEN_COMPONENTS for part in Path(entry["path"]).parts):
                f, b = tally(top) if top.is_dir() else (1, top.lstat().st_size)
                rows.append((rec["name"], "SKIPPED-REGEN", entry["path"], f"{f} files / {b} B"))
                continue
            walk = [(top, [], [top.name])] if top.is_file() or top.is_symlink() else None
            if walk is None:
                if not any(top.iterdir()):
                    rows.append((rec["name"], "EMPTY-DIR", entry["path"], "0 files / 0 B"))
                    continue
                for root, dirs, names in os.walk(top, followlinks=False):
                    rootp = Path(root)
                    for d in list(dirs):
                        if is_regen_dir(rootp / d):
                            f, b = tally(rootp / d)
                            rows.append((rec["name"], "SKIPPED-REGEN", str((rootp / d).relative_to(wt)) + "/", f"{f} files / {b} B"))
                            dirs.remove(d)
                    for n in names:
                        failures += copy_one(wt, rootp / n, args.dest / rec["name"], rows, rec["name"])
            else:
                failures += copy_one(wt, top, args.dest / rec["name"], rows, rec["name"])
    with manifest.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")
    copied = [r for r in rows if r[1] == "COPIED"]
    skipped = [r for r in rows if r[1] == "SKIPPED-REGEN"]
    print(f"COPIED {len(copied)} files; SKIPPED-REGEN {len(skipped)} trees; EMPTY-DIR {sum(1 for r in rows if r[1] == 'EMPTY-DIR')}; failures {failures}")
    print(f"manifest: {manifest}")
    return 1 if failures else 0


def copy_one(wt: Path, src: Path, dest_root: Path, rows: list, name: str) -> int:
    rel = src.relative_to(wt)
    dst = dest_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        if src.is_symlink():
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            os.symlink(os.readlink(src), dst)
            rows.append((name, "COPIED", str(rel), f"symlink -> {os.readlink(src)}"))
            return 0
        before = sha256(src)
        shutil.copy2(src, dst)
        after = sha256(dst)
    except OSError as exc:
        rows.append((name, "FAILED", str(rel), str(exc)))
        return 1
    if before != after:
        rows.append((name, "FAILED", str(rel), f"sha256 {before} != {after}"))
        return 1
    rows.append((name, "COPIED", str(rel), before))
    return 0


if __name__ == "__main__":
    sys.exit(main())
