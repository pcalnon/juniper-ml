#!/usr/bin/env python3
"""
Compare a ported secret-scan job with juniper-data's, and lint the port: actionlint on the workflow, shellcheck on each run block.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-deploy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         adapted from 2026-11-11_flood4r2_r10-data-client_workflow_checks.py

ADAPTED FOR juniper-deploy
The port's job is `gitleaks` (named `Gitleaks`), juniper-data's is `security`, so the two job ids are separate
arguments (--job for the port and main, --data-job for juniper-data). It also compares each ported block's RAW lines
as they stand in the two files (indentation included), not only the parsed strings.

WHY THIS EXISTS
A port is not a copy, but the two shell blocks juniper-data#530 validated (the install and the pull-request scan)
should arrive unchanged, and everything around them (the job's keys, the workflow's events, the step order, the
checkout) is where a port differs. This prints both sides of each, says whether the two run blocks are byte-identical
to juniper-data's, writes every run block of the port's job to a file, and runs the linters:

    actionlint <workflow>             on the port's workflow and on main's copy, so a finding main already has is told apart
    shellcheck -s bash <run block>    on each run block of the job, as the default `bash -e {0}` shell runs it

It reads the three workflow files it is given and writes only under --out.

Usage (the interpreter needs PyYAML):
    python3 <this> --port <ci.yml> --main <main's ci.yml> --data <juniper-data's ci.yml> --job gitleaks --data-job security --out <dir> [--actionlint <bin>] [--shellcheck <bin>]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv: actionlint and shellcheck on files this script wrote or was given
import sys
from pathlib import Path

import yaml

PORTED = ("Install Gitleaks (pull request)", "Run Gitleaks over the pull request (Secrets Detection)")


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    # PyYAML (YAML 1.1) reads the bare `on:` key as boolean True.
    if True in data and "on" not in data:
        data["on"] = data.pop(True)
    return data


def describe(workflow: dict, job_id: str) -> dict:
    job = workflow["jobs"][job_id]
    steps = job["steps"]
    return {
        "on": sorted(workflow["on"]),
        "job": {k: job.get(k) for k in ("name", "needs", "if", "permissions", "continue-on-error", "runs-on")},
        "steps": [{"name": s.get("name"), "uses": s.get("uses"), "if": s.get("if"), "env": sorted((s.get("env") or {})), "with": s.get("with"), "continue-on-error": s.get("continue-on-error"), "shell": s.get("shell")} for s in steps],
        "gates": {name: sorted(other.get("needs") or []) if isinstance(other.get("needs"), list) else other.get("needs") for name, other in workflow["jobs"].items() if job_id in (other.get("needs") or [])},
    }


def run_of(workflow: dict, job_id: str, name: str) -> str | None:
    return next((str(s["run"]) for s in workflow["jobs"][job_id]["steps"] if s.get("name") == name and "run" in s), None)


def raw_block(path: Path, name: str) -> list[str] | None:
    """The lines of step ``name``'s ``run: |`` block exactly as the file holds them, up to the first less-indented line."""
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == f"- name: {name}"]
    if len(starts) != 1:
        return None
    i = starts[0] + 1
    while i < len(lines) and lines[i].strip() != "run: |":
        i += 1
    if i == len(lines):
        return None
    indent = len(lines[i]) - len(lines[i].lstrip())
    block = []
    for line in lines[i + 1 :]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        block.append(line)
    while block and not block[-1].strip():
        block.pop()
    return block


def lint(argv: list[str]) -> dict:
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=300, check=False)  # nosec B603
    return {"argv": argv, "exit": proc.returncode, "output": (proc.stdout + proc.stderr).strip()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--port", type=Path, required=True)
    ap.add_argument("--main", type=Path, required=True)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--job", default="gitleaks")
    ap.add_argument("--data-job", default="security")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--actionlint")
    ap.add_argument("--shellcheck")
    args = ap.parse_args()
    out = args.out.resolve()
    blocks = out / "run-blocks"
    blocks.mkdir(parents=True, exist_ok=True)
    port, main_wf, data = load(args.port), load(args.main), load(args.data)
    report: dict = {"port": describe(port, args.job), "main": describe(main_wf, args.job), "juniper_data": describe(data, args.data_job), "ported_run_blocks": {}, "shellcheck": [], "actionlint": {}}
    for name in PORTED:
        mine, theirs = run_of(port, args.job, name), run_of(data, args.data_job, name)
        raw_mine, raw_theirs = raw_block(args.port, name), raw_block(args.data, name)
        report["ported_run_blocks"][name] = {
            "present": mine is not None,
            "byte_identical_to_juniper_data": mine is not None and mine == theirs,
            "raw_lines_identical_to_juniper_data": raw_mine is not None and raw_mine == raw_theirs,
            "lines": len((mine or "").splitlines()),
        }
    for index, step in enumerate(port["jobs"][args.job]["steps"]):
        if "run" not in step:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", str(step.get("name", "step")).lower()).strip("-")
        path = blocks / f"{index:02d}_{slug}.sh"
        # The job names no shell, so GitHub runs each block as `bash -e {0}`.
        path.write_text("#!/usr/bin/env bash\nset -e\n" + str(step["run"]), encoding="utf-8")
        if args.shellcheck:
            row = lint([args.shellcheck, "-s", "bash", "-S", "style", str(path)])
            row["step"] = step.get("name")
            row["new_in_port"] = step.get("name") not in {s.get("name") for s in main_wf["jobs"][args.job]["steps"]}
            report["shellcheck"].append(row)
    if args.actionlint:
        report["actionlint"] = {"version": lint([args.actionlint, "-version"])["output"], "port": lint([args.actionlint, str(args.port)]), "main": lint([args.actionlint, str(args.main)])}
    if args.shellcheck:
        report["shellcheck_version"] = lint([args.shellcheck, "--version"])["output"]
    with open(out / "workflow_checks.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    for name, row in report["ported_run_blocks"].items():
        print(f"run block {name!r}: present={row['present']} byte-identical to juniper-data's={row['byte_identical_to_juniper_data']} raw lines identical={row['raw_lines_identical_to_juniper_data']} ({row['lines']} lines)")
    for side in ("main", "port", "juniper_data"):
        print(f"{side:<12} on={report[side]['on']} job={report[side]['job']} gates={report[side]['gates']}")
        print(f"{'':<12} steps={[s['name'] for s in report[side]['steps']]}")
    for row in report["shellcheck"]:
        print(f"shellcheck exit={row['exit']} new_in_port={row['new_in_port']} {row['step']!r}" + (("\n    " + row["output"].replace("\n", "\n    ")) if row["output"] else ""))
    if args.actionlint:
        for side in ("main", "port"):
            row = report["actionlint"][side]
            print(f"actionlint {side} exit={row['exit']}" + (("\n    " + row["output"].replace("\n", "\n    ")) if row["output"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
