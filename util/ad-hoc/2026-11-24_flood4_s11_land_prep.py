#!/usr/bin/env python3
"""Freeze a change's files and probe the sequence-safety screens on them, before a signed upload (flood-4 session 11).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (the landing path of flood-4 session 11's pull requests)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md;
    util/ad-hoc/2026-11-23_flood4_s10_open_pr_from_paths.py (the signed upload that reads the frozen set);
    util/ad-hoc/2026-11-23_flood4_s10_verify_pr_blobs.py (the read-back);
    util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_seqsafety.py (the probe-commit idea this generalises)

freeze: copy each listed path from the working tree into <out>/final/<path>, and write <out>/paths.txt and
    <out>/final.sha256. A later upload reads only the frozen copies, so an edit made after the freeze cannot ride along.
seqsafety: build a tree from <base> plus the frozen copies in a private index (GIT_INDEX_FILE, so the checkout's
    index is untouched), make a dangling probe commit with `git commit-tree` carrying the commit body, and run CI's two
    screens on it with CI's scopes (ci.yml's "Sequence Safety" job): the symbol-loss screen over tests/*.py,
    util/**/*.py and util/**/*.bash, and the docs deletion-magnitude screen with no scope. The probe commit gets no
    ref and is never pushed. A path listed in --delete is removed from the probe tree.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s11_land_prep.py freeze --out DIR PATH [PATH ...]
    python3 util/ad-hoc/2026-11-24_flood4_s11_land_prep.py seqsafety --out DIR --base SHA --commit-body FILE [--delete PATH ...]
Exit 0 when the step succeeded and (seqsafety) both screens exit 0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 -- git plumbing and the two read-only screens, fixed argv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SYMBOL_SCOPES = ["--scope", "tests/*.py", "--scope", "util/**/*.py", "--scope", "util/**/*.bash"]


def _run(argv: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=REPO, env=env, capture_output=True, text=True, check=False, timeout=600)  # nosec B603


def _must(argv: list[str], env: dict[str, str] | None = None) -> str:
    done = _run(argv, env)
    if done.returncode != 0:
        raise SystemExit(f"failed ({done.returncode}): {' '.join(argv)}\n{done.stderr}")
    return done.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(out: Path, paths: list[str]) -> int:
    final = out / "final"
    if final.exists():
        shutil.rmtree(final)
    lines = []
    for rel in paths:
        src = REPO / rel
        if not src.is_file() or src.is_symlink():
            print(f"REFUSED: {rel} is not a regular file")
            return 1
        dst = final / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        lines.append(f"{_sha256(dst)}  {rel}")
    (out / "paths.txt").write_text("".join(f"{p}\n" for p in paths), encoding="utf-8")
    (out / "final.sha256").write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    print(f"frozen {len(paths)} files into {final.relative_to(REPO)}")
    for line in lines:
        print(" ", line[:16], line.split("  ", 1)[1])
    return 0


def seqsafety(out: Path, base: str, body: Path, deletes: list[str]) -> int:
    final = out / "final"
    paths = [p for p in (out / "paths.txt").read_text(encoding="utf-8").splitlines() if p]
    for line in (out / "final.sha256").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        if _sha256(final / rel) != digest:
            print(f"REFUSED: the frozen {rel} changed after the freeze")
            return 1
    index = out / "probe.index"
    if index.exists():
        index.unlink()
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    _must(["git", "read-tree", base], env)
    for rel in paths:
        blob = _must(["git", "hash-object", "-w", "--", str(final / rel)])
        mode = "100755" if os.access(final / rel, os.X_OK) else "100644"
        _must(["git", "update-index", "--add", "--cacheinfo", f"{mode},{blob},{rel}"], env)
    for rel in deletes:
        _must(["git", "update-index", "--force-remove", "--", rel], env)
    tree = _must(["git", "write-tree"], env)
    commit = _must(["git", "commit-tree", tree, "-p", base, "-F", str(body)])
    symbol = _run(["juniper-symbol-loss-check", *SYMBOL_SCOPES, "--base", base, "--head", commit])
    docs = _run(["juniper-docs-additions-check", "--base", base, "--head", commit])
    (out / "symbol.log").write_text(symbol.stdout + symbol.stderr, encoding="utf-8")
    (out / "docs.log").write_text(docs.stdout + docs.stderr, encoding="utf-8")
    changed = _must(["git", "diff-tree", "-r", "--name-status", base, commit]).splitlines()
    result = {
        "base": base,
        "probe_commit": commit,
        "tree": tree,
        "changed": changed,
        "symbol_exit": symbol.returncode,
        "docs_exit": docs.returncode,
    }
    (out / "seqsafety.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))
    for name, done in (("symbol", symbol), ("docs", docs)):
        tail = [line for line in done.stdout.splitlines() if "files_screened" in line or "FAIL" in line or "fail=" in line]
        print(f"{name}: exit {done.returncode}; {' | '.join(tail) if tail else '(no summary line)'}")
    return 0 if symbol.returncode == 0 and docs.returncode == 0 else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="step", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--out", required=True)
    f.add_argument("paths", nargs="+")
    s = sub.add_parser("seqsafety")
    s.add_argument("--out", required=True)
    s.add_argument("--base", required=True)
    s.add_argument("--commit-body", required=True)
    s.add_argument("--delete", action="append", default=[])
    args = parser.parse_args(argv)
    out = (REPO / args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.step == "freeze":
        return freeze(out, args.paths)
    return seqsafety(out, args.base, (REPO / args.commit_body).resolve(), args.delete)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
