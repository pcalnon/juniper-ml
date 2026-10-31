#!/usr/bin/env python3
"""
Preserve a cleanup target's evidence before its removal: every file outside ``tmp/`` that never existed on ``main``,
and all of ``tmp/`` except the regenerable parts, with a MANIFEST of what was copied and what was skipped.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-30
Status: ad-hoc — one-off (flood-3 cleanup of 2026-10-30)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-26_worktree_blob_classify.py (whose ``listing`` and ``blob_id`` this reuses);
         util/ad-hoc/2026-10-26_worktree_preserve_unique.py and 2026-10-29_cleanup_skipped_suffix_sweep.py (the
         two steps this folds together); notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§6)

Why this exists
---------------
The owner ruled on 2026-10-30 that the cleanup keeps "evidence only": each target's ``tmp/`` is copied to
``juniper-ml/tmp/worktree-cleanup-2026-10-30/`` without its regenerable parts (virtualenvs, bytecode caches,
pytest temp dirs, and canopy's export and tar of its base commit), and a MANIFEST names what was skipped. About
480 MB of the 500 MB in those ``tmp/`` folders is regenerable. The 2026-10-26 classifier cannot express that: it
hashes everything under ``tmp/`` (a ``venv-*`` folder is not in its skip list) and it skips image and PDF suffixes
everywhere. So this:

- outside ``tmp/``, classifies each file against the target's base tree and ``main`` the way the classifier does,
  and copies every MODIFIED or UNTRACKED file whose blob never existed in ``main``'s history (``*/UNIQUE``). An
  image or PDF is copied when the base tree lacks it or holds another blob (an LFS pointer included), never
  silently skipped;
- inside ``tmp/``, copies every file and symlink except the regenerable parts, which it records as
  ``SKIPPED-REGEN`` rows with their file count and size;
- re-hashes every copy and reports any mismatch.

It runs no git command: the listings are made beforehand, in any checkout of the same repository.

    python3 -I util/ad-hoc/2026-10-30_worktree_cleanup_keep_evidence.py <dest-root> <targets.tsv>

``targets.tsv`` rows: ``<worktree>\\t<base ls-tree listing>\\t<main ls-tree listing>\\t<main rev-list --objects>``,
with an optional fifth column, ``git lfs ls-files -l <base>``. In a repository that stores images in LFS the tree
holds pointer blobs, so every image on disk differs from its tree entry; with the fifth column a file whose sha256
equals its LFS oid counts as unchanged. (juniper-ml's test run without it copied all 99 of its LFS images.)
MANIFEST rows (appended to ``<dest-root>/MANIFEST.tsv``): ``worktree, state, verdict, path, sha256 or count/bytes``.
Exit 0 when every copy verified, 1 on a mismatch or unreadable file, 2 on bad arguments.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGEN_DIR_NAMES = {"pycache", "__pycache__", "tmpdir", "pytest-tmp", "base-export"}
SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "node_modules"}


def _load_classifier():
    spec = importlib.util.spec_from_file_location("worktree_blob_classify", HERE / "2026-10-26_worktree_blob_classify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    if p.is_symlink():
        h.update(os.readlink(p).encode())
        return h.hexdigest()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def regen_reason(path: Path, name: str) -> str | None:
    """Why a tmp/ entry is regenerable, or None when it is evidence."""
    if path.is_dir() and not path.is_symlink():
        if name in REGEN_DIR_NAMES:
            return name
        if (path / "pyvenv.cfg").exists():
            return "venv"
    elif name.startswith("base-") and name.endswith(".tar"):
        return "base-tar"
    return None


def tree_size(root: Path) -> tuple[int, int]:
    files = size = 0
    for dirpath, _dirnames, filenames in os.walk(root):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            files += 1
            if not os.path.islink(fp):
                size += os.path.getsize(fp)
    return files, size


def copy_one(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_symlink():
        if dst.is_symlink() or dst.exists():
            dst.unlink()
        os.symlink(os.readlink(src), dst)
    else:
        shutil.copy2(src, dst)


def lfs_listing(path: str) -> dict:
    """Parse `git lfs ls-files -l` output into {path: sha256 oid}."""
    out = {}
    for line in Path(path).read_text().splitlines():
        oid, _, rest = line.partition(" ")
        if rest[:2] in ("* ", "- "):
            out[rest[2:]] = oid
    return out


class Target:
    def __init__(self, wt: Path, base: dict, main_: dict, history: set, dest: Path, clf, lfs: dict | None = None) -> None:
        self.wt, self.base, self.main, self.history, self.dest, self.clf = wt, base, main_, history, dest, clf
        self.lfs = lfs or {}
        self.rows: list[tuple[str, str, str, str]] = []
        self.copied: list[tuple[Path, Path, str]] = []
        self.errors: list[str] = []

    def keep(self, rel: str, state: str, verdict: str) -> None:
        src, dst = self.wt / rel, self.dest / self.wt.name / rel
        try:
            digest = sha256(src)
            copy_one(src, dst)
        except OSError as exc:
            self.errors.append(f"{rel}: {exc}")
            return
        self.copied.append((src, dst, digest))
        self.rows.append((state, verdict, rel, digest))

    def outside_tmp(self) -> None:
        for dirpath, dirnames, filenames in os.walk(self.wt):
            here = Path(dirpath)
            if here == self.wt:
                dirnames[:] = [d for d in dirnames if d != "tmp"]
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")]
            for f in filenames:
                p = here / f
                rel = str(p.relative_to(self.wt))
                if rel == self.clf.POINTER:
                    continue
                if rel in self.lfs:
                    try:
                        if sha256(p) == self.lfs[rel]:
                            continue  # the LFS object the base tree points at
                    except OSError as exc:
                        self.errors.append(f"{rel}: {exc}")
                        continue
                    self.keep(rel, "MODIFIED", "LFS")
                    continue
                try:
                    bid = self.clf.blob_id(p)
                except OSError as exc:
                    self.errors.append(f"{rel}: {exc}")
                    continue
                if self.base.get(rel) == bid:
                    continue
                state = "MODIFIED" if rel in self.base else "UNTRACKED"
                if p.suffix.lower() in self.clf.LFS_EXT:
                    self.keep(rel, state, "EXT")  # never skipped: the classifier would have
                    continue
                if self.main.get(rel) == bid or bid in self.history:
                    self.rows.append((state, "SAME" if self.main.get(rel) == bid else "HIST", rel, "-"))
                    continue
                self.keep(rel, state, "UNIQUE")

    def tmp(self) -> None:
        root = self.wt / "tmp"
        if not root.is_dir():
            return
        for dirpath, dirnames, filenames in os.walk(root):
            here = Path(dirpath)
            kept_dirs = []
            for d in dirnames:
                p = here / d
                rel = str(p.relative_to(self.wt))
                if p.is_symlink():
                    self.keep(rel, "TMP", "SYMLINK")
                    continue
                reason = regen_reason(p, d)
                if reason:
                    files, size = tree_size(p)
                    self.rows.append(("TMP", f"SKIPPED-REGEN:{reason}", rel + "/", f"{files} files / {size} bytes"))
                    continue
                kept_dirs.append(d)
            dirnames[:] = kept_dirs
            for f in filenames:
                p = here / f
                rel = str(p.relative_to(self.wt))
                reason = regen_reason(p, f)
                if reason:
                    files, size = 1, (0 if p.is_symlink() else p.stat().st_size)
                    self.rows.append(("TMP", f"SKIPPED-REGEN:{reason}", rel, f"{files} files / {size} bytes"))
                    continue
                self.keep(rel, "TMP", "COPIED")

    def verify(self) -> int:
        bad = 0
        for src, dst, digest in self.copied:
            if sha256(dst) != digest:
                self.errors.append(f"MISMATCH {dst}")
                bad += 1
        return bad


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    dest_root, targets = Path(sys.argv[1]), Path(sys.argv[2])
    clf = _load_classifier()
    dest_root.mkdir(parents=True, exist_ok=True)
    status = 0
    with (dest_root / "MANIFEST.tsv").open("a", encoding="utf-8") as manifest:
        for line in targets.read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            cols = line.split("\t")
            wt_s, base_s, main_s, objects_s = cols[:4]
            lfs = lfs_listing(cols[4]) if len(cols) > 4 and cols[4] else None
            history = {row.split()[0] for row in Path(objects_s).read_text().splitlines() if row}
            t = Target(Path(wt_s), clf.listing(base_s), clf.listing(main_s), history, dest_root, clf, lfs)
            t.outside_tmp()
            t.tmp()
            bad = t.verify()
            for state, verdict, rel, extra in t.rows:
                manifest.write(f"{t.wt.name}\t{state}\t{verdict}\t{rel}\t{extra}\n")
            kinds: dict[str, int] = {}
            for state, verdict, _rel, _extra in t.rows:
                kinds[f"{state}:{verdict.split(':')[0]}"] = kinds.get(f"{state}:{verdict.split(':')[0]}", 0) + 1
            print(f"{t.wt.name}\tcopied={len(t.copied)}\tverified_bad={bad}\terrors={len(t.errors)}\t{sorted(kinds.items())}")
            for err in t.errors:
                print(f"  ERROR {err}")
            if bad or t.errors:
                status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
