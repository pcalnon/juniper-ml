"""
Run lockfile-update.yml's commit step, byte-identical, against a gh that exits as the real CLI does (owner ruling 17).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4, owner ruling 17 ("canopy: dead error path"); juniper-canopy#808; juniper-canopy
         .github/workflows/lockfile-update.yml step "Commit updated lockfile (GitHub-signed, via API)"

The defect: ``gh api graphql`` exits 1 on a response that carries GraphQL ``errors``
(cli/cli pkg/cmd/api/api.go, ``processResponse``: the body goes to stdout, ``gh: <message>``
to stderr, then ``cmdutil.SilentError``), so under the step's ``set -euo pipefail`` the step
ends at the ``gh`` line and its own ``createCommitOnBranch failed`` diagnostic never prints.

This harness takes the step's ``run:`` text from each workflow file (``--before`` = main,
``--after`` = the fix), writes it to a file unchanged and runs it the way the runner does:
``bash -e FILE`` (the step sets no ``shell:``; run 42642175942's log shows
``shell: /usr/bin/bash -e {0}``) and also ``bash --noprofile --norc -eo pipefail FILE``. The
step's two absolute temp paths are NOT rewritten: bubblewrap mounts a per-case directory
under ``--work`` over the directory they name, so the step writes there and this host's
system temp directory is never written. The paths are read from the step, not hardcoded.

``gh`` on PATH is one of:

* a stub modelled on api.go (stdout body first, then stderr, then the exit status);
* ``realgh_graphql_error``: a wrapper that runs the REAL gh, with its stored login, on a
  read-only query GitHub rejects (an undefined field). It ignores the step's argv (logged),
  so the step's mutation is never sent;
* ``realgh_http401``: a wrapper that runs the real gh with the harness's fake token, which
  GitHub answers 401 (no GraphQL ``errors``). Read-only query; the token is not a credential.

Every case runs in a throwaway git repository whose commit dates are fixed, so the request
body the step writes is byte-comparable between ``--before`` and ``--after``.

Usage::

    python3 util/ad-hoc/2026-11-09_flood4r2_r17-canopy-lockfile_harness.py \
        --before <main copy of lockfile-update.yml> --after <fixed lockfile-update.yml> \
        --work <dir under a repository's tmp/> [--no-real-gh]

Writes ``<work>/harness_results.json`` and ``<work>/{before,after}/step.sh``. Prints a table.
Environment values and real tokens are never printed. Exit 0 when every expectation holds.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess  # nosec B404 - runs bash, git, bwrap and gh against scratch directories
import sys
from pathlib import Path

import yaml

STEP_NAME = "Commit updated lockfile (GitHub-signed, via API)"
JOB_ID = "update-lockfile"
FAKE_TOKEN = "lockfile-harness-token-not-real"
BRANCH = "dependabot/pip/example"
REPO_NAME = "pcalnon/juniper-canopy"
FIXED_DATE = "2026-11-09T00:00:00+0000"
SIGNED_URL = "https://example.test/commit/abc123"
STALE_MESSAGE = 'Expected branch to point to "0123456789abcdef0123456789abcdef01234567" but it did not. Pull and try again.'

SHELLS = {
    "bash -e": ["bash", "-e"],
    "bash --noprofile --norc -eo pipefail": ["bash", "--noprofile", "--norc", "-eo", "pipefail"],
}

SIGNED_BODY = json.dumps({"data": {"createCommitOnBranch": {"commit": {"oid": "abc123", "url": SIGNED_URL}}}})
STALE_BODY = json.dumps(
    {
        "data": {"createCommitOnBranch": None},
        "errors": [
            {
                "type": "STALE_DATA",
                "path": ["createCommitOnBranch"],
                "locations": [{"line": 1, "column": 58}],
                "message": STALE_MESSAGE,
            }
        ],
    }
)
TWO_ERRORS_BODY = json.dumps({"data": None, "errors": [{"message": "first problem"}, {"message": "second problem"}]})
# api.go parseErrorResponse joins the error messages; a single error with no message joins
# to an empty string, processResponse sees no serverError, and a 200 exits 0.
EMPTY_MESSAGE_BODY = json.dumps({"data": None, "errors": [{"type": "INTERNAL"}]})
HTTP401_BODY = json.dumps({"message": "Bad credentials", "documentation_url": "https://docs.github.com/rest", "status": "401"}, indent=2)
TOKEN_BODY = json.dumps({"data": None, "errors": [{"type": "FORBIDDEN", "message": f"token {FAKE_TOKEN} lacks access"}]})

# name -> (lockfile edit, gh kind, stdout, stderr, exit status, expected outcome after the fix)
# lockfile edit: "dirty" changes requirements.lock, "empty" truncates it, "none" leaves it.
SCENARIOS: dict[str, dict] = {
    "unchanged": {"edit": "none", "gh": "forbidden", "expect": "up_to_date"},
    "empty_payload": {"edit": "empty", "gh": "forbidden", "expect": "empty_payload"},
    "success": {"edit": "dirty", "gh": "stub", "stdout": SIGNED_BODY, "stderr": "", "rc": 0, "expect": "signed"},
    "graphql_error_stale": {"edit": "dirty", "gh": "stub", "stdout": STALE_BODY, "stderr": f"gh: {STALE_MESSAGE}\n", "rc": 1, "expect": "graphql_diag"},
    "graphql_error_two_messages": {"edit": "dirty", "gh": "stub", "stdout": TWO_ERRORS_BODY, "stderr": "gh: first problem\nsecond problem\n", "rc": 1, "expect": "graphql_diag"},
    "graphql_errors_gh_exit0": {"edit": "dirty", "gh": "stub", "stdout": EMPTY_MESSAGE_BODY, "stderr": "", "rc": 0, "expect": "graphql_diag"},
    "http_502_html": {"edit": "dirty", "gh": "stub", "stdout": "<html><body><h1>502 Bad Gateway</h1></body></html>\n", "stderr": "gh: HTTP 502\n", "rc": 1, "expect": "http_diag"},
    "http_401_json": {"edit": "dirty", "gh": "stub", "stdout": HTTP401_BODY, "stderr": "gh: Bad credentials (HTTP 401)\n", "rc": 1, "expect": "http_diag", "hint401": True},
    "network_error": {"edit": "dirty", "gh": "stub", "stdout": "", "stderr": "error connecting to api.github.com\ncheck your internet connection or https://githubstatus.com\n", "rc": 1, "expect": "http_diag"},
    "token_in_gh_output": {"edit": "dirty", "gh": "stub", "stdout": TOKEN_BODY, "stderr": f"gh: token {FAKE_TOKEN} lacks access\n", "rc": 1, "expect": "graphql_diag"},
    "realgh_graphql_error": {"edit": "dirty", "gh": "real_graphql_error", "expect": "graphql_diag"},
    "realgh_http401": {"edit": "dirty", "gh": "real_http401", "expect": "http_diag", "hint401": True},
}

GRAPHQL_DIAG = "createCommitOnBranch failed"
HTTP_DIAG = "gh api graphql failed"
SIGNED_LINE = f"Signed lockfile commit: {SIGNED_URL}"
HINT_401 = "CROSS_REPO_DISPATCH_TOKEN is invalid or expired"


def step_of(workflow: Path) -> dict:
    with workflow.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    job = doc["jobs"][JOB_ID]
    found = [step for step in job["steps"] if step.get("name") == STEP_NAME]
    if len(found) != 1:
        raise SystemExit(f"{workflow}: expected one step named {STEP_NAME!r}, found {len(found)}")
    shell_overrides = {
        "workflow defaults": (doc.get("defaults") or {}).get("run", {}).get("shell"),
        "job defaults": (job.get("defaults") or {}).get("run", {}).get("shell"),
        "step": found[0].get("shell"),
    }
    if any(shell_overrides.values()):
        raise SystemExit(f"{workflow}: a shell is set ({shell_overrides}); this harness models the unspecified default")
    return found[0]


def temp_paths(script: str) -> tuple[str, str, list[str]]:
    """The step's request-body and result paths, and every absolute path under their directory."""
    found = re.findall(r"(/\S*?lockfile-commit(?:-result)?\.json)", script)
    body = sorted({p for p in found if p.endswith("/lockfile-commit.json")})
    result = sorted({p for p in found if p.endswith("/lockfile-commit-result.json")})
    if len(body) != 1 or len(result) != 1:
        raise SystemExit(f"expected one body and one result path, found {found}")
    directory = os.path.dirname(body[0])
    if os.path.dirname(result[0]) != directory or not directory.startswith("/"):
        raise SystemExit(f"body and result are not in one absolute directory: {body[0]} {result[0]}")
    under = sorted(set(re.findall(re.escape(directory) + r"/[^\s;)\"']+", script)))
    return body[0], result[0], under


def git(repo: Path, *args: str) -> str:
    env = dict(
        os.environ,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CEILING_DIRECTORIES=str(repo.parent),
        GIT_AUTHOR_NAME="harness",
        GIT_AUTHOR_EMAIL="harness@example.invalid",
        GIT_COMMITTER_NAME="harness",
        GIT_COMMITTER_EMAIL="harness@example.invalid",
        GIT_AUTHOR_DATE=FIXED_DATE,
        GIT_COMMITTER_DATE=FIXED_DATE,
    )
    proc = subprocess.run(["git", "-C", str(repo), *args], env=env, check=True, capture_output=True, text=True)  # nosec B603 B607 - scratch repo only
    return proc.stdout


def make_repo(case_dir: Path, edit: str) -> tuple[Path, str]:
    repo = case_dir / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "config", "core.autocrlf", "false")
    (repo / "requirements.lock").write_text("# lock\npackage==1.0.0\n", encoding="utf-8")
    git(repo, "add", "requirements.lock")
    git(repo, "commit", "-q", "-m", "base")
    head = git(repo, "rev-parse", "HEAD").strip()
    if edit == "dirty":
        (repo / "requirements.lock").write_text("# lock\npackage==2.0.0\n", encoding="utf-8")
    elif edit == "empty":
        (repo / "requirements.lock").write_text("", encoding="utf-8")
    return repo, head


def write_gh(bin_dir: Path, scenario: dict, real_gh: str | None) -> None:
    bin_dir.mkdir(parents=True)
    stub_dir = bin_dir.parent / "gh-stub"
    stub_dir.mkdir()
    log = '#!/bin/bash\nprintf \'argv:\' >> "$GH_ARGV_LOG"\nprintf \' %s\' "$@" >> "$GH_ARGV_LOG"\nprintf \'\\n\' >> "$GH_ARGV_LOG"\n'
    kind = scenario["gh"]
    if kind == "forbidden":
        body = log + "echo 'harness: gh must not be called here' >&2\nexit 99\n"
    elif kind == "stub":
        (stub_dir / "stdout").write_text(scenario["stdout"], encoding="utf-8")
        (stub_dir / "stderr").write_text(scenario["stderr"], encoding="utf-8")
        # api.go processResponse: the body is copied to stdout, then `gh: <message>` goes to
        # stderr, then the command returns (SilentError -> exit 1 when there was a message).
        body = log + f"cat '{stub_dir}/stdout'\ncat '{stub_dir}/stderr' >&2\nexit {int(scenario['rc'])}\n"
    elif kind == "real_graphql_error":
        if real_gh is None:
            raise SystemExit("real gh requested but not found")
        # Stored login (GH_TOKEN unset); a read-only query GitHub rejects. The step's argv is ignored.
        body = log + f"exec env -u GH_TOKEN '{real_gh}' api graphql -f query='query {{ viewer {{ loginx }} }}'\n"
    elif kind == "real_http401":
        if real_gh is None:
            raise SystemExit("real gh requested but not found")
        # GH_TOKEN is the harness's fake token from the step's env: GitHub answers 401.
        body = log + f"exec '{real_gh}' api graphql -f query='query {{ viewer {{ login }} }}'\n"
    else:
        raise SystemExit(f"unknown gh kind {kind}")
    path = bin_dir / "gh"
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def run_case(label: str, step_file: Path, ci_dir: str, body_name: str, result_name: str, name: str, scenario: dict, shell_label: str, work: Path, real_gh: str | None) -> dict:
    case_dir = work / label / name / shell_label.replace(" ", "_")
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    private_tmp = case_dir / "private-tmp"
    private_tmp.mkdir()
    repo, head = make_repo(case_dir, scenario["edit"])
    write_gh(case_dir / "bin", scenario, real_gh)
    argv_log = case_dir / "gh-argv.log"
    base_env = {k: v for k, v in os.environ.items() if k not in {"GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"}}
    env = dict(
        base_env,
        PATH=f"{case_dir / 'bin'}{os.pathsep}{os.environ.get('PATH', '/usr/bin:/bin')}",
        LANG="C",
        GH_TOKEN=FAKE_TOKEN,
        GH_ARGV_LOG=str(argv_log),
        EVENT_NAME="pull_request",
        GITHUB_REPOSITORY=REPO_NAME,
        BRANCH=BRANCH,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CEILING_DIRECTORIES=str(case_dir),
    )
    command = ["bwrap", "--dev-bind", "/", "/", "--bind", str(private_tmp), ci_dir, "--chdir", str(repo), "--", *SHELLS[shell_label], str(step_file)]
    proc = subprocess.run(command, env=env, capture_output=True, text=True, check=False, timeout=120)  # nosec B603 B607 - bwrap runs bash on the extracted step
    combined = proc.stdout + proc.stderr
    body_file = private_tmp / body_name
    result_file = private_tmp / result_name
    return {
        "label": label,
        "scenario": name,
        "shell": shell_label,
        "exit": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "graphql_diag": GRAPHQL_DIAG in combined,
        "http_diag": HTTP_DIAG in combined,
        "signed_line": SIGNED_LINE in proc.stdout,
        "up_to_date_line": "Lockfile already up to date" in combined,
        "empty_payload_line": "base64 produced an empty payload" in combined,
        "token_printed": FAKE_TOKEN in combined,
        "hint_401": HINT_401 in combined,
        "gh_argv": argv_log.read_text(encoding="utf-8") if argv_log.is_file() else "",
        "request_body_sha_input": body_file.read_text(encoding="utf-8") if body_file.is_file() else None,
        "result_file": result_file.read_text(encoding="utf-8")[:4000] if result_file.is_file() else None,
        "fixture_head": head,
    }


def judge(case: dict, expect: str, hint401: bool) -> list[str]:
    """Expectation failures for the FIXED step. Empty list = as expected."""
    problems = []
    if case["hint_401"] != hint401:
        problems.append(f"401 hint printed={case['hint_401']}, expected {hint401}")
    if case["token_printed"]:
        problems.append("token printed")
    if expect == "up_to_date":
        if case["exit"] != 0 or not case["up_to_date_line"] or case["gh_argv"]:
            problems.append("expected exit 0, the up-to-date notice and no gh call")
    elif expect == "empty_payload":
        if case["exit"] != 1 or not case["empty_payload_line"] or case["gh_argv"]:
            problems.append("expected exit 1, the empty-payload error and no gh call")
    elif expect == "signed":
        if case["exit"] != 0 or not case["signed_line"] or case["graphql_diag"] or case["http_diag"]:
            problems.append("expected exit 0 and the signed-commit line only")
    elif expect == "graphql_diag":
        if case["exit"] != 1 or not case["graphql_diag"] or case["http_diag"] or case["signed_line"]:
            problems.append("expected exit 1 with the createCommitOnBranch diagnostic")
    elif expect == "http_diag":
        if case["exit"] != 1 or not case["http_diag"] or case["graphql_diag"] or case["signed_line"]:
            problems.append("expected exit 1 with the gh api graphql failed diagnostic")
    return problems


def bash_probe(name: str, text: str) -> dict:
    proc = subprocess.run(["bash", "-c", text], capture_output=True, text=True, check=False, timeout=30)  # nosec B603 B607 - fixed snippets
    return {"probe": name, "script": text, "exit": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def host_paths_state(paths: list[str]) -> dict:
    return {p: os.path.exists(p) for p in paths}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--no-real-gh", action="store_true")
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    if shutil.which("bwrap") is None:
        raise SystemExit("bwrap is required (it gives the step a private temp directory)")
    real_gh = None if args.no_real_gh else shutil.which("gh")
    gh_version = subprocess.run([real_gh, "--version"], capture_output=True, text=True, check=False).stdout.splitlines()[0] if real_gh else None  # nosec B603

    steps = {"before": step_of(args.before), "after": step_of(args.after)}
    paths = {}
    for label, step in steps.items():
        out_dir = work / label
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "step.sh").write_text(step["run"], encoding="utf-8")
        paths[label] = temp_paths(step["run"])
    if paths["before"][:2] != paths["after"][:2]:
        raise SystemExit(f"the fix moved the step's temp paths: {paths}")
    body_path, result_path, _ = paths["after"]
    ci_dir = os.path.dirname(body_path)
    if Path(ci_dir).resolve() == work or str(work).startswith(ci_dir + "/"):
        raise SystemExit("--work must not be under the directory the step writes to")
    watched = sorted(set(paths["before"][2]) | set(paths["after"][2]))
    host_before = host_paths_state(watched)

    cases = []
    for name, scenario in SCENARIOS.items():
        if scenario["gh"].startswith("real_") and real_gh is None:
            continue
        for shell_label in SHELLS:
            for label in ("before", "after"):
                cases.append(run_case(label, work / label / "step.sh", ci_dir, os.path.basename(body_path), os.path.basename(result_path), name, scenario, shell_label, work, real_gh))

    host_after = host_paths_state(watched)
    failures = []
    identity = []
    for case in cases:
        if case["label"] == "after":
            scenario = SCENARIOS[case["scenario"]]
            for problem in judge(case, scenario["expect"], scenario.get("hint401", False)):
                failures.append(f"after/{case['scenario']}/{case['shell']}: {problem}")
    for name in ("unchanged", "empty_payload", "success"):
        for shell_label in SHELLS:
            pair = {c["label"]: c for c in cases if c["scenario"] == name and c["shell"] == shell_label}
            same = all(pair["before"][key] == pair["after"][key] for key in ("exit", "stdout", "stderr", "request_body_sha_input", "gh_argv"))
            identity.append({"scenario": name, "shell": shell_label, "identical": same})
            if not same:
                failures.append(f"{name}/{shell_label}: before and after differ on a path the fix must not change")
    if any(host_after[p] and not host_before[p] for p in watched):
        failures.append("a host temp path appeared during the run")

    probes = [
        bash_probe("redact-exact-value", "GH_TOKEN='t*k'; x='a t*k b tok'; printf '[%s]\\n' \"${x//\"${GH_TOKEN}\"/***}\""),
        bash_probe("redact-empty-token", "GH_TOKEN=''; x='a b'; printf '[%s]\\n' \"${x//\"${GH_TOKEN}\"/***}\""),
        bash_probe("capture-status-and-stderr", "set -euo pipefail; S=0; E=$({ sh -c 'echo out; echo err >&2; exit 3' > /dev/null; } 2>&1) || S=$?; printf '[%s][%s]\\n' \"$S\" \"$E\""),
        bash_probe("bare-failure-ends-step", "set -euo pipefail; sh -c 'exit 1' > /dev/null; echo reached"),
    ]

    report = {
        "before": str(args.before),
        "after": str(args.after),
        "real_gh": gh_version,
        "step_temp_paths": {"body": body_path, "result": result_path, "all_under_dir_before": paths["before"][2], "all_under_dir_after": paths["after"][2]},
        "host_temp_paths_existed_before_run": host_before,
        "host_temp_paths_exist_after_run": host_after,
        "cases": cases,
        "success_path_identity": identity,
        "bash_probes": probes,
        "failures": failures,
    }
    out = work / "harness_results.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"real gh: {gh_version}")
    print(f"{'scenario':28} {'shell':38} {'before rc/gql/http/signed':28} {'after rc/gql/http/signed':28} token(after)")
    for name in SCENARIOS:
        for shell_label in SHELLS:
            pair = {c["label"]: c for c in cases if c["scenario"] == name and c["shell"] == shell_label}
            if not pair:
                continue
            cells = []
            for label in ("before", "after"):
                c = pair[label]
                cells.append(f"{c['exit']}/{int(c['graphql_diag'])}/{int(c['http_diag'])}/{int(c['signed_line'])}")
            print(f"{name:28} {shell_label:38} {cells[0]:28} {cells[1]:28} {int(pair['after']['token_printed'])}")
    for row in identity:
        print(f"identity {row['scenario']} / {row['shell']}: {row['identical']}")
    for probe in probes:
        print(f"probe {probe['probe']}: exit={probe['exit']} stdout={probe['stdout'].strip()!r}")
    print(f"host temp paths created: {[p for p in watched if host_after[p] and not host_before[p]]}")
    print(f"failures: {failures}")
    print(f"wrote {out}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
