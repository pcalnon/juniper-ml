"""
Run lockfile-update.yml's own commit step against REAL gh answering a GraphQL error, read-only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 validation of the canopy-docs carrier (canopy#798, #799); claims-and-docs lens

The canopy-docs carrier says a GraphQL error never reaches the step's own
``createCommitOnBranch failed`` branch, because ``gh api graphql`` exits 1 on an
``errors`` body and ``set -euo pipefail`` ends the step at the ``gh`` line. This
re-derives that end to end. The step's ``run:`` text is taken from the workflow
file (PyYAML), its two ``/tmp`` paths relocated under the scratch directory (this
host never writes under /tmp), and it runs in a throwaway git repo whose
``requirements.lock`` is dirty, with the real ``base64`` and ``jq``.

``gh`` on PATH is a wrapper. It NEVER sends the step's mutation: it ignores its
argv (logging it) and runs the real gh on a READ-ONLY query that GitHub answers
with GraphQL ``errors``:

* ``validation``: an undefined field (``viewer { thisFieldDoesNotExist }``), no ``data``;
* ``execution``: a repository that does not exist, ``data`` present with ``errors``,
  the shape a stale ``expectedHeadOid`` has;
* ``stub-exit-0`` (control, no network): prints an ``errors`` body and exits 0, as
  the canopy regression test's stub does, to show the branch is reachable that way.

Also checks the bash ``set -e`` facts the docs state (assignment vs argument
substitution, and a failing substitution that printed bytes first).

Usage::

    python3 util/ad-hoc/2026-11-08_flood4r2_val_canopy-docs_step_e2e.py \
        --workflow <canopy checkout>/.github/workflows/lockfile-update.yml --scratch <dir>

Nothing in the canopy checkout is written. Environment values and tokens are never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404 - runs bash, git and gh in a scratch dir
import sys
from pathlib import Path

import yaml

STEP_NAME = "Commit updated lockfile (GitHub-signed, via API)"
CI_BODY = "/tmp/lockfile-commit.json"  # nosec B108 - the workflow's own text, relocated before running
CI_RESULT = "/tmp/lockfile-commit-result.json"  # nosec B108 - the workflow's own text, relocated before running

WRAPPERS = {
    "validation": "query { viewer { thisFieldDoesNotExist } }",
    "execution": 'query { repository(Overtoad: "cli", name: "no-such-repo-flood4r2-val-probe") { id } }',
}


def step_script(workflow: Path) -> str:
    with workflow.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    steps = doc["jobs"]["update-lockfile"]["steps"]
    found = [step for step in steps if step.get("name") == STEP_NAME]
    if len(found) != 1:
        raise SystemExit(f"expected one step named {STEP_NAME!r}, found {len(found)}")
    return found[0]["run"]


def git(repo: Path, *args: str) -> str:
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_CEILING_DIRECTORIES=str(repo.parent))
    proc = subprocess.run(["git", "-C", str(repo), *args], env=env, check=True, capture_output=True, text=True)  # nosec B603 B607 - scratch repo only
    return proc.stdout


def make_repo(case_dir: Path) -> Path:
    repo = case_dir / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "val@example.invalid")
    git(repo, "config", "user.name", "val")
    git(repo, "config", "commit.gpgsign", "false")
    (repo / "requirements.lock").write_text("# lock\npackage==1.0.0\n", encoding="utf-8")
    git(repo, "add", "requirements.lock")
    git(repo, "commit", "-q", "-m", "base")
    (repo / "requirements.lock").write_text("# lock\npackage==2.0.0\n", encoding="utf-8")
    return repo


def write_wrapper(bin_dir: Path, kind: str, real_gh: str) -> None:
    bin_dir.mkdir(parents=True)
    path = bin_dir / "gh"
    if kind == "stub-exit-0":
        body = '#!/bin/bash\nprintf \'%s\\n\' "argv: $*" >> "$WRAP_LOG"\nprintf \'%s\' \'{"errors":[{"message":"stub gh exited 0"}]}\'\nexit 0\n'
    else:
        query = WRAPPERS[kind].replace("'", "'\\''")
        body = f"#!/bin/bash\nprintf '%s\\n' \"argv: $*\" >> \"$WRAP_LOG\"\nexec '{real_gh}' api graphql -f query='{query}'\n"
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def run_case(scratch: Path, script: str, kind: str, real_gh: str) -> dict:
    case_dir = scratch / f"case-{kind}"
    if case_dir.exists():
        shutil.rmtree(case_dir)
    repo = make_repo(case_dir)
    write_wrapper(case_dir / "bin", kind, real_gh)
    body, result = case_dir / "lockfile-commit.json", case_dir / "lockfile-commit-result.json"
    executed = script.replace(CI_BODY, str(body)).replace(CI_RESULT, str(result))
    # The scratch dir is under a repo's own tmp/, so strip it before looking for a system /tmp path.
    if CI_BODY in executed or CI_RESULT in executed or "/tmp/" in executed.replace(str(case_dir), "<case>"):
        raise SystemExit("a /tmp path survived relocation; refusing to run")
    env = dict(os.environ)
    env.update(
        PATH=f"{case_dir / 'bin'}{os.pathsep}{os.environ.get('PATH', '/usr/bin:/bin')}",
        WRAP_LOG=str(case_dir / "wrapper.log"),
        EVENT_NAME="pull_request",
        GITHUB_REPOSITORY="pcalnon/juniper-canopy",
        BRANCH="dependabot/pip/example",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CEILING_DIRECTORIES=str(case_dir),
    )
    proc = subprocess.run(["bash", "-c", executed], cwd=repo, env=env, capture_output=True, text=True, check=False, timeout=60)  # nosec B603 B607
    out = proc.stdout + proc.stderr
    return {
        "case": kind,
        "exit": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "own_errors_branch_printed": "createCommitOnBranch failed" in out,
        "signed_line_printed": "Signed lockfile commit" in out,
        "gh_line": [line for line in proc.stderr.splitlines() if line.startswith("gh: ")],
        "request_body_written": body.is_file(),
        "result_file": result.read_text(encoding="utf-8") if result.is_file() else None,
        "wrapper_argv": (case_dir / "wrapper.log").read_text(encoding="utf-8") if (case_dir / "wrapper.log").is_file() else "",
    }


def bash_case(name: str, text: str) -> dict:
    proc = subprocess.run(["bash", "-c", text], capture_output=True, text=True, check=False, timeout=30)  # nosec B603 B607 - fixed snippets
    return {"case": name, "script": text, "exit": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    if str(scratch).startswith(("/tmp", "/var/tmp")):
        raise SystemExit("refusing a scratch dir under /tmp")
    scratch.mkdir(parents=True, exist_ok=True)
    real_gh = shutil.which("gh")
    if real_gh is None:
        raise SystemExit("no gh on PATH")
    gh_version = subprocess.run([real_gh, "--version"], capture_output=True, text=True, check=False).stdout.splitlines()[0]  # nosec B603
    script = step_script(args.workflow)
    report = {
        "workflow": str(args.workflow),
        "gh": gh_version,
        "home_relative_scratch": str(scratch.relative_to(Path.home())) if scratch.is_relative_to(Path.home()) else str(scratch),
        "step_cases": [run_case(scratch, script, kind, real_gh) for kind in ("validation", "execution", "stub-exit-0")],
        "bash_cases": [
            bash_case("assignment-substitution-fails", "set -euo pipefail; X=$(false); echo reached"),
            bash_case("assignment-substitution-printed-bytes-then-failed", "set -euo pipefail; X=$(printf bytes; exit 1); echo \"reached X=$X\""),
            bash_case("argument-substitution-fails", "set -euo pipefail; printf '[%s]\\n' \"$(false)\"; echo reached"),
        ],
    }
    out = scratch / "step_e2e.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for case in report["step_cases"]:
        print(f"{case['case']}: exit={case['exit']} own_errors_branch={case['own_errors_branch_printed']} signed={case['signed_line_printed']} gh_line={case['gh_line']}")
    for case in report["bash_cases"]:
        print(f"bash {case['case']}: exit={case['exit']} stdout={case['stdout']!r}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
