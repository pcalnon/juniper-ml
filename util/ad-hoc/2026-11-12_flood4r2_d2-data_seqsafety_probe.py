#!/usr/bin/env python3
"""
Run CI's two sequence-safety screens on a local, never-pushed probe commit of an uncommitted juniper-data tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (does the change need an Allow-Symbol-Loss / Allow-Docs-Rewrite trailer before it is pushed?)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md;
         adapted from 2026-11-12_flood4r2_s6_seqsafety_probe.py (which reads a frozen snapshot instead of a working tree)

Usage:
    python3 <this> --worktree <juniper-data tree> --tools-bin <dir holding the two console scripts> --out <dir>
                   --title <pr_title.txt> --body <commit_body.txt> --tag <name> [--main-ref origin/main]
                   [--trailer "Allow-Symbol-Loss: <value>" ...]

WHAT IT DOES
Reads the tree's uncommitted changes (``status --porcelain``: modified, added or untracked, and deleted paths; the
tree's own ignored files are not listed, so its scratch directory stays out), builds a tree object that is main's tree
with those paths applied -- through a private index file under --out, so the working tree, its index, HEAD and every
ref stay untouched -- and makes one commit of it with ``commit-tree``, parent main, message = the title, a blank line,
the body and any --trailer lines. The commit is dangling and is never pushed. It then runs, as
.github/workflows/sequence-safety.yml does at juniper-data c68e6b4c:

    juniper-symbol-loss-check --base <main> --head <probe> --scope 'juniper_data/**'
    juniper-docs-additions-check --base <main> --head <probe>

each a second time with ``--json``, and writes <out>/<tag>/{symbol.log,docs.log,symbol-report.json,docs-report.json,
result.json}. Exit 0 = both screens pass on the probe commit, 1 = a finding, 2 = an invocation error.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404 - fixed argv: the version-control client and two juniper-ci-tools console scripts
import sys
from pathlib import Path

SCOPE = "juniper_data/**"
VCS = "git"


def _run(argv: list[str], cwd: Path, env: dict[str, str] | None = None, data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=str(cwd), env=env, input=data, capture_output=True, check=False)  # nosec B603


def _must(argv: list[str], cwd: Path, env: dict[str, str] | None = None, data: bytes | None = None) -> str:
    done = _run(argv, cwd, env, data)
    if done.returncode != 0:
        raise SystemExit(f"command failed ({done.returncode}): {' '.join(argv)}\n{done.stderr.decode('utf-8', 'replace')}")
    return done.stdout.decode("utf-8", "replace")


def _changes(wt: Path) -> tuple[list[str], list[str]]:
    """(paths to take from the working tree, paths to remove), from ``status --porcelain -z``."""
    raw = _must([VCS, "status", "--porcelain", "-z", "--untracked-files=all"], wt)
    adds: list[str] = []
    deletes: list[str] = []
    entries = [e for e in raw.split("\0") if e]
    pending = ""
    for entry in entries:
        if pending:  # the origin path of a rename / copy record: a rename removes it, a copy keeps it
            if pending == "R":
                deletes.append(entry)
            pending = ""
            continue
        code, path = entry[:2], entry[3:]
        if code[0] in "RC":
            pending = code[0]
        if "D" in code and code != "RD":
            deletes.append(path)
        else:
            adds.append(path)
    return sorted(set(adds)), sorted(set(deletes) - set(adds))


def _screen(argv: list[str], cwd: Path, log: Path) -> int:
    done = _run(argv, cwd)
    text = done.stdout.decode("utf-8", "replace") + done.stderr.decode("utf-8", "replace")
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(f"$ {' '.join(argv)}\n{text}\nexit={done.returncode}\n")
    for line in text.splitlines():
        print("   " + line.rstrip()[:300])
    return done.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--tools-bin", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--title", type=Path, required=True)
    ap.add_argument("--body", type=Path, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--main-ref", default="origin/main")
    ap.add_argument("--trailer", action="append", default=[])
    args = ap.parse_args()
    wt = args.worktree.resolve()
    out = args.out.resolve() / args.tag
    out.mkdir(parents=True, exist_ok=True)
    symbol_tool = str(args.tools_bin.resolve() / "juniper-symbol-loss-check")
    docs_tool = str(args.tools_bin.resolve() / "juniper-docs-additions-check")
    for tool in (symbol_tool, docs_tool):
        if not Path(tool).is_file():
            print(f"MISSING TOOL: {tool}")
            return 2

    main_sha = _must([VCS, "rev-parse", args.main_ref], wt).strip()
    head_sha = _must([VCS, "rev-parse", "HEAD"], wt).strip()
    adds, deletes = _changes(wt)
    index = out / "probe.index"
    if index.exists():
        index.unlink()
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    _must([VCS, "read-tree", main_sha], wt, env)
    for path in deletes:
        _must([VCS, "update-index", "--force-remove", "--", path], wt, env)
    for path in adds:
        blob = _must([VCS, "hash-object", "-w", "--", path], wt).strip()
        listed = _must([VCS, "ls-tree", main_sha, "--", path], wt).strip()
        mode = listed.split()[0] if listed else "100644"
        _must([VCS, "update-index", "--add", "--cacheinfo", f"{mode},{blob},{path}"], wt, env)
    tree = _must([VCS, "write-tree"], wt, env).strip()
    index.unlink()

    with open(args.title, encoding="utf-8") as fh:
        title = fh.read().strip()
    with open(args.body, encoding="utf-8") as fh:
        body = fh.read().rstrip("\n")
    message = f"{title}\n\n{body}\n"
    if args.trailer:
        message += "\n" + "\n".join(args.trailer) + "\n"
    commit = _must([VCS, "commit-tree", tree, "-p", main_sha], wt, data=message.encode("utf-8")).strip()
    stat = _must([VCS, "diff", "--stat", "--find-renames", main_sha, commit], wt)
    print(f"probe commit {commit} (tree {tree[:12]}; {len(adds)} taken, {len(deletes)} removed) on {args.main_ref} {main_sha[:8]} -- dangling, never pushed")
    print(stat.rstrip())

    print("--- symbol-loss screen ---")
    symbol_argv = [symbol_tool, "--base", main_sha, "--head", commit, "--scope", SCOPE]
    symbol_rc = _screen(symbol_argv, wt, out / "symbol.log")
    with open(out / "symbol-report.json", "w", encoding="utf-8") as fh:
        fh.write(_run([*symbol_argv, "--json"], wt).stdout.decode("utf-8", "replace"))
    print("--- docs deletion-magnitude screen ---")
    docs_argv = [docs_tool, "--base", main_sha, "--head", commit]
    docs_rc = _screen(docs_argv, wt, out / "docs.log")
    with open(out / "docs-report.json", "w", encoding="utf-8") as fh:
        fh.write(_run([*docs_argv, "--json"], wt).stdout.decode("utf-8", "replace"))

    result = {"worktree": str(wt), "worktree_head": head_sha, "main_ref": args.main_ref, "main": main_sha, "probe_commit": commit, "tree": tree, "taken": adds, "removed": deletes, "trailers": args.trailer, "scope": SCOPE, "symbol_argv": symbol_argv, "symbol_exit": symbol_rc, "docs_argv": docs_argv, "docs_exit": docs_rc, "diff_stat": stat.splitlines()}
    with open(out / "result.json", "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print(f"symbol screen exit={symbol_rc} ; docs screen exit={docs_rc}")
    if symbol_rc >= 2 or docs_rc >= 2:
        return 2
    return 0 if symbol_rc == 0 and docs_rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
