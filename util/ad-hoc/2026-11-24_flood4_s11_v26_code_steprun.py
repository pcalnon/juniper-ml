#!/usr/bin/env python3
"""Run a lockfile-update.yml commit step (main vs frozen) under both runner shells and compare (V26 CODE lens).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (validation of the ruling-26 lockfile-print ports; tmp/flood4/session11/r26/val_code/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session11/briefs/V26_ports_validator.txt (CODE lens: "Does the success path stay byte-identical?",
    the `bash -e {0}` default vs `shell: bash`); juniper-canopy#814

Independent of every repository's own tests. For each scenario, each shell and each variant (main, frozen) it:
  - builds a git repository under --out holding the step's locks (read from the step's own `base64 -w0 FILE` lines),
    regenerates the first lock unless the scenario says unchanged;
  - puts a stub `gh` first on PATH that logs its argv, prints the scenario's body on stdout, then its message on stderr,
    then exits with the scenario's status (the real CLI's order);
  - rewrites every occurrence of the runner's temp prefix in the step into the scenario's own scratch directory and
    REFUSES to run if any temp-prefix path is left (the prefix is passed in as --runner-tmp, so this file names none);
  - runs the step as `bash -e FILE` (no `shell:` key) and `bash --noprofile --norc -eo pipefail FILE` (`shell: bash`).
Then it compares main vs frozen byte for byte (stdout, stderr, exit status, request body, gh argv) for the scenarios
whose output must not change, and records every run for the others.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_code_steprun.py --main WF --frozen WF --runner-tmp PREFIX \
        --out DIR --label NAME
Exit 0 when every must-not-change scenario is identical under both shells and every failure scenario of the frozen
variant prints its diagnostic and exits 1; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess  # nosec B404 -- runs bash and git with fixed argv
import sys
from pathlib import Path

import yaml

TOKEN = "steprun-token-not-a-credential"  # nosec B105 -- a stand-in the step must never print
REPO_NAME = "pcalnon/example"
BRANCH = "dependabot/pip/example"
SIGNED = json.dumps({"data": {"createCommitOnBranch": {"commit": {"oid": "abc123", "url": "https://example.test/commit/abc123"}}}})
STALE = 'Expected branch to point to "abc" but it did not. Pull and try again.'
SHELLS = {
    "default-bash-e": ["bash", "-e"],
    "shell-bash": ["bash", "--noprofile", "--norc", "-eo", "pipefail"],
}
GH_STUB = """#!/bin/bash
{ printf '%s' gh; for a in "$@"; do printf '\\t%s' "$a"; done; printf '\\n'; } >> "$GH_LOG"
printf '%s' "${GH_STDOUT-}"
if [ -n "${GH_ERR-}" ]; then printf '%s' "${GH_ERR}" >&2; fi
exit "${GH_RC:-0}"
"""
# name: (changed, stdout body, stderr text, gh exit, must the output stay identical to main?)
SCENARIOS = {
    "success": (True, SIGNED, "", 0, True),
    "success-gh-stderr-newline": (True, SIGNED, "gh: notice on a success\n", 0, False),
    "success-gh-stderr-no-newline": (True, SIGNED, "gh: notice on a success", 0, False),
    "unchanged": (False, SIGNED, "", 0, True),
    "graphql-error-exit-1": (True, json.dumps({"data": {"createCommitOnBranch": None}, "errors": [{"type": "STALE_DATA", "message": STALE}]}), f"gh: {STALE}\n", 1, False),
    "http-502-exit-1": (True, "<html>502 Bad Gateway</html>\n", "gh: HTTP 502\n", 1, False),
    "http-401-exit-1": (True, json.dumps({"message": "Bad credentials", "status": "401"}), "gh: Bad credentials (HTTP 401)\n", 1, False),
    "no-token-exit-4": (True, "", "gh: To use GitHub CLI in a GitHub Actions workflow, set the GH_TOKEN environment variable.\n", 4, False),
    "errors-without-message-exit-0": (True, json.dumps({"errors": [{"type": "X"}]}), "", 0, False),
    "token-in-gh-output-exit-1": (True, json.dumps({"errors": [{"type": "FORBIDDEN", "message": f"token {TOKEN} lacks access ({TOKEN})"}]}), f"gh: token {TOKEN} lacks access ({TOKEN})\n", 1, False),
}


def _step_run(path: Path) -> str:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for job in data["jobs"].values():
        for step in job.get("steps", []):
            if str(step.get("name", "")).startswith("Commit updated lockfile"):
                return step["run"]
    raise SystemExit(f"no commit step in {path}")


def _git(repo: Path, *args: str) -> None:
    # Fixed dates: the request body carries expectedHeadOid, so main's and the frozen run's HEAD must be the same commit.
    env = {"PATH": os.environ["PATH"], "HOME": str(repo.parent), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z", "GIT_CEILING_DIRECTORIES": str(repo.parent)}
    proc = subprocess.run(["git", *args], cwd=repo, env=env, capture_output=True, text=True, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise SystemExit(f"git {args} failed: {proc.stderr}")


def _one(run_text: str, runner_tmp: str, scenario: str, shell: str, root: Path) -> dict:
    changed, body, err, rc, _same = SCENARIOS[scenario]
    if root.exists():
        shutil.rmtree(root)
    repo, scratch, bindir, tmpdir = root / "repo", root / "scratch", root / "bin", root / "tmp"
    for d in (repo, scratch, bindir, tmpdir):
        d.mkdir(parents=True)
    # `LOCK_B64=$(base64 -w0 requirements.lock)`: stop at the `)` that closes the substitution.
    locks = re.findall(r"base64 -w0 ([^\s)]+)", run_text)
    if not locks:
        raise SystemExit("no `base64 -w0 FILE` line in the step")
    _git(repo, "init", "-q")
    _git(repo, "config", "commit.gpgsign", "false")
    for lock in locks:
        (repo / lock).write_text(f"# {lock}\npackage==1.0.0\n", encoding="utf-8")
    _git(repo, "add", *locks)
    _git(repo, "commit", "-q", "-m", "base")
    if changed:
        (repo / locks[0]).write_text("# regenerated\npackage==2.0.0\n", encoding="utf-8")
    (bindir / "gh").write_text(GH_STUB, encoding="utf-8")
    (bindir / "gh").chmod(0o700)
    script = run_text.replace(runner_tmp, f"{scratch}/")
    if runner_tmp.rstrip("/") in script.replace(str(scratch), ""):
        raise SystemExit(f"REFUSED: the step still names a {runner_tmp} path after relocation")
    step = root / "step.sh"
    step.write_text(script, encoding="utf-8")
    env = {
        "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}",
        "HOME": str(root),
        "LANG": "C",
        "TMPDIR": str(tmpdir),
        "TEMP": str(tmpdir),
        "TMP": str(tmpdir),
        "GIT_CEILING_DIRECTORIES": str(root),
        "GH_TOKEN": TOKEN,
        "GITHUB_REPOSITORY": REPO_NAME,
        "BRANCH": BRANCH,
        "GH_LOG": str(root / "gh.log"),
        "GH_STDOUT": body,
        "GH_ERR": err,
        "GH_RC": str(rc),
    }
    proc = subprocess.run([*SHELLS[shell], str(step)], cwd=repo, env=env, capture_output=True, check=False, timeout=60)  # nosec B603
    payload = scratch / "lockfile-commit.json"
    return {
        "exit": proc.returncode,
        "stdout": proc.stdout.decode("utf-8", "replace"),
        "stderr": proc.stderr.decode("utf-8", "replace"),
        "payload": payload.read_text(encoding="utf-8") if payload.is_file() else None,
        "gh_argv": (root / "gh.log").read_text(encoding="utf-8").replace(str(scratch), "<scratch>") if (root / "gh.log").is_file() else None,
        "token_printed": TOKEN in (proc.stdout + proc.stderr).decode("utf-8", "replace"),
        "scratch_files": sorted(p.name for p in scratch.iterdir()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--runner-tmp", required=True, help="the temp prefix the step hardcodes, e.g. the runner's temp dir with a trailing slash")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    # Absolute: the step runs with cwd = its repository, so every path handed to it must be absolute.
    args.out = args.out.resolve()
    runs = {"main": _step_run(args.main), "frozen": _step_run(args.frozen)}
    report: dict = {}
    lines = [f"== {args.label}: main {args.main} vs frozen {args.frozen}"]
    ok = True
    for scenario, (_c, _b, _e, _rc, same) in SCENARIOS.items():
        for shell in SHELLS:
            result = {variant: _one(text, args.runner_tmp, scenario, shell, args.out / args.label / scenario / shell / variant) for variant, text in runs.items()}
            report.setdefault(scenario, {})[shell] = result
            m, f = result["main"], result["frozen"]
            identical = all(m[k] == f[k] for k in ("exit", "stdout", "stderr", "payload", "gh_argv"))
            if same:
                verdict = "IDENTICAL" if identical else "DIFFERENT"
                ok &= identical
            else:
                verdict = "identical" if identical else "differs (expected)"
            token = " TOKEN-PRINTED" if (m["token_printed"] or f["token_printed"]) else ""
            lines.append(f"  [{scenario} / {shell}] main exit {m['exit']} | frozen exit {f['exit']} | {verdict}{token}")
            if not same:
                lines.append(f"      main   stdout={m['stdout']!r} stderr={m['stderr']!r}")
                lines.append(f"      frozen stdout={f['stdout']!r} stderr={f['stderr']!r}")
            if f["token_printed"]:
                ok = False
            if scenario.endswith(("exit-1", "exit-4", "exit-0")) and scenario != "success" and f["exit"] != 1:
                ok = False
    out_json = args.out / f"{args.label}.json"
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    text = "\n".join(lines) + f"\n  RESULT {args.label}: {'OK' if ok else 'CHECK'}\n"
    (args.out / f"{args.label}.txt").write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
