"""
Print one job of a tree's workflow file: its runs-on, env, and each step's name, uses, with, shell, env and run (read-only).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent L1b, flood-4 session 8)
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --tree <tree> --workflow ci.yml --job host-tooling-macos [--run-lines 400]
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--run-lines", type=int, default=400)
    args = parser.parse_args(argv)

    path = Path(args.tree) / ".github" / "workflows" / args.workflow
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    # PyYAML reads the bare key `on:` as the boolean True.
    print("triggers:", json.dumps(workflow.get("on", workflow.get(True)), default=str))
    if args.job == "?":
        print("jobs:", " ".join(workflow["jobs"]))
        return 0
    job = workflow["jobs"][args.job]
    print("workflow env:", json.dumps(workflow.get("env", {})))
    print("job:", args.job, "| runs-on:", job.get("runs-on"), "| needs:", job.get("needs"), "| if:", job.get("if"))
    print("job env:", json.dumps(job.get("env", {})))
    print("job defaults:", json.dumps(job.get("defaults", {})))
    print("job strategy:", json.dumps(job.get("strategy", {})), "| continue-on-error:", job.get("continue-on-error"))
    for index, step in enumerate(job.get("steps", []), 1):
        print("---- step %d: %s" % (index, step.get("name")))
        for key in ("id", "if", "uses", "with", "shell", "env"):
            if key in step:
                print("  %s: %s" % (key, json.dumps(step[key])))
        if "run" in step:
            lines = step["run"].splitlines()
            for line in lines[: args.run_lines]:
                print("  | " + line)
            if len(lines) > args.run_lines:
                print("  | ... (%d more lines)" % (len(lines) - args.run_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
