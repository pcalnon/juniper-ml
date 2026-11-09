"""
Copy a flood-4 carrier's files from the builder's worktree into a validator's own worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier, round-2 validation (corrections and their blast radius)

Usage:
    python3 util/ad-hoc/2026-11-07_flood4_val_round2_setup.py MANIFEST DEST_ROOT [--include-adhoc] [--report PATH]

Reads MANIFEST (the builder's manifest.json), takes the builder's worktree from its
"worktree" key, reports that worktree's HEAD by reading its gitdir files (no git
command is run against it), and copies every listed file into DEST_ROOT. Files under
util/ad-hoc/ are skipped unless --include-adhoc is given. Prints, per file, the
sha256 of the source and of the copy, and whether the copy already matched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "-"


def _target_head(worktree: Path) -> str:
    dot_git = worktree / ".git"
    with open(dot_git, encoding="utf-8") as fh:
        line = fh.read().strip()
    gitdir = Path(line.split("gitdir:", 1)[1].strip())
    with open(gitdir / "HEAD", encoding="utf-8") as fh:
        return f"gitdir={gitdir} HEAD={fh.read().strip()}"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("dest_root")
    ap.add_argument("--include-adhoc", action="store_true")
    ap.add_argument("--report")
    args = ap.parse_args(argv)

    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)
    src_root = Path(manifest["worktree"])
    dest_root = Path(args.dest_root)
    lines = [f"manifest base_sha={manifest['base_sha']}", f"target {_target_head(src_root)}"]
    copied = skipped = 0
    for entry in manifest["files"]:
        rel = entry["path"]
        if rel.startswith("util/ad-hoc/") and not args.include_adhoc:
            skipped += 1
            lines.append(f"SKIP   {entry['status']:8} {rel}")
            continue
        src = src_root / rel
        dst = dest_root / rel
        before = _sha(dst)
        if entry["status"] == "deleted":
            if dst.exists():
                dst.unlink()
            lines.append(f"DELETE {rel}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        after = _sha(dst)
        same = "unchanged" if before == after else "changed"
        lines.append(f"COPY   {entry['status']:8} {rel} src={_sha(src)[:12]} dst={after[:12]} ({same})")
        copied += 1
    lines.append(f"copied={copied} skipped={skipped} total={len(manifest['files'])}")
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
