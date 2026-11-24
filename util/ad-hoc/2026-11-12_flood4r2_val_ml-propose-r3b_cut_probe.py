#!/usr/bin/env python3
"""
Build a local probe commit of "main after a 0.11.5 cut that landed first", to rehearse the carrier's landing on it.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
Another arc has a juniper-ml 0.11.5 cut queued (the head commit of the open juniper-ml#2548 says it stepped aside
for it). If that release proposal lands before the ml-propose carrier, main's CHANGELOG.md has its [Unreleased]
entries under a new `## [0.11.5]` heading, and the three-way rebuild of the carrier's entry follows its neighbours
there. This builds that main as a dangling commit so the landing helper can be run against it with --dry-run:

* the tree is main's with the files a simulated patch proposal wrote (a sandbox of the simulator: pyproject.toml,
  CHANGELOG.md, README.md, AGENTS.md), and docs/REFERENCE.md with the three hand edits every 0.11.x cut made
  (the Version cell, the "declares" sentence, the "sets them to" clause moved to 0.11.5);
* it is made with a private index file and `git commit-tree`: no branch, ref or working tree is touched, nothing
  is pushed, and the commit is unsigned and unreachable.

Usage:
    python3 <this> --repo <own worktree at main> --sandbox <the simulator's main--patch sandbox> --out <dir>
Prints the probe commit's sha.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: plumbing in the validator's own worktree, with a private index file
import sys
from pathlib import Path

PROPOSAL_FILES = ("pyproject.toml", "CHANGELOG.md", "README.md", "AGENTS.md")
REFERENCE = "docs/REFERENCE.md"


def must(argv: list, cwd: Path, env: "dict | None" = None, data: "bytes | None" = None) -> str:
    done = subprocess.run(argv, cwd=cwd, env=env, input=data, capture_output=True, check=False)  # nosec B603
    if done.returncode != 0:
        raise SystemExit(f"failed ({done.returncode}): {' '.join(argv)}\n{done.stderr.decode('utf-8', 'replace')}")
    return done.stdout.decode("utf-8", "replace").strip()


def hand_cut(reference: str, old: str, new: str) -> str:
    """The three REFERENCE edits a cut made by hand: the Version cell, the sentence and the clause."""
    edits = (
        (re.compile(r"^(\| \*\*Version\*\*\s+\| `)" + re.escape(old) + r"(`\s*\|)$", re.MULTILINE), r"\g<1>" + new + r"\g<2>"),
        (re.compile(r"(`juniper-ml` )" + re.escape(old) + r"( declares the following pins\.)"), r"\g<1>" + new + r"\g<2>"),
        (re.compile(r"(?<![0-9.])" + re.escape(old) + r"( sets them to )"), new + r"\g<1>"),
    )
    for pattern, replacement in edits:
        reference, count = pattern.subn(replacement, reference)
        if count != 1:
            raise SystemExit(f"expected one site for {pattern.pattern!r}, found {count}")
    return reference


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--sandbox", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo, sandbox, out = args.repo.resolve(), args.sandbox.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    main_sha = must(["git", "rev-parse", "HEAD"], repo)
    index = out / "probe.index"
    index.unlink(missing_ok=True)
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    must(["git", "read-tree", main_sha], repo, env)
    staged = {}
    main_reference = subprocess.run(["git", "show", f"{main_sha}:{REFERENCE}"], cwd=repo, capture_output=True, check=True).stdout  # nosec B603 B607
    reference = hand_cut(main_reference.decode("utf-8"), "0.11.4", "0.11.5")
    (out / "REFERENCE.after-cut.md").write_bytes(reference.encode("utf-8"))
    sources = {path: sandbox / path for path in PROPOSAL_FILES}
    sources[REFERENCE] = out / "REFERENCE.after-cut.md"
    for path, source in sources.items():
        blob = must(["git", "hash-object", "-w", "--", str(source)], repo)
        mode = must(["git", "ls-tree", main_sha, "--", path], repo).split()[0]
        must(["git", "update-index", "--add", "--cacheinfo", f"{mode},{blob},{path}"], repo, env)
        staged[path] = blob
    tree = must(["git", "write-tree"], repo, env)
    index.unlink()
    message = b"probe: main after a simulated juniper-ml 0.11.5 cut (validator rehearsal; never pushed)\n"
    commit = must(["git", "commit-tree", tree, "-p", main_sha], repo, data=message)
    (out / "probe.json").write_text(json.dumps({"main": main_sha, "probe_commit": commit, "tree": tree, "files": staged, "sandbox": str(sandbox)}, indent=1) + "\n", encoding="utf-8")
    print(commit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
