"""
Run the WHOLE lockfile-update commit step, text unchanged, under bash 3.2.57 in a network-less container, and compare with the host bash.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: Cursor flood-4 disposition, Overtoad ruling 17 ("canopy: dead error path"), session-5 validation

canopy's required macOS unit-test leg runs the regression test, which executes the step with the runner's bash
(3.2.57 there). This prepares a work directory (the step text as the workflow has it, stub gh and git, a wrapper
that runs the host's jq through the host's loader, mounted read-only) and prints the `docker run` command line;
with --collect it reads the outputs back and compares them with the validator harness's bash 5 rows.
The step writes its two files in the CONTAINER's own temp directory; nothing is written on the host outside --work.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

STEP_NAME = "Commit updated lockfile (GitHub-signed, via API)"
TOKEN = "lockfile-val-harness-token-not-real"
GLOB_TOKEN = "a*b?[c]x"
SIGNED = json.dumps({"data": {"createCommitOnBranch": {"commit": {"oid": "abc123", "url": "https://example.test/commit/abc123"}}}})
STALE = 'Expected branch to point to "abc" but it did not. Pull and try again.'

GH_STUB = """\
#!/bin/sh
cat "$GH_STDOUT_FILE"
cat "$GH_STDERR_FILE" >&2
exit "$GH_RC"
"""

GIT_STUB = """\
#!/bin/sh
case "$1" in
  diff) exit 1 ;;
  rev-parse) echo 0123456789abcdef0123456789abcdef01234567 ;;
  *) echo "git stub: unexpected $*" >&2; exit 99 ;;
esac
"""

JQ_WRAPPER = """\
#!/bin/sh
exec /lib64/ld-linux-x86-64.so.2 --library-path /usr/lib/x86_64-linux-gnu /hostbin/jq "$@"
"""

# Scenario ids shared with the bash 5 harness are compared row for row; the glob-token rows are 3.2-only checks.
SCENARIOS: list[dict[str, object]] = [
    {"id": "success", "stdout": SIGNED, "stderr": "", "rc": 0},
    {"id": "graphql_stale_exit1", "stdout": json.dumps({"data": {"createCommitOnBranch": None}, "errors": [{"type": "STALE_DATA", "path": ["createCommitOnBranch"], "message": STALE}]}), "stderr": f"gh: {STALE}\n", "rc": 1},
    {"id": "graphql_token_in_message_exit1", "stdout": json.dumps({"errors": [{"type": "FORBIDDEN", "message": f"token {TOKEN} lacks access"}]}), "stderr": f"gh: token {TOKEN} lacks access\n", "rc": 1},
    {"id": "http_502_html", "stdout": "<html>502 Bad Gateway</html>\n", "stderr": "gh: HTTP 502\n", "rc": 1},
    {"id": "http_401_json", "stdout": json.dumps({"message": "Bad credentials", "documentation_url": "https://docs.github.com/rest", "status": "401"}, indent=2), "stderr": "gh: Bad credentials (HTTP 401)\n", "rc": 1},
    {"id": "http_error_body_carries_token", "stdout": json.dumps({"message": f"bad token {TOKEN}", "status": "403"}), "stderr": f"gh: bad token {TOKEN} (HTTP 403)\n", "rc": 1},
    {"id": "empty_json_response", "stdout": "", "stderr": "unexpected end of JSON input\n", "rc": 1},
    {"id": "glob_token_literal", "token": GLOB_TOKEN, "stdout": json.dumps({"errors": [{"message": f"bad {GLOB_TOKEN} here; aXXbYcx stays"}]}), "stderr": f"gh: bad {GLOB_TOKEN} here; aXXbYcx stays\n", "rc": 1},
    {"id": "empty_token", "token": "", "stdout": json.dumps({"errors": [{"message": "plain"}]}), "stderr": "gh: plain\n", "rc": 1},
]


def _step_text(workflow: Path) -> str:
    doc = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    found = [step for step in doc["jobs"]["update-lockfile"]["steps"] if step.get("name") == STEP_NAME]
    if len(found) != 1:
        raise SystemExit("step not found exactly once")
    return str(found[0]["run"])


def _prepare(work: Path, workflow: Path, image: str, uid_gid: str) -> int:
    if work.exists():
        raise SystemExit(f"{work} exists; give a fresh directory")
    (work / "bin").mkdir(parents=True)
    (work / "repo").mkdir()
    (work / "in").mkdir()
    (work / "out").mkdir()
    (work / "repo" / "requirements.lock").write_bytes(b"changed\n")
    (work / "step.sh").write_text(_step_text(workflow), encoding="utf-8")
    for name, body in (("gh", GH_STUB), ("git", GIT_STUB), ("jq", JQ_WRAPPER)):
        target = work / "bin" / name
        target.write_text(body, encoding="utf-8")
        target.chmod(0o755)
    lines = ["#!/usr/local/bin/bash", "bash --version | head -n 1 > /work/out/bash_version.txt", "/work/bin/jq --version > /work/out/jq_version.txt 2>&1", "cd /work/repo"]
    for scenario in SCENARIOS:
        sid = str(scenario["id"])
        (work / "in" / f"{sid}.stdout").write_text(str(scenario["stdout"]), encoding="utf-8")
        (work / "in" / f"{sid}.stderr").write_text(str(scenario["stderr"]), encoding="utf-8")
        (work / "in" / f"{sid}.token").write_text(str(scenario.get("token", TOKEN)), encoding="utf-8")
        for shell_id, shell in (("bash-e", "bash -e"), ("bash-eo-pipefail", "bash --noprofile --norc -eo pipefail")):
            prefix = f"/work/out/{sid}.{shell_id}"
            lines.append(
                f'env -i PATH=/work/bin:/usr/local/bin:/usr/bin:/bin HOME=/work LANG=C GH_TOKEN="$(cat /work/in/{sid}.token)" GH_STDOUT_FILE=/work/in/{sid}.stdout GH_STDERR_FILE=/work/in/{sid}.stderr GH_RC={scenario["rc"]} '
                f"EVENT_NAME=pull_request GITHUB_REPOSITORY=pcalnon/juniper-canopy BRANCH=dependabot/pip/example {shell} /work/step.sh > {prefix}.stdout 2> {prefix}.stderr; echo $? > {prefix}.rc"
            )
    (work / "run.sh").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("docker run --rm --network none --user " + uid_gid + f" -v {work}:/work -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro -v /lib64/ld-linux-x86-64.so.2:/lib64/ld-linux-x86-64.so.2:ro -v /usr/bin/jq:/hostbin/jq:ro {image} bash /work/run.sh")
    return 0


def _collect(work: Path, harness: Path) -> int:
    with open(harness, encoding="utf-8") as fh:
        rows = {(row["scenario"], row["shell"]): row["fix"] for row in json.load(fh)["rows"]}
    out = work / "out"
    report: dict[str, object] = {"bash": (out / "bash_version.txt").read_text(encoding="utf-8").strip(), "jq": (out / "jq_version.txt").read_text(encoding="utf-8").strip(), "rows": []}
    rows_out: list[dict[str, object]] = []
    problems = 0
    for scenario in SCENARIOS:
        sid = str(scenario["id"])
        token = str(scenario.get("token", TOKEN))
        for shell_id in ("bash-e", "bash-eo-pipefail"):
            prefix = out / f"{sid}.{shell_id}"
            got = {"rc": int(Path(f"{prefix}.rc").read_text(encoding="utf-8").strip()), "stdout": Path(f"{prefix}.stdout").read_text(encoding="utf-8"), "stderr": Path(f"{prefix}.stderr").read_text(encoding="utf-8")}
            bash5 = rows.get((sid, shell_id))
            same = None if bash5 is None else all(got[key] == bash5[key] for key in ("rc", "stdout", "stderr"))
            token_printed = bool(token) and token in got["stdout"] + got["stderr"]
            row = {"scenario": sid, "shell": shell_id, **got, "same_as_bash5_harness": same, "token_printed": token_printed}
            rows_out.append(row)
            if same is False or token_printed:
                problems += 1
            print(f"{sid:34} {shell_id:17} rc={got['rc']} same_as_bash5={same} token_printed={token_printed}")
            if bash5 is None:
                print(f"    stdout={got['stdout']!r}")
                print(f"    stderr={got['stderr']!r}")
    report["rows"] = rows_out
    with open(work / "bash32_step.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(f"bash: {report['bash']}; jq: {report['jq']}; problems: {problems}")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--workflow", type=Path)
    parser.add_argument("--image", default="bash:3.2.57")
    parser.add_argument("--uid-gid", default="1000:1000")
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--harness", type=Path)
    args = parser.parse_args()
    if args.collect:
        if args.harness is None:
            raise SystemExit("--collect needs --harness")
        return _collect(args.work, args.harness)
    if args.workflow is None:
        raise SystemExit("--workflow is required to prepare")
    return _prepare(args.work, args.workflow, args.image, args.uid_gid)


if __name__ == "__main__":
    sys.exit(main())
