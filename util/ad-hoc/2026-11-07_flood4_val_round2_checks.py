"""
Round-2 validation probes for the flood-4 juniper-ml tests carrier (base move, completeness, ci.yml).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier, round-2 validation (corrections and their blast radius)

Usage (run from the validator's own worktree root, which holds origin/main plus the copied carrier files):
    python3 util/ad-hoc/2026-11-07_flood4_val_round2_checks.py basemove MANIFEST OLD_BASE NEW_BASE
    python3 util/ad-hoc/2026-11-07_flood4_val_round2_checks.py inventory MANIFEST
    python3 util/ad-hoc/2026-11-07_flood4_val_round2_checks.py suites

basemove: paths OLD_BASE..NEW_BASE changed, intersected with the manifest's carrier paths.
inventory: every tracked file of HEAD whose bytes differ in the builder's worktree, and every
          untracked non-ignored-looking file there, against the manifest's file list.
suites:   the `python3 -m unittest` suites ci.yml's regression step runs (count, duplicates),
          versus docs/REFERENCE.md's "Running every suite" block and tests/ on disk.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def _manifest(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def basemove(manifest_path: str, old: str, new: str) -> int:
    changed = sorted(p for p in _git("diff", "--name-only", old, new).splitlines() if p)
    carrier = sorted(f["path"] for f in _manifest(manifest_path)["files"])
    both = sorted(set(changed) & set(carrier))
    print(f"{old[:8]}..{new[:8]} changed {len(changed)} paths:")
    for p in changed:
        print("  ", p)
    print(f"carrier paths: {len(carrier)}")
    print(f"intersection: {both if both else 'EMPTY'}")
    # Also: any carrier path whose blob at OLD differs from NEW (redundant with the diff, but explicit)
    moved = []
    for p in carrier:
        a = subprocess.run(["git", "rev-parse", "-q", "--verify", f"{old}:{p}"], capture_output=True, text=True).stdout.strip()
        b = subprocess.run(["git", "rev-parse", "-q", "--verify", f"{new}:{p}"], capture_output=True, text=True).stdout.strip()
        if a != b:
            moved.append((p, a[:10], b[:10]))
    print(f"carrier paths whose blob differs between {old[:8]} and {new[:8]}: {moved if moved else 'NONE'}")
    return 1 if both or moved else 0


def _blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # nosec B324 - git object id, not security


def complete(manifest_path: str) -> int:
    m = _manifest(manifest_path)
    target = Path(m["worktree"])
    listed = {f["path"] for f in m["files"]}
    tracked = {}
    for line in _git("ls-tree", "-r", "HEAD").splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, sha = meta.split()
        if kind == "blob":
            tracked[path] = (mode, sha)
    differ, missing = [], []
    for path, (mode, sha) in sorted(tracked.items()):
        tp = target / path
        if mode == "120000":
            continue
        if not tp.exists():
            missing.append(path)
            continue
        if tp.is_file() and _blob_sha(tp) != sha:
            differ.append(path)
    # untracked files in target, skipping tmp/, .git, caches, and the .claude dir
    skip_dirs = {".git", "tmp", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".claude", "node_modules", ".venv", "build", "dist"}
    untracked = []
    for p in target.rglob("*"):
        rel = p.relative_to(target)
        if any(part in skip_dirs or part.endswith(".egg-info") for part in rel.parts):
            continue
        if p.is_file() and str(rel) not in tracked:
            untracked.append(str(rel))
    print(f"tracked files differing in target: {len(differ)}")
    for p in differ:
        print("  ", "LISTED  " if p in listed else "UNLISTED", p)
    print(f"tracked files missing in target: {missing if missing else 'NONE'}")
    print(f"untracked files in target (outside tmp/ etc.): {len(untracked)}")
    for p in sorted(untracked):
        print("  ", "LISTED  " if p in listed else "UNLISTED", p)
    not_found = sorted(listed - set(differ) - set(untracked))
    print(f"manifest paths not seen as changed/added in target: {not_found if not_found else 'NONE'}")
    unlisted = [p for p in differ + untracked if p not in listed]
    return 1 if unlisted or not_found or missing else 0


_UNITTEST_RE = re.compile(r"python3? -m unittest(?: -v)? (tests/[A-Za-z0-9_./-]+\.py)")


def suites() -> int:
    ci = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    ci_list = _UNITTEST_RE.findall(ci)
    ref = Path("docs/REFERENCE.md").read_text(encoding="utf-8")
    start = ref.find("### Running every suite")
    block = ref[start:]
    nxt = block.find("\n## ", 10)
    block = block[: nxt if nxt != -1 else len(block)]
    ref_list = _UNITTEST_RE.findall(block)
    disk = sorted(str(p) for p in Path("tests").glob("test_*.py"))
    print(f"ci.yml unittest invocations: {len(ci_list)} (unique {len(set(ci_list))})")
    dups = sorted({x for x in ci_list if ci_list.count(x) > 1})
    print(f"ci.yml duplicates: {dups if dups else 'NONE'}")
    print(f"REFERENCE.md 'Running every suite' invocations: {len(ref_list)} (unique {len(set(ref_list))})")
    print(f"tests/test_*.py on disk: {len(disk)}")
    print(f"on disk, not in ci.yml: {sorted(set(disk) - set(ci_list))}")
    print(f"in ci.yml, not on disk: {sorted(set(ci_list) - set(disk))}")
    print(f"ci.yml vs REFERENCE order identical: {ci_list == ref_list}")
    print(f"in ci.yml not in REFERENCE: {sorted(set(ci_list) - set(ref_list))}; in REFERENCE not in ci.yml: {sorted(set(ref_list) - set(ci_list))}")
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[0]
    if cmd == "basemove":
        return basemove(argv[1], argv[2], argv[3])
    if cmd == "inventory":
        return complete(argv[1])
    if cmd == "suites":
        return suites()
    raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
