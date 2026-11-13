#!/usr/bin/env python3
"""
Refresh the ml-code carrier's manifest for round 2 (the brace-sequence fix), with a sha256 per changed file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-code carrier, extended under the owner ruling "Carry in ml-code")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: 2026-11-08_flood4r2_ml_code_manifest.py (the builder's manifest, which this one extends);
         BRIEF_COMMON_R2 DELIVERABLES (manifest.json shape).

Usage (two phases; no git command runs here, so it works from a session isolated in another worktree):
  1. python3 -I <this> files <worktree> <base ls-tree file> <candidates out>
       <base ls-tree file> is `git ls-tree -r <base sha>` saved from any checkout of the same repository.
       Every file of the worktree (no .git, tmp/ or __pycache__) is hashed as a git blob and compared with the
       base: a different blob is "modified", a path the base lacks is a candidate "added", and a base path the
       worktree lacks is "deleted". The candidates are written one per line, for `git check-ignore`. A path that
       .gitattributes sends through `filter=lfs` holds the smudged file while the base blob is the LFS pointer,
       so those blob ids go to <candidates out>.lfs, one per line, for `git cat-file --batch`.
  2. python3 -I <this> assemble <worktree> <base ls-tree file> <ignored file> <lfs pointers> <builder manifest> <r2 json> <out>
       <ignored file> is what `git check-ignore --no-index --stdin` printed for the candidates (it may be empty);
       <lfs pointers> is what `git cat-file --batch` printed for the .lfs list: an LFS path is unchanged when its
       sha256 is the pointer's oid. <r2 json> holds the round-2 rows: {"extension": {...}, "checks": [...],
       "open_questions": [...], "swap_check_json": <path>, "mutation_logs": {"C8": <path>, ...}}; one mutation row
       is built per swap-check mutant and per KILLED / SURVIVED line of each log, after any rows given under
       "mutations". The builder's carried rows are kept as they are.
"""

import fnmatch
import hashlib
import json
import os
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__"}


def read_ls_tree(path: Path) -> dict:
    blobs = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            meta, _, name = line.rstrip("\n").partition("\t")
            parts = meta.split()
            if len(parts) == 3 and parts[1] == "blob":
                blobs[name] = parts[2]
    return blobs


def blob_sha1(path: Path) -> str:
    data = os.readlink(path).encode("utf-8") if path.is_symlink() else path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()


def sha256(path: Path) -> str:
    data = os.readlink(path).encode("utf-8") if path.is_symlink() else path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def walk(root: Path) -> list:
    """Every path git could track under ``root``: no .git, no top-level tmp/, no __pycache__ or .pyc."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        here = Path(dirpath)
        rel_dir = here.relative_to(root)
        keep = []
        for name in sorted(dirnames):
            if name in SKIP_DIRS or (rel_dir == Path(".") and name == "tmp"):
                continue
            if (here / name).is_symlink():
                out.append((rel_dir / name).as_posix())  # git stores a symlink to a directory as a blob
                continue
            keep.append(name)
        dirnames[:] = keep
        out.extend((rel_dir / name).as_posix() for name in filenames if name != ".git" and not name.endswith(".pyc"))
    return sorted(out)


def lfs_patterns(root: Path) -> list:
    path = root / ".gitattributes"
    if not path.exists():
        return []
    return [line.split()[0] for line in path.read_text(encoding="utf-8").splitlines() if "filter=lfs" in line.split()[1:]]


def compare(root: Path, base: dict) -> tuple:
    """(modified, candidate added, deleted, LFS paths whose blob differs as (path, base blob id))."""
    patterns = lfs_patterns(root)
    on_disk = walk(root)
    differ = [p for p in on_disk if p in base and blob_sha1(root / p) != base[p]]
    lfs = [(p, base[p]) for p in differ if any(fnmatch.fnmatchcase(p.rsplit("/", 1)[-1], pat) for pat in patterns)]
    modified = [p for p in differ if p not in {path for path, _ in lfs}]
    candidates = [p for p in on_disk if p not in base]
    deleted = sorted(p for p in base if not (root / p).is_symlink() and not (root / p).exists())
    return modified, candidates, deleted, lfs


def read_cat_file_batch(path: Path) -> dict:
    """Blob id -> text, from `git cat-file --batch` output."""
    data = path.read_bytes()
    out = {}
    pos = 0
    while pos < len(data):
        end = data.index(b"\n", pos)
        header = data[pos:end].decode("ascii").split()
        pos = end + 1
        if len(header) == 3 and header[1] == "blob":
            size = int(header[2])
            out[header[0]] = data[pos : pos + size].decode("utf-8", errors="replace")
            pos += size + 1
    return out


def lfs_changed(root: Path, lfs: list, pointers: dict) -> list:
    """The LFS paths whose file is not the object their base pointer names."""
    changed = []
    for path, blob in lfs:
        oid = next((line.split("sha256:", 1)[1].strip() for line in pointers.get(blob, "").splitlines() if line.startswith("oid sha256:")), None)
        if oid is None or sha256(root / path) != oid:
            changed.append(path)
    return changed


def mutation_rows(r2: dict) -> list:
    """Rows from the swap check's JSON (one per mutant) and from the guard's older mutation-check logs."""
    rows = list(r2.get("mutations", []))
    swap = r2.get("swap_check_json")
    if swap:
        with open(swap, encoding="utf-8") as fh:
            report = json.load(fh)
        log_dir = Path(swap).parent
        for m in report.get("mutants", []):
            targets = ", ".join(r["target"] for r in m.get("results", []))
            rows.append({"id": m["id"], "test_file": targets, "mutant": "%s: %r -> %r" % (m.get("file"), m.get("old"), m.get("new")), "result": m.get("verdict", "not run: " + m.get("error", "?")), "log": str(log_dir / (m["id"] + ".log"))})
    for check, log in sorted(r2.get("mutation_logs", {}).items()):
        for line in Path(log).read_text(encoding="utf-8").splitlines():
            parts = line.split(None, 2)
            if len(parts) == 3 and parts[0] in ("KILLED", "SURVIVED"):
                rows.append({"id": "%s-%s" % (check, parts[1]), "test_file": "tests/test_claude_agent_guard.py", "mutant": "%s %s: %s" % (check, parts[1], parts[2]), "result": parts[0].lower(), "log": log})
    return rows


def main(argv: list) -> int:
    if len(argv) >= 5 and argv[1] == "files":
        root, base = Path(argv[2]), read_ls_tree(Path(argv[3]))
        modified, candidates, deleted, lfs = compare(root, base)
        Path(argv[4]).write_text("".join(p + "\n" for p in candidates), encoding="utf-8")
        Path(argv[4] + ".lfs").write_text("".join(blob + "\n" for _, blob in lfs), encoding="utf-8")
        print("modified %d, candidate added %d, deleted %d, LFS paths to check against their pointers %d" % (len(modified), len(candidates), len(deleted), len(lfs)))
        return 0
    if len(argv) == 9 and argv[1] == "assemble":
        root, base = Path(argv[2]), read_ls_tree(Path(argv[3]))
        ignored = {line.strip() for line in Path(argv[4]).read_text(encoding="utf-8").splitlines() if line.strip()}
        pointers = read_cat_file_batch(Path(argv[5]))
        with open(argv[6], encoding="utf-8") as fh:
            manifest = json.load(fh)
        with open(argv[7], encoding="utf-8") as fh:
            r2 = json.load(fh)
        modified, candidates, deleted, lfs = compare(root, base)
        modified = sorted(modified + lfs_changed(root, lfs, pointers))
        added = [p for p in candidates if p not in ignored]
        files = [{"path": p, "status": "modified", "sha256": sha256(root / p)} for p in modified]
        files += [{"path": p, "status": "added", "sha256": sha256(root / p)} for p in added]
        files += [{"path": p, "status": "deleted"} for p in deleted]
        builder_paths = {row["path"] for row in manifest["files"]}
        manifest["files"] = files
        manifest["round2_extension"] = dict(r2["extension"], files_new_in_round2=sorted({row["path"] for row in files} - builder_paths), builder_files_absent_now=sorted(builder_paths - {row["path"] for row in files}))
        manifest["checks"] = r2["checks"]
        manifest["mutations"] = mutation_rows(r2)
        manifest["open_questions"] = r2["open_questions"]
        Path(argv[8]).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print("files: %d modified, %d added, %d deleted; %d checks, %d mutations" % (len(modified), len(added), len(deleted), len(manifest["checks"]), len(manifest["mutations"])))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
