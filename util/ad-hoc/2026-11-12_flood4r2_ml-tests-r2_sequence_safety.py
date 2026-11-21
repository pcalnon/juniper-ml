#!/usr/bin/env python3
"""
Run CI's two sequence-safety screens on the carrier's uncommitted tree, through a `git commit-tree` probe.

The carrier is never committed by its builder (a signed commit needs the Overtoad's key), but both screens compare
two commits. So the working tree is written as a tree object through a THROWAWAY index (the checkout's own index
and HEAD are not touched), and `git commit-tree` makes one unsigned, never-pushed, unreferenced commit of it on
top of --base. The screens then run exactly as ci.yml runs them:

    juniper-symbol-loss-check --scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash' --base B --head P
    juniper-docs-additions-check --base B --head P

With --message-file the probe's commit message is that file (a commit body with an `Allow-Symbol-Loss:` trailer is
how a finding is waived, so the second run shows the trailer is the one the screen accepts).

Writes <out>/sequence_safety.json and one log per screen. Exit 0 when both screens exit 0.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_sequence_safety.py --base origin/main --out <dir>
        [--message-file <file>] [--tag <name>]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: .github/workflows/ci.yml (the two screens); auto-memory reference_sequence_safety_local_repro.md
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCOPES = ("tests/*.py", "util/**/*.py", "util/**/*.bash")


def _git(*argv: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], capture_output=True, text=True, check=False, env=env)


def _equals_working_tree(probe: str) -> bool:
    """True when the probe's tree differs from HEAD's on exactly the paths `status` lists, each with the working file's blob id.

    `diff <probe>` alone cannot answer this: it ignores a new file that is not in the checkout's index, so the
    answer depended on whether the new files had been marked intent-to-add.
    """
    env = os.environ.copy()
    changed = sorted(path for path in _git("diff", "--no-renames", "--name-only", "-z", "HEAD", probe, env=env).stdout.split("\0") if path)
    listed = sorted(entry[3:] for entry in _git("status", "--porcelain", "--untracked-files=all", "-z", env=env).stdout.split("\0") if entry)
    if changed != listed:
        return False
    for path in changed:
        if not Path(path).is_file() or _git("rev-parse", f"{probe}:{path}", env=env).stdout.strip() != _git("hash-object", "--", path, env=env).stdout.strip():
            return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--out", required=True)
    ap.add_argument("--message-file")
    ap.add_argument("--tag", default="probe")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    index = out / f"{args.tag}.index"
    index.unlink(missing_ok=True)
    env = {**os.environ, "GIT_INDEX_FILE": str(index.resolve())}
    for step in (("read-tree", "HEAD"), ("add", "-A", ".")):
        done = _git(*step, env=env)
        if done.returncode != 0:
            raise SystemExit(f"git {' '.join(step)}: {done.stderr.strip()}")
    tree = _git("write-tree", env=env).stdout.strip()
    message = Path(args.message_file).read_text(encoding="utf-8") if args.message_file else "probe: the ml-tests carrier's uncommitted tree (never pushed)\n"
    base_sha = _git("rev-parse", args.base, env=os.environ.copy()).stdout.strip()
    probe = subprocess.run(["git", "commit-tree", tree, "-p", base_sha, "-F", "-"], input=message, capture_output=True, text=True, check=True).stdout.strip()
    index.unlink(missing_ok=True)
    same = _equals_working_tree(probe)
    screens = {
        "symbol_loss": ["juniper-symbol-loss-check", *[arg for scope in SCOPES for arg in ("--scope", scope)], "--base", base_sha, "--head", probe],
        "docs_additions": ["juniper-docs-additions-check", "--base", base_sha, "--head", probe],
    }
    report = {"base": base_sha, "probe": probe, "tree": tree, "probe_equals_working_tree": same, "message_file": args.message_file, "screens": {}}
    for name, argv in screens.items():
        done = subprocess.run(argv, capture_output=True, text=True, check=False)
        log = out / f"{args.tag}_{name}.log"
        log.write_text(done.stdout + done.stderr, encoding="utf-8")
        report["screens"][name] = {"command": " ".join(argv), "rc": done.returncode, "log": str(log)}
        print(f"{name}: rc={done.returncode} ({log})")
    with open(out / f"{args.tag}_sequence_safety.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"probe {probe} on {base_sha[:8]}; equals the working tree: {same}")
    return 0 if all(screen["rc"] == 0 for screen in report["screens"].values()) and same else 1


if __name__ == "__main__":
    sys.exit(main())
