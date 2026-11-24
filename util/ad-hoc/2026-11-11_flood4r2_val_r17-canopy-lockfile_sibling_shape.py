"""
Read every Juniper repo's workflows on its default branch (read-only contents API) and report each `gh api graphql` call's shape.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: Cursor flood-4 disposition, Overtoad ruling 17 ("canopy: dead error path"), session-5 validation

For each repo: the default branch and its head sha, every workflow file, each non-comment line that calls
`gh api graphql`, and for the step that holds it: the shell the runner gives it, whether the call is bare (not in
an `if`, `||` or `&&` list), and whether the text from the call to the end of the step equals juniper-canopy's
(main's, before the ruling-17 fix). Only GET requests are sent.
"""

from __future__ import annotations

import argparse
import difflib
import json
import subprocess
import sys
from pathlib import Path

import yaml

OWNER = "pcalnon"
REPOS = ["juniper-canopy", "juniper-data", "juniper-cascor", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-ml", "juniper-recurrence", "juniper-deploy", "juniper-harcot"]
NEEDLE = "gh api graphql"


def _get(path: str, raw: bool = False) -> tuple[int, str]:
    cmd = ["gh", "api", "--method", "GET", path]
    if raw:
        cmd += ["-H", "Accept: application/vnd.github.raw"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=120)
    return proc.returncode, proc.stdout


def _steps_with_call(text: str) -> list[dict[str, object]]:
    doc = yaml.safe_load(text)
    found: list[dict[str, object]] = []
    if not isinstance(doc, dict):
        return found
    workflow_shell = ((doc.get("defaults") or {}).get("run") or {}).get("shell")
    for job_id, job in (doc.get("jobs") or {}).items():
        job_shell = ((job.get("defaults") or {}).get("run") or {}).get("shell")
        for step in job.get("steps") or []:
            run = step.get("run")
            if not isinstance(run, str):
                continue
            lines = run.splitlines()
            calls = [index for index, line in enumerate(lines) if NEEDLE in line and not line.lstrip().startswith("#")]
            for index in calls:
                line = lines[index].strip()
                shell = step.get("shell") or job_shell or workflow_shell
                bare = line.startswith(NEEDLE) and "||" not in line and "&&" not in line and not line.startswith("if ")
                found.append(
                    {
                        "job": job_id,
                        "step": step.get("name"),
                        "shell_key": shell,
                        "runner_shell": "bash -e {0} (no shell key: the runner default)" if shell is None else str(shell),
                        "explicit_set_e": [candidate.strip() for candidate in lines[:index] if candidate.strip().startswith("set -")],
                        "call_line": line,
                        "bare": bare,
                        "tail": "\n".join(candidate.strip() for candidate in lines[index:] if candidate.strip()),
                    }
                )
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {}
    canopy_tail = ""
    for repo in REPOS:
        entry: dict[str, object] = {}
        rc, body = _get(f"repos/{OWNER}/{repo}")
        if rc != 0:
            entry["error"] = "repo read failed"
            report[repo] = entry
            continue
        default_branch = json.loads(body)["default_branch"]
        rc, body = _get(f"repos/{OWNER}/{repo}/branches/{default_branch}")
        head = json.loads(body)["commit"]["sha"] if rc == 0 else None
        entry["default_branch"] = default_branch
        entry["head_sha"] = head
        rc, body = _get(f"repos/{OWNER}/{repo}/contents/.github/workflows?ref={head}")
        files = [item["name"] for item in json.loads(body)] if rc == 0 else []
        entry["workflow_files"] = len(files)
        hits: list[dict[str, object]] = []
        for name in sorted(files):
            if not name.endswith((".yml", ".yaml")):
                continue
            rc, text = _get(f"repos/{OWNER}/{repo}/contents/.github/workflows/{name}?ref={head}", raw=True)
            if rc != 0:
                hits.append({"file": name, "error": "read failed"})
                continue
            if NEEDLE not in text:
                continue
            (args.out / f"{repo}__{name}").write_text(text, encoding="utf-8")
            line_numbers = [number for number, line in enumerate(text.splitlines(), start=1) if NEEDLE in line and not line.lstrip().startswith("#")]
            comment_only = [number for number, line in enumerate(text.splitlines(), start=1) if NEEDLE in line and line.lstrip().startswith("#")]
            steps = _steps_with_call(text)
            hits.append({"file": name, "call_lines": line_numbers, "comment_lines": comment_only, "steps": steps})
            if repo == "juniper-canopy" and name == "lockfile-update.yml" and steps:
                canopy_tail = str(steps[0]["tail"])
        entry["hits"] = hits
        report[repo] = entry

    for repo, entry in report.items():
        for hit in entry.get("hits", []) if isinstance(entry, dict) else []:
            for step in hit.get("steps", []):
                tail = str(step["tail"])
                step["tail_equals_canopy_main"] = tail == canopy_tail
                if tail != canopy_tail:
                    step["tail_diff_vs_canopy_main"] = list(difflib.unified_diff(canopy_tail.splitlines(), tail.splitlines(), "juniper-canopy", repo, lineterm="", n=0))
    with open(args.out / "sibling_shape.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")

    for repo, entry in report.items():
        if not isinstance(entry, dict) or "error" in entry:
            print(f"{repo}: {entry}")
            continue
        print(f"{repo}: {entry['default_branch']} @ {str(entry['head_sha'])[:8]}, {entry['workflow_files']} workflow files, {len(entry['hits'])} with a call")
        for hit in entry["hits"]:
            print(f"  {hit['file']}: call lines {hit.get('call_lines')} (comment-only mentions at {hit.get('comment_lines')})")
            for step in hit.get("steps", []):
                print(f"    step {step['step']!r}: runner shell = {step['runner_shell']}; explicit {step['explicit_set_e']}; bare={step['bare']}; tail == canopy main: {step['tail_equals_canopy_main']}")
                print(f"      call: {step['call_line']}")
                for line in step.get("tail_diff_vs_canopy_main", []):
                    print(f"      diff {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
