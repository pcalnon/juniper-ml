#!/usr/bin/env python3
"""Find workflow steps that pipe a git listing into `grep -q` under pipefail: change detectors that can fail open.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-11-16
Status:      ad-hoc -- investigation (found while porting juniper-recurrence's `changes` detector to juniper-cascor#771)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-11-16_cascor_model_gate_logic_check.py (measured the fail-open with a 200,000-line list)

Why this exists
---------------
`git diff --name-only ... | grep -qE '<paths>'` under `set -o pipefail` can report "no match" for a list that DOES
match: grep -q exits at its first match, a git still writing the rest of a long list dies of SIGPIPE (141), and the
pipeline's status is then non-zero. In an `if`/`elif` condition that reads as "the package was not touched", so the
package jobs are skipped and an aggregate gate that passes on `skipped` reports success. Without pipefail the
pipeline's status is grep's alone, which is correct. GitHub's default `run:` shell on Linux is `bash -e {0}`, which
has no pipefail; an explicit `shell: bash` is `bash --noprofile --norc -eo pipefail {0}`, which has it, and so does a
`set -o pipefail` / `set -euo pipefail` line in the script.

This reads every workflow on each repo's default branch through `gh api` and prints each `run:` script that pipes a
`git` command into `grep -q`, with whether pipefail is on for it. Read-only: GET requests. Writes nothing.

Usage
-----
    python3 util/ad-hoc/2026-11-16_piped_grep_q_failopen_scan.py [--repo <bare-name> ...]

Exit 0 when every read succeeded (findings are printed, not failed on); 1 when any read failed.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess  # nosec B404
import sys

import yaml

OWNER = "pcalnon"
REPOS = [
    "juniper-ml", "juniper-cascor", "juniper-canopy", "juniper-data", "juniper-recurrence", "juniper-deploy",
    "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-harcot",
]
PIPEFAIL = re.compile(r"set\s+-[A-Za-z]*o\s+pipefail")  # set -o / -eo / -euo / -Eeuo pipefail


def gh(path: str) -> object:
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path}: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


def logical_lines(script: str) -> list[str]:
    """Join backslash-continued lines, so `git diff ... \\` + `| grep -q` reads as one pipeline."""
    out, buf = [], ""
    for line in script.splitlines():
        if line.rstrip().endswith("\\"):
            buf += line.rstrip()[:-1] + " "
            continue
        out.append(buf + line)
        buf = ""
    if buf:
        out.append(buf)
    return out


def findings_for(doc: dict) -> list[tuple[str, str, str, str]]:
    found = []
    defaults_shell = ((doc.get("defaults") or {}).get("run") or {}).get("shell")
    for job_id, job in (doc.get("jobs") or {}).items():
        job = job or {}
        job_shell = ((job.get("defaults") or {}).get("run") or {}).get("shell") or defaults_shell
        for idx, step in enumerate(job.get("steps") or []):
            script = step.get("run")
            if not isinstance(script, str):
                continue
            shell = step.get("shell") or job_shell
            pipefail = bool(PIPEFAIL.search(script)) or (isinstance(shell, str) and shell.strip() == "bash")
            for line in logical_lines(script):
                if re.search(r"\bgit\b[^|]*\|\s*grep\s+-[A-Za-z]*q", line):
                    label = step.get("name") or step.get("id") or f"step {idx}"
                    found.append((job_id, str(label), "pipefail ON" if pipefail else "no pipefail", line.strip()[:200]))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", action="append", help="limit to these bare repo names")
    args = ap.parse_args()
    failed = False
    for repo in args.repo or REPOS:
        try:
            listing = gh(f"repos/{OWNER}/{repo}/contents/.github/workflows?ref=main")
        except RuntimeError as exc:
            print(f"!! {repo}: {exc}")
            failed = True
            continue
        for entry in listing:
            if not entry["name"].endswith((".yml", ".yaml")):
                continue
            try:
                blob = gh(f"repos/{OWNER}/{repo}/contents/{entry['path']}?ref=main")
                doc = yaml.safe_load(base64.b64decode(blob["content"]).decode("utf-8")) or {}
            except (RuntimeError, yaml.YAMLError, KeyError) as exc:
                print(f"!! {repo}: {entry['name']}: {exc}")
                failed = True
                continue
            for job_id, label, pf, line in findings_for(doc):
                print(f"{repo:22s} {entry['name']:34s} job {job_id!r} step {label!r}: {pf}")
                print(f"      {line}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
