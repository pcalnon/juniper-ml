"""
Run each repository's pinned pre-commit on exactly the files its D-14 carrier changes, and record whether any hook rewrote one.

For the juniper-ml carrier (this worktree) and the juniper-cascor carrier: the changed and untracked files from
``git status --porcelain --untracked-files=all`` (``tmp/`` skipped), then
``/opt/miniforge3/bin/pre-commit run --files <those paths>`` from that worktree's root, with the six Sentry variables
set to the empty string. The sha256 of every file before and after is compared, so a hook that fixes a file in place
is reported as a rewrite, not as a pass. Writes ``precommit_<repo>.log`` and ``precommit.json``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

PRE_COMMIT = "/opt/miniforge3/bin/pre-commit"
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")


def changed_paths(repo: Path, own: bool) -> list[str]:
    command = ["git", "status", "--porcelain", "--untracked-files=all"] if own else ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"]
    out = subprocess.run(command, cwd=repo if own else Path.cwd(), capture_output=True, text=True, check=True).stdout
    return [line[3:] for line in out.splitlines() if not line[3:].startswith("tmp/") and (repo / line[3:]).is_file()]


def digests(repo: Path, paths: list[str]) -> dict:
    return {path: hashlib.sha256((repo / path).read_bytes()).hexdigest() for path in paths}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--ml", type=Path, required=True)
    parser.add_argument("--cascor", type=Path, required=True)
    parser.add_argument("--log-dir", type=Path, required=True)
    args = parser.parse_args()
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}}
    summary = {}
    for name, repo, own in (("juniper-ml", args.ml, True), ("juniper-cascor", args.cascor, False)):
        paths = changed_paths(repo, own)
        before = digests(repo, paths)
        done = subprocess.run([PRE_COMMIT, "run", "--files", *paths], cwd=repo, env=env, capture_output=True, text=True, check=False)
        after = digests(repo, paths)
        log = args.log_dir / f"precommit_{name}.log"
        log.write_text(done.stdout + "\n--- stderr ---\n" + done.stderr, encoding="utf-8")
        rewritten = [path for path in paths if before[path] != after[path]]
        failed_hooks = [line.split("...")[0].strip() for line in done.stdout.splitlines() if line.rstrip().endswith("Failed")]
        summary[name] = {"files": paths, "exit": done.returncode, "failed_hooks": failed_hooks, "rewritten": rewritten, "log": str(log)}
        print(f"{name}: pre-commit exit {done.returncode}; {len(paths)} files; failed hooks {failed_hooks}; rewritten {rewritten}")
    with open(args.log_dir / "precommit.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1)
        handle.write("\n")


if __name__ == "__main__":
    main()
