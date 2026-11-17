#!/usr/bin/env python3
"""Map what phase 3 of the Python 3.15 migration would touch: each repo's informational 3.15 legs and required checks.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-11-16
Status:      ad-hoc -- investigation (Python 3.15 migration arc, phase 3 scoping: what "make 3.15 required" means)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-11-15_py315_leg_survey.py (the legs' current results),
             prompts/thread-handoff_automated-prompts/
             HANDOFF_2026-11-15_python-3-15-phase-2-complete-dill-drift-nightly-markers-cleanup.md (phase 3 is next)

Why this exists
---------------
Phase 3 makes the 3.15 checks required. Per repo that is two different switches: (1) dropping the leg's
`experimental: true`, so a 3.15 failure fails its matrix job and, through any aggregate gate that `needs:` it,
blocks the merge; and (2) naming the leg's own context in the branch ruleset. Which switch does anything depends
on whether a gate needs the job, whether the ruleset already names per-version contexts for 3.12-3.14, and whether
the workflow is path-filtered (a required context from a workflow that did not run waits forever). This reads all
three from each repo's default branch, through `gh api` only (no checkout, so it reads the CURRENT `main`).

Read-only: GET requests. Writes nothing.

Usage
-----
    python3 util/ad-hoc/2026-11-16_py315_phase3_scope_survey.py [--repo <bare-name> ...] [--json]

Exit 0 when every read succeeded; 1 when any failed (each failure is printed, the rest still run).
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess  # nosec B404
import sys

import yaml

OWNER = "pcalnon"
REPOS = [
    "juniper-ml", "juniper-cascor", "juniper-canopy", "juniper-data", "juniper-recurrence", "juniper-deploy",
    "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-harcot",
]
VERSIONED = re.compile(r"\b3\.1[0-9]\b")


def gh(path: str) -> object:
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path}: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


def triggers(doc: dict) -> dict:
    # PyYAML (YAML 1.1) parses the bare key `on` as boolean True.
    on = doc.get("on", doc.get(True, {}))
    if isinstance(on, str):
        on = {on: None}
    elif isinstance(on, list):
        on = {k: None for k in on}
    out = {}
    for event in ("pull_request", "push", "schedule", "workflow_dispatch", "merge_group"):
        if event not in on:
            continue
        spec = on[event] or {}
        filt = sorted(k for k in ("paths", "paths-ignore") if isinstance(spec, dict) and k in spec)
        out[event] = ",".join(filt) if filt else "unfiltered"
    return out


def needs_of(spec: object) -> list[str]:
    needs = (spec or {}).get("needs") if isinstance(spec, dict) else None
    if isinstance(needs, str):
        return [needs]
    return list(needs) if isinstance(needs, list) else []


def legs_315(doc: dict) -> list[dict]:
    found = []
    jobs = doc.get("jobs") or {}
    for job_id, job in jobs.items():
        matrix = ((job or {}).get("strategy") or {}).get("matrix") or {}
        if not isinstance(matrix, dict):
            continue
        includes = matrix.get("include") or []
        exp = [i for i in includes if isinstance(i, dict) and str(i.get("python-version", i.get("python", ""))) == "3.15"]
        if not exp:
            continue
        needers = sorted(j for j, spec in jobs.items() if job_id in needs_of(spec))
        found.append({
            "job": job_id,
            "name": str(job.get("name", job_id)),
            "experimental": [i.get("experimental") for i in exp],
            "job_coe": job.get("continue-on-error"),
            "needed_by": needers,
        })
    return found


def survey(repo: str) -> tuple[dict, list[str]]:
    errors: list[str] = []
    rec: dict = {"repo": repo, "rulesets": [], "workflows": []}
    try:
        rules = gh(f"repos/{OWNER}/{repo}/rules/branches/main")
        for r in rules:
            if r.get("type") != "required_status_checks":
                continue
            ctx = [c["context"] for c in r["parameters"]["required_status_checks"]]
            rec["rulesets"].append({"id": r.get("ruleset_id"), "count": len(ctx), "versioned": [c for c in ctx if VERSIONED.search(c)], "contexts": ctx})
    except RuntimeError as exc:
        errors.append(f"{repo}: rules: {exc}")
    try:
        listing = gh(f"repos/{OWNER}/{repo}/contents/.github/workflows?ref=main")
    except RuntimeError as exc:
        errors.append(f"{repo}: workflows: {exc}")
        return rec, errors
    for entry in listing:
        if not entry["name"].endswith((".yml", ".yaml")):
            continue
        try:
            blob = gh(f"repos/{OWNER}/{repo}/contents/{entry['path']}?ref=main")
            text = base64.b64decode(blob["content"]).decode("utf-8")
            doc = yaml.safe_load(text) or {}
        except (RuntimeError, yaml.YAMLError, KeyError) as exc:
            errors.append(f"{repo}: {entry['name']}: {exc}")
            continue
        legs = legs_315(doc)
        if legs:
            rec["workflows"].append({"file": entry["name"], "name": doc.get("name", entry["name"]), "on": triggers(doc), "legs": legs})
    return rec, errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", action="append", help="limit to these bare repo names")
    ap.add_argument("--json", action="store_true", help="print one JSON document instead of the text report")
    args = ap.parse_args()
    records, errors = [], []
    for repo in args.repo or REPOS:
        rec, errs = survey(repo)
        records.append(rec)
        errors.extend(errs)
    if args.json:
        print(json.dumps({"records": records, "errors": errors}, indent=2))
    else:
        for rec in records:
            print(f"=== {rec['repo']}")
            for rs in rec["rulesets"]:
                print(f"  ruleset {rs['id']}: {rs['count']} required contexts; versioned: {rs['versioned'] or 'none'}")
            if not rec["rulesets"]:
                print("  no required_status_checks rule readable on main")
            for wf in rec["workflows"]:
                on = ", ".join(f"{k}={v}" for k, v in wf["on"].items())
                print(f"  {wf['file']} ({wf['name']}) on: {on}")
                for leg in wf["legs"]:
                    print(f"    job {leg['job']!r} name {leg['name']!r}: experimental={leg['experimental']} job continue-on-error={leg['job_coe']!r}; needed by: {leg['needed_by'] or 'nothing'}")
        for err in errors:
            print(f"!! {err}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
