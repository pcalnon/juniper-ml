#!/usr/bin/env python3
"""Print each PyPI publish workflow's shape: triggers, permissions, env, defaults, and every job's gate and steps.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (port juniper-cascor#763 / #767's one-artifact publish fix to the other publishing repos)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_publish_workflow_artifact_audit.py (the audit naming the 18 publishers),
         util/ad-hoc/2026-11-15_publish_port_clone.py (makes the clones this reads)

Why
---
The audit says WHAT each publisher lacks; a port also needs each workflow's shape (an existing dispatch and its inputs,
a job default directory, a release guard, extra jobs such as juniper-data's notify-consumers), so the brief for each
port names the differences from juniper-cascor's template instead of discovering them mid-edit. A workflow is a
publisher when a step uses pypa/gh-action-pypi-publish.

    python3 -I util/ad-hoc/2026-11-15_publish_port_survey.py REPO_DIR [REPO_DIR ...]

Exit status: 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

PUBLISH_ACTION = "pypa/gh-action-pypi-publish@"


def short(value: object, limit: int = 160) -> str:
    text = json.dumps(value, sort_keys=True) if not isinstance(value, str) else value
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def survey(path: Path) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["on"] = data.pop(True, data.get("on"))
    print(f"### {path.parent.parent.parent.name}/{path.name}  ({len(path.read_text(encoding='utf-8').splitlines())} lines)")
    print(f"  on: {short(data.get('on'), 400)}")
    for key in ("permissions", "env", "concurrency", "defaults"):
        if key in data:
            print(f"  {key}: {short(data[key], 300)}")
    for job_id, job in (data.get("jobs") or {}).items():
        print(f"  job {job_id!r} name={job.get('name')!r} needs={job.get('needs')!r} env={short(job.get('environment'))!r}")
        for key in ("if", "permissions", "defaults", "outputs", "env", "strategy", "continue-on-error", "timeout-minutes"):
            if key in job:
                print(f"      {key}: {short(job[key], 300)}")
        for step in job.get("steps") or []:
            label = step.get("name") or step.get("uses")
            extras = []
            if step.get("uses") and step.get("name"):
                extras.append(f"uses={step['uses'].split('@')[0]}")
            for key in ("id", "if", "working-directory", "shell"):
                if key in step:
                    extras.append(f"{key}={short(step[key], 120)}")
            if "with" in step:
                extras.append(f"with={short(step['with'], 200)}")
            if "run" in step:
                extras.append(f"run={short(step['run'], 140)}")
            print(f"      - {label}  [{'; '.join(extras)}]")


def main(argv: "list[str]") -> int:
    for repo in argv:
        workflows = Path(repo) / ".github" / "workflows"
        for path in sorted(workflows.glob("*.y*ml")):
            if PUBLISH_ACTION in path.read_text(encoding="utf-8"):
                survey(path)
                print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
