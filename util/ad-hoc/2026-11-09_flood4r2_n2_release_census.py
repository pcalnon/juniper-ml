#!/usr/bin/env python3
"""Stop-then-start release census: which juniper-service-core release tags accept a start beside a stopped fit.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
             (juniper-service-core's stop-then-start race)

For every ``juniper-service-core-v*`` tag in the repository, reads
``juniper-service-core/juniper_service_core/lifecycle/manager.py`` at that tag (``git show``) and
reports whether the file exists, whether ``start_training`` clears the stop event, and whether it
refuses a start while the previous training thread is alive (``is_alive()`` inside
``start_training``). A tag whose ``start_training`` clears the stop and has no such refusal accepts
a start sent while a stopped run's ``fit`` is still running. Reads only; prints one JSON object.

Usage (from the juniper-ml worktree root):
    python3 util/ad-hoc/2026-11-09_flood4r2_n2_release_census.py [--ref <extra ref> ...]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANAGER = "juniper-service-core/juniper_service_core/lifecycle/manager.py"
_START = re.compile(r"\n    def start_training\(.*?(?=\n    def )", re.S)


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def _row(ref: str) -> dict[str, object]:
    shown = _git("show", f"{ref}:{MANAGER}")
    if shown.returncode != 0:
        return {"ref": ref, "manager": False}
    match = _START.search(shown.stdout)
    body = match.group(0) if match else ""
    clears = "self._stop_event.clear()" in body
    refuses = "is_alive()" in body
    return {"ref": ref, "manager": True, "start_training_found": bool(body), "clears_the_stop": clears, "refuses_while_alive": refuses, "accepts_a_start_beside_a_stopped_fit": clears and not refuses}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ref", action="append", default=[], help="an extra ref to report (a branch, a commit)")
    args = parser.parse_args(argv)
    tags = _git("tag", "-l", "juniper-service-core-v*", "--sort=version:refname")
    if tags.returncode != 0:
        print(tags.stderr, file=sys.stderr)
        return 2
    refs = [*tags.stdout.split(), *args.ref]
    print(json.dumps([_row(ref) for ref in refs], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
