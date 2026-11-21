"""
Run canopy's lockfile-update commit step, main's text and the carrier's, against stub gh binaries under both runner shells.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: Cursor flood-4 disposition, Overtoad ruling 17 ("canopy: dead error path"), session-5 validation

The step's `run:` text is read from each workflow file with PyYAML and executed unchanged except that the two
absolute paths it writes are relocated into the scenario directory (the repo's own regression test does the same).
gh is ALWAYS a stub here: no request leaves the host. Stub shapes follow cli/cli v2.103.3 pkg/cmd/api/api.go
(processResponse :477-573, parseErrorResponse :655-726). Each scenario runs as `bash -e FILE` (what the runner
gives a step with no `shell:` key) and as `bash --noprofile --norc -eo pipefail FILE` (what `shell: bash` gives).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

STEP_NAME = "Commit updated lockfile (GitHub-signed, via API)"
TOKEN = "lockfile-val-harness-token-not-real"
BRANCH = "dependabot/pip/example"
REPO_NAME = "pcalnon/juniper-canopy"
SIGNED = json.dumps({"data": {"createCommitOnBranch": {"commit": {"oid": "abc123", "url": "https://example.test/commit/abc123"}}}})
STALE = 'Expected branch to point to "abc" but it did not. Pull and try again.'
TIMEOUT_MSG = "Something went wrong while executing your query. This may be the result of a timeout, or it could be a GitHub bug. Please include `AAAA:BBBB:CCCC` when reporting this issue."

GH_STUB = """\
#!/bin/bash
{
  printf '%s' gh
  for arg in "$@"; do printf '\\t%s' "$arg"; done
  printf '\\n'
} >> "$GH_LOG"
cat "$GH_STDOUT_FILE"
cat "$GH_STDERR_FILE" >&2
if [[ -n "${GH_SIGNAL:-}" ]]; then
  kill -s "${GH_SIGNAL}" $$
fi
exit "${GH_RC}"
"""

SHELLS: dict[str, list[str]] = {
    "bash-e": ["bash", "-e"],
    "bash-eo-pipefail": ["bash", "--noprofile", "--norc", "-eo", "pipefail"],
}


def _scenarios() -> list[dict[str, object]]:
    errors_stale = json.dumps({"data": {"createCommitOnBranch": None}, "errors": [{"type": "STALE_DATA", "path": ["createCommitOnBranch"], "message": STALE}]})
    return [
        {"id": "unchanged", "dirty": None},
        {"id": "empty_payload", "dirty": ""},
        {"id": "success", "stdout": SIGNED},
        {"id": "success_push_event", "stdout": SIGNED, "event": "push"},
        {"id": "success_stderr_notice", "stdout": SIGNED, "stderr": "gh: a notice on a successful call\n"},
        {"id": "success_stderr_no_newline", "stdout": SIGNED, "stderr": "notice without newline"},
        {"id": "success_stderr_two_newlines", "stdout": SIGNED, "stderr": "notice\n\n"},
        {"id": "graphql_stale_exit1", "stdout": errors_stale, "stderr": f"gh: {STALE}\n", "rc": 1},
        {"id": "graphql_two_messages_exit1", "stdout": json.dumps({"errors": [{"message": "first"}, {"message": "second"}]}), "stderr": "gh: first\nsecond\n", "rc": 1},
        {"id": "graphql_no_message_exit0", "stdout": json.dumps({"errors": [{"type": "X"}]}), "rc": 0},
        {"id": "graphql_errors_empty_array_exit0", "stdout": json.dumps({"data": json.loads(SIGNED)["data"], "errors": []}), "rc": 0},
        {"id": "graphql_token_in_message_exit1", "stdout": json.dumps({"errors": [{"type": "FORBIDDEN", "message": f"token {TOKEN} lacks access"}]}), "stderr": f"gh: token {TOKEN} lacks access\n", "rc": 1},
        {"id": "http_502_html", "stdout": "<html>502 Bad Gateway</html>\n", "stderr": "gh: HTTP 502\n", "rc": 1},
        {"id": "http_502_json_errors_timeout", "stdout": json.dumps({"data": None, "errors": [{"message": TIMEOUT_MSG}]}), "stderr": f"gh: {TIMEOUT_MSG}\n", "rc": 1},
        {"id": "http_401_json", "stdout": json.dumps({"message": "Bad credentials", "documentation_url": "https://docs.github.com/rest", "status": "401"}, indent=2), "stderr": "gh: Bad credentials (HTTP 401)\n", "rc": 1},
        {"id": "http_403_scopes", "stdout": json.dumps({"message": "Resource not accessible by personal access token", "status": "403"}), "stderr": 'gh: Resource not accessible by personal access token (HTTP 403)\ngh: This API operation needs the "repo" scope. To request it, run:  gh auth refresh -h github.com -s repo\n', "rc": 1},
        {"id": "http_422_message_and_errors", "stdout": json.dumps({"message": "Validation Failed", "errors": [{"resource": "Commit", "code": "custom"}], "status": "422"}), "stderr": "gh: Validation Failed (HTTP 422)\n", "rc": 1},
        {"id": "http_error_body_carries_token", "stdout": json.dumps({"message": f"bad token {TOKEN}", "status": "403"}), "stderr": f"gh: bad token {TOKEN} (HTTP 403)\n", "rc": 1},
        {"id": "empty_json_response", "stdout": "", "stderr": "unexpected end of JSON input\n", "rc": 1},
        {"id": "no_response_dns", "stdout": "", "stderr": 'Post "https://api.github.com/graphql": dial tcp: lookup api.github.com: no such host\n', "rc": 1},
        {"id": "gh_exit_4_auth", "stdout": "", "stderr": "To get started with GitHub CLI, please run:  gh auth login\n", "rc": 4},
        {"id": "gh_exit_127", "stdout": "", "stderr": "bash: gh: command not found\n", "rc": 127},
        {"id": "gh_killed_sigterm", "stdout": "", "stderr": "", "rc": 0, "signal": "TERM"},
        {"id": "exit0_empty_body", "stdout": "", "rc": 0},
        {"id": "exit0_nonjson_body", "stdout": "<html>ok</html>\n", "rc": 0},
        {"id": "exit0_null_commit", "stdout": json.dumps({"data": {"createCommitOnBranch": None}}), "rc": 0},
    ]


def _step_text(workflow: Path) -> str:
    doc = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    steps = doc["jobs"]["update-lockfile"]["steps"]
    found = [step for step in steps if step.get("name") == STEP_NAME]
    if len(found) != 1:
        raise SystemExit(f"{workflow}: step not found exactly once")
    if "shell" in found[0]:
        raise SystemExit(f"{workflow}: the step sets its own shell: {found[0]['shell']}")
    return str(found[0]["run"])


def _git(repo: Path, *args: str) -> str:
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(repo.parent), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CEILING_DIRECTORIES": str(repo.parent), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    return subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True).stdout


def _run_one(work: Path, script: str, scenario: dict[str, object], shell: list[str], merge_streams: bool) -> dict[str, object]:
    work.mkdir(parents=True)
    repo = work / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "requirements.lock").write_bytes(b"# lock\npackage==1.2.3\n")
    _git(repo, "add", "requirements.lock")
    _git(repo, "commit", "-q", "-m", "base")
    head = _git(repo, "rev-parse", "HEAD").strip()
    dirty = scenario.get("dirty", "changed\n")
    if dirty is not None:
        (repo / "requirements.lock").write_text(str(dirty), encoding="utf-8")

    tdir = work / "t"
    tdir.mkdir()
    found = sorted(set(re.findall(r"(/\S*lockfile-commit(?:-result)?\.json)", script)))
    relocated = script
    for path in sorted(found, key=len, reverse=True):
        relocated = relocated.replace(path, str(tdir / Path(path).name))
    step_file = work / "step.sh"
    step_file.write_text(relocated, encoding="utf-8")

    bin_dir = work / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(GH_STUB, encoding="utf-8")
    gh.chmod(0o755)
    out_file = work / "gh.stdout.in"
    err_file = work / "gh.stderr.in"
    out_file.write_text(str(scenario.get("stdout", "")), encoding="utf-8")
    err_file.write_text(str(scenario.get("stderr", "")), encoding="utf-8")
    env = {
        "PATH": f"{bin_dir}{os.pathsep}/usr/bin:/bin",
        "HOME": str(work),
        "LANG": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CEILING_DIRECTORIES": str(work),
        "GH_TOKEN": TOKEN,
        "GH_LOG": str(work / "gh.log"),
        "GH_STDOUT_FILE": str(out_file),
        "GH_STDERR_FILE": str(err_file),
        "GH_RC": str(scenario.get("rc", 0)),
        "GH_SIGNAL": str(scenario.get("signal", "")),
        "EVENT_NAME": str(scenario.get("event", "pull_request")),
        "GITHUB_REPOSITORY": REPO_NAME,
        "BRANCH": BRANCH,
    }
    stderr_target = subprocess.STDOUT if merge_streams else subprocess.PIPE
    proc = subprocess.run([*shell, str(step_file)], cwd=repo, env=env, stdout=subprocess.PIPE, stderr=stderr_target, check=False, timeout=60)
    stdout = proc.stdout.decode("utf-8", "replace")
    stderr = "" if merge_streams else proc.stderr.decode("utf-8", "replace")
    body = tdir / "lockfile-commit.json"
    result = tdir / "lockfile-commit-result.json"
    gh_log = work / "gh.log"
    # The scenario directory differs per variant, so normalise it out before any main-vs-fix comparison.
    norm_out = stdout.replace(str(work), "<WORK>")
    norm_err = stderr.replace(str(work), "<WORK>")
    return {
        "rc": proc.returncode,
        "stdout": norm_out,
        "stderr": norm_err,
        "head": head,
        "gh_called": gh_log.is_file(),
        "gh_args": gh_log.read_text(encoding="utf-8").replace(str(work), "<WORK>") if gh_log.is_file() else "",
        "request_body": body.read_text(encoding="utf-8").replace(head, "<HEAD>") if body.is_file() else None,
        "result_file": result.read_text(encoding="utf-8") if result.is_file() else None,
        "token_printed": TOKEN in stdout + stderr,
        "paths_relocated": found,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-wf", required=True, type=Path)
    parser.add_argument("--fix-wf", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.work.exists():
        raise SystemExit(f"{args.work} exists; give a fresh directory")

    texts = {"main": _step_text(args.main_wf), "fix": _step_text(args.fix_wf)}
    rows: list[dict[str, object]] = []
    for scenario in _scenarios():
        for shell_id, shell in SHELLS.items():
            runs: dict[str, dict[str, object]] = {}
            for variant, text in texts.items():
                runs[variant] = _run_one(args.work / str(scenario["id"]) / shell_id / variant, text, scenario, shell, merge_streams=False)
                runs[variant + "_merged"] = _run_one(args.work / str(scenario["id"]) / shell_id / (variant + "-merged"), text, scenario, shell, merge_streams=True)
            main_run, fix_run = runs["main"], runs["fix"]
            rows.append(
                {
                    "scenario": scenario["id"],
                    "shell": shell_id,
                    "gh_rc": scenario.get("rc", 0),
                    "gh_signal": scenario.get("signal", ""),
                    "main": {key: main_run[key] for key in ("rc", "stdout", "stderr", "gh_called", "token_printed")},
                    "fix": {key: fix_run[key] for key in ("rc", "stdout", "stderr", "gh_called", "token_printed")},
                    "fix_merged_log": runs["fix_merged"]["stdout"],
                    "main_merged_log": runs["main_merged"]["stdout"],
                    "identical_rc_stdout_stderr": all(main_run[key] == fix_run[key] for key in ("rc", "stdout", "stderr")),
                    "identical_merged_log": runs["main_merged"]["stdout"] == runs["fix_merged"]["stdout"],
                    "identical_request_body": main_run["request_body"] == fix_run["request_body"],
                    "identical_gh_args": main_run["gh_args"] == fix_run["gh_args"],
                    "main_prints_step_diagnostic": "createCommitOnBranch failed" in str(main_run["stdout"]) + str(main_run["stderr"]),
                    "fix_prints_graphql_diagnostic": "createCommitOnBranch failed" in str(fix_run["stdout"]),
                    "fix_prints_http_diagnostic": "gh api graphql failed" in str(fix_run["stdout"]),
                    "fix_says_signed": "Signed lockfile commit" in str(fix_run["stdout"]),
                }
            )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"token": "<a fake literal, never a credential>", "rows": rows}, fh, indent=2)
        fh.write("\n")

    print(f"{'scenario':34} {'shell':17} {'gh':>4} | main rc diag | fix rc gql http signed tok | same(out/err/rc) same(body)")
    for row in rows:
        main_run = row["main"]
        fix_run = row["fix"]
        print(
            f"{row['scenario']!s:34} {row['shell']!s:17} {row['gh_rc']!s:>4} | {main_run['rc']!s:>7} {int(bool(row['main_prints_step_diagnostic'])):>4} | "
            f"{fix_run['rc']!s:>6} {int(bool(row['fix_prints_graphql_diagnostic'])):>3} {int(bool(row['fix_prints_http_diagnostic'])):>4} {int(bool(row['fix_says_signed'])):>6} {int(bool(fix_run['token_printed'])):>3} | "
            f"{int(bool(row['identical_rc_stdout_stderr'])):>16} {int(bool(row['identical_request_body'])):>10}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
