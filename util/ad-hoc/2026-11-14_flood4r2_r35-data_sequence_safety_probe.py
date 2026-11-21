#!/usr/bin/env python3
"""Build an unsigned, never-pushed `git commit-tree` probe of an uncommitted juniper-data tree and run CI's two
sequence-safety screens on it, with the scope juniper-data's .github/workflows/sequence-safety.yml passes.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use helper of the Cursor flood-4 disposition arc: the juniper-data back-port of the
             gitleaks pull-request scan's blocking-wiring pins)
Author:      Paul Calnon
Created:     2026-11-14
Status:      ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     juniper-data#530, juniper-data-client#260
Version:     0.1.0
License:     MIT License

The probe is built through a PRIVATE index file (GIT_INDEX_FILE under --out), so the worktree's own index and HEAD
are untouched: read-tree <base>, add the named paths from the working tree, write-tree, then
`git -c commit.gpgsign=false commit-tree <tree> -p <base>`. No ref points at the probe; nothing is pushed.

The screens are CI's console scripts (juniper-ci-tools): juniper-symbol-loss-check with --scope 'juniper_data/**',
and juniper-docs-additions-check with its default cluster, each run plainly and with --json, from the worktree.

Usage:
    python3 util/ad-hoc/2026-11-14_flood4r2_r35-data_sequence_safety_probe.py --worktree <checkout> --base <sha>
        --out <dir> --symbol-check <console script> --docs-check <console script> <path> [<path> ...]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404 -- runs git and the two screens with a fixed argv
import sys
from pathlib import Path

SYMBOL_SCOPE = "juniper_data/**"


def run(argv: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run one command and return it; never raises on a non-zero exit."""
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=600, check=False)  # nosec B603


def checked(argv: list[str], cwd: Path, env: dict[str, str]) -> str:
    """Run one git command that must succeed; return its stripped stdout."""
    proc = run(argv, cwd, env)
    if proc.returncode != 0:
        raise SystemExit(f"FATAL: {' '.join(argv)} exited {proc.returncode}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def main(argv: list[str]) -> int:
    """Build the probe, run both screens, write sequence_safety.json under --out."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--symbol-check", required=True)
    parser.add_argument("--docs-check", required=True)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    worktree = Path(args.worktree).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    index = out / "probe-index"
    if index.exists():
        index.unlink()
    git_env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    checked(["git", "read-tree", args.base], worktree, git_env)
    checked(["git", "add", "--", *args.paths], worktree, git_env)
    tree = checked(["git", "write-tree"], worktree, git_env)
    plain_env = {k: v for k, v in os.environ.items() if k != "GIT_INDEX_FILE"}
    probe = checked(["git", "-c", "commit.gpgsign=false", "commit-tree", tree, "-p", args.base, "-m", "probe: local sequence-safety screen input (never pushed)"], worktree, plain_env)
    changed = checked(["git", "diff", "--name-status", args.base, probe], worktree, plain_env).splitlines()
    result: dict[str, object] = {"base": args.base, "probe_commit": probe, "probe_tree": tree, "changed": changed, "screens": {}}
    screens = {
        "symbol": [args.symbol_check, "--base", args.base, "--head", probe, "--scope", SYMBOL_SCOPE],
        "docs": [args.docs_check, "--base", args.base, "--head", probe],
    }
    worst = 0
    for name, command in screens.items():
        plain = run(command, worktree, plain_env)
        as_json = run([*command, "--json"], worktree, plain_env)
        (out / f"{name}_screen.log").write_text(f"$ {' '.join(command)}\n(exit {plain.returncode})\n{plain.stdout}\n--- stderr ---\n{plain.stderr}", encoding="utf-8")
        (out / f"{name}_report.json").write_text(as_json.stdout, encoding="utf-8")
        result["screens"][name] = {"command": " ".join(command), "exit": plain.returncode, "json_exit": as_json.returncode, "log": str(out / f"{name}_screen.log"), "report": str(out / f"{name}_report.json")}
        worst = max(worst, plain.returncode)
        print(f"{name} screen exit {plain.returncode}; last lines:\n  " + "\n  ".join(plain.stdout.strip().splitlines()[-6:]))
    (out / "sequence_safety.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(f"probe {probe} (tree {tree}) over base {args.base}: {len(changed)} changed path(s)")
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
