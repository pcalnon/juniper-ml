#!/usr/bin/env python3
"""Run a lockfile-update.yml commit step against good and broken ``base64`` stand-ins and judge the result.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — investigation (flood-3 backlog rows B / E / H verification)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md §4 (the base64 row)

The defect: the commit step passed ``--arg contents "$(base64 -w0 <lock>)"`` to jq. A failure inside a
command substitution used as an ARGUMENT does not trip ``set -e``, so a failing or silent ``base64``
handed jq an empty string and the step went on to commit an empty lockfile. juniper-cascor-client and
juniper-cascor-worker have no test that runs this step, so this probe runs the workflow's OWN step
shell (extracted from the YAML, never re-implemented) in a throwaway git repo:

* the lockfile(s) are committed, then modified, so ``git diff --quiet`` sees a change;
* ``gh`` is a stub that logs its argv and answers a successful ``createCommitOnBranch``;
* the step's temp-directory prefix is rewritten to a scratch directory, so nothing is written to the system temp directory;
* ``base64`` is the host's GNU one (scenario ``real``) or a stand-in first on PATH that fails or
  prints nothing -- for every file, or for one named lockfile only (a pair must not half-commit).

``--expect fixed``: ``real`` commits once and each addition decodes to the file's bytes; every broken
scenario exits non-zero without calling gh. ``--expect defect``: at least one broken scenario calls gh
with an empty ``contents`` (the bug reproduced). Exit 0 when the expectation holds, 1 otherwise.

Usage:
    2026-10-26_flood3_backlog_commit_step_probe.py --workflow W --lock requirements.lock [--lock requirements-cpu.lock] --expect {fixed,defect}
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess  # nosec B404 - runs the workflow's own extracted step in a scratch repo
import sys
import tempfile
from pathlib import Path

import yaml

GH_STUB = """#!/bin/sh
printf '%s\\n' "$*" >> "$GH_LOG"
printf '%s' '{"data":{"createCommitOnBranch":{"commit":{"oid":"deadbeef","url":"https://example.invalid/commit/deadbeef"}}}}'
"""

FAILING = "#!/bin/sh\necho 'base64: simulated encode failure' >&2\nexit 1\n"
SILENT = "#!/bin/sh\nexit 0\n"


def _selective(target: str, broken_body: str) -> str:
    """A base64 that is broken only for ``target`` and defers to the host's GNU base64 otherwise."""
    broken = broken_body.split("\n", 1)[1]
    return f'#!/bin/sh\nif [ "$2" = "{target}" ]; then\n{broken}fi\nexec /usr/bin/base64 "$@"\n'


def _step_script(workflow: Path) -> str:
    doc = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    for job in doc["jobs"].values():
        for step in job.get("steps", []):
            if str(step.get("name", "")).startswith("Commit updated lockfile"):
                return step["run"]
    raise SystemExit(f"no 'Commit updated lockfile' step in {workflow}")


def _run(script: str, locks: list[str], base64_body: str | None, scratch: Path) -> dict:
    root = Path(tempfile.mkdtemp(prefix="scenario-", dir=scratch))
    repo, bin_dir, step_tmp = root / "repo", root / "bin", root / "step-tmp"
    for path in (repo, bin_dir, step_tmp):
        path.mkdir()
    env = {"PATH": f"{bin_dir}{os.pathsep}/usr/bin:/bin", "HOME": str(root), "LANG": "C", "GIT_CONFIG_NOSYSTEM": "1"}

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)  # nosec B603 B607 - fixed argv

    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    git("config", "commit.gpgsign", "false")
    for lock in locks:
        (repo / lock).write_text(f"{lock}==1\n", encoding="utf-8")
    git("add", *locks)
    git("commit", "-qm", "seed")
    new_bytes = {lock: f"{lock}==2\n# regenerated\n".encode() for lock in locks}
    for lock, data in new_bytes.items():
        (repo / lock).write_bytes(data)

    (bin_dir / "gh").write_text(GH_STUB, encoding="utf-8")
    (bin_dir / "gh").chmod(0o700)
    if base64_body is not None:
        (bin_dir / "base64").write_text(base64_body, encoding="utf-8")
        (bin_dir / "base64").chmod(0o700)
    if "/tmp/" not in script:  # tmp-path-literal: allow
        raise SystemExit("the step no longer writes under /tmp/; the relocation is stale")  # tmp-path-literal: allow
    relocated = script.replace("/tmp/", f"{step_tmp}/")  # tmp-path-literal: allow
    proc = subprocess.run(  # nosec B603 B607 - the workflow's own step, fixed bash argv
        ["bash", "-c", relocated],
        cwd=repo,
        env={**env, "GH_TOKEN": "probe-token-not-a-secret", "BRANCH": "dependabot/pip/probe", "GITHUB_REPOSITORY": "pcalnon/probe", "GH_LOG": str(root / "gh.log")},  # nosec B105
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    gh_called = (root / "gh.log").exists()
    additions: dict[str, bytes] = {}
    commit_json = step_tmp / "lockfile-commit.json"
    if commit_json.exists():
        payload = json.loads(commit_json.read_text(encoding="utf-8"))
        for item in payload["variables"]["input"]["fileChanges"]["additions"]:
            additions[item["path"]] = base64.b64decode(item["contents"])
    return {"rc": proc.returncode, "gh_called": gh_called, "additions": additions, "expected": new_bytes, "stdout": proc.stdout, "stderr": proc.stderr}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workflow", required=True, type=Path)
    parser.add_argument("--lock", action="append", required=True, dest="locks")
    parser.add_argument("--expect", required=True, choices=("fixed", "defect"))
    args = parser.parse_args(argv)

    script = _step_script(args.workflow)
    scenarios: list[tuple[str, str | None]] = [("real", None), ("fail-all", FAILING), ("silent-all", SILENT)]
    if len(args.locks) > 1:
        for lock in args.locks:
            scenarios += [(f"fail-{lock}", _selective(lock, FAILING)), (f"silent-{lock}", _selective(lock, SILENT))]

    scratch = Path(tempfile.mkdtemp(prefix="flood3-backlog-commit-probe-"))
    ok = True
    defect_seen = False
    try:
        for name, body in scenarios:
            got = _run(script, args.locks, body, scratch)
            empties = [path for path, data in got["additions"].items() if not data]
            line = f"{name:34s} rc={got['rc']:<3d} gh_called={str(got['gh_called']):5s} empty_additions={empties}"
            if name == "real":
                good = got["rc"] == 0 and got["gh_called"] and got["additions"] == got["expected"]
            else:
                good = got["rc"] != 0 and not got["gh_called"]
                if got["gh_called"] and empties:
                    defect_seen = True
            if args.expect == "fixed" and not good:
                ok = False
                line += "  <-- NOT FIXED"
                line += f"\n    stdout={got['stdout'].strip()[-200:]!r}\n    stderr={got['stderr'].strip()[-200:]!r}"
            if "error::" in got["stdout"]:
                line += f"  [{got['stdout'].strip().splitlines()[-1][:80]}]"
            print(line)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    if args.expect == "defect":
        print("DEFECT REPRODUCED" if defect_seen else "defect NOT reproduced")
        return 0 if defect_seen else 1
    print("FIXED: every broken encode stopped before gh" if ok else "NOT FIXED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
