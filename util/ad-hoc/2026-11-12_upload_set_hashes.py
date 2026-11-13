#!/usr/bin/env python3
"""
Record, or verify, the sha256 of every file a fork PR of this arc will upload, and show each file's delta from origin/main.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- pre-upload freeze check for the telemetry and Retry-After fork PRs
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/open_signed_pr.py (uploads WHOLE files); the mutation checks
         util/ad-hoc/2026-11-12_fastapi_telemetry_opt_out_mutation_check.py and
         util/ad-hoc/2026-11-12_fork_retry_after_round_up_mutation_check.py (they edit a source file in place)

Why
---
``util/open_signed_pr.py`` uploads whole files from a worktree. Two things can make such a file wrong without anyone
editing it on purpose: a mutation run, or a validation lane, that edits the source in place and does not restore it;
and ``origin/main`` moving under the worktree, so that the upload reverts someone else's merge. This script answers
both before an upload:

* ``--record FILE`` writes ``{set name: {worktree, base, files: {path: sha256}}}`` for each named set of files, once
  they are final. It refuses a worktree whose HEAD is not ``origin/main``: the base it records is ``origin/main``,
  and a set built on an older commit would be uploaded over whatever ``main`` has gained since;
* ``--verify FILE`` re-hashes them and fails on any difference (a mutant left behind, an unplanned edit);
* ``--record`` also stores, per worktree, the ``origin/main`` commit the set was built on (its base) and prints
  ``git diff --stat <base> -- <paths>``; ``--verify`` (with ``--fetch`` to refresh ``origin`` first) names every
  uploaded path that ``origin/main`` has changed since that base, so a moved file is seen before it is uploaded.

Usage
-----
    python3 util/ad-hoc/2026-11-12_upload_set_hashes.py --record tmp/hashes.json --set NAME=WORKTREE:path[,path...] [...]
    python3 util/ad-hoc/2026-11-12_upload_set_hashes.py --verify tmp/hashes.json [--fetch]

Exit 0 when (verifying) every hash matches and no uploaded path moved on origin/main; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 -- git in argv form, no shell
from pathlib import Path


def git(worktree: str, *args: str) -> str:
    done = subprocess.run(["git", "-C", worktree, *args], capture_output=True, text=True, check=False)  # nosec B603 B607
    if done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed in {worktree}: {done.stderr.strip()}")
    return done.stdout


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--record", metavar="FILE")
    mode.add_argument("--verify", metavar="FILE")
    parser.add_argument("--set", dest="sets", action="append", default=[], metavar="NAME=WORKTREE:path[,path...]")
    parser.add_argument("--fetch", action="store_true", help="git fetch origin in each worktree's repository first")
    args = parser.parse_args(argv)

    if args.record:
        if not args.sets:
            parser.error("--record needs at least one --set")
        record: dict[str, dict] = dict()
        for item in args.sets:
            name, _, rest = item.partition("=")
            worktree, _, paths = rest.partition(":")
            if not name or not worktree or not paths:
                parser.error(f"--set wants NAME=WORKTREE:path[,path...], got {item!r}")
            if args.fetch:
                git(worktree, "fetch", "origin", "--quiet")
            base = git(worktree, "rev-parse", "origin/main").strip()
            # The base is only "what the set was built on" when the worktree is ON it. origin/main is a ref every
            # worktree of the repository shares, so any fetch moves it while this worktree's HEAD stays behind.
            head = git(worktree, "rev-parse", "HEAD").strip()
            if head != base:
                raise SystemExit(f"{name}: HEAD {head[:12]} is not origin/main {base[:12]}; these files were not built on the base being recorded. Re-home the worktree, then record.")
            files = dict((path, sha256(Path(worktree) / path)) for path in paths.split(","))
            record[name] = dict(worktree=worktree, base=base, files=files)
        out = Path(args.record)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        record = json.loads(Path(args.verify).read_text(encoding="utf-8"))

    problems = 0
    for name, entry in sorted(record.items()):
        worktree, base, files = entry["worktree"], entry["base"], entry["files"]
        if args.fetch and args.verify:
            git(worktree, "fetch", "origin", "--quiet")
        now_main = git(worktree, "rev-parse", "origin/main").strip()
        print(f"== {name}: {worktree}")
        print(f"   base {base[:12]}  origin/main now {now_main[:12]}{'' if base == now_main else '  (MOVED)'}")
        head_now = git(worktree, "rev-parse", "HEAD").strip()
        if head_now != base:
            problems += 1
            print(f"   HEAD {head_now[:12]} IS NOT THE RECORDED BASE: the files are not built on it")
        for path, expected in sorted(files.items()):
            actual = sha256(Path(worktree) / path)
            state = "ok" if actual == expected else "CHANGED"
            if actual != expected:
                problems += 1
            print(f"   {state:8s}{actual[:16]}  {path}")
        moved = [line for line in git(worktree, "diff", "--name-only", base, now_main, "--", *files).split("\n") if line]
        for path in moved:
            problems += 1
            print(f"   MOVED ON MAIN since the base: {path}")
        tracked = [path for path in files if git(worktree, "ls-files", "--", path).strip()]
        if tracked:
            for line in git(worktree, "diff", "--stat", base, "--", *tracked).rstrip().split("\n"):
                print(f"   {line}")
        for path in sorted(set(files) - set(tracked)):
            print(f"   (new file) {path}")
    print(f"result: {'OK' if not problems else 'PROBLEMS'} ({problems})")
    return 1 if (args.verify and problems) else 0


if __name__ == "__main__":
    raise SystemExit(main())
