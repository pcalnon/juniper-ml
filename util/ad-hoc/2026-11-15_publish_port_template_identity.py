#!/usr/bin/env python3
"""Check a ported publish workflow against juniper-cascor's one-artifact template: identical steps, and the same wiring.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (port juniper-cascor#763 / #767's one-artifact publish fix to the other publishing repos)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor src/tests/unit/test_publish_one_artifact.py (the checks this applies across repos);
         util/ad-hoc/2026-11-15_publish_workflow_artifact_audit.py (the audit that found the 15 publishers to port)

Why
---
Each port copies juniper-cascor's template steps "verbatim", and each repo's own test can only compare the copies inside
that repo. This compares every copy in every repo with cascor's ``publish.yml`` (the template's source), step by step,
as parsed YAML, so a whitespace, comment-free or reordering difference in a run script fails here even when the repo's
own test passes. It also re-checks the wiring cascor's test pins (job chain and names, permissions, retention, no
``skip-existing``, the dispatch input, the build guard, the reuse condition, no checkout inside a template run).

    python3 -I util/ad-hoc/2026-11-15_publish_port_template_identity.py --template <cascor publish.yml> WORKFLOW [WORKFLOW ...]

Exit status: 0 when every workflow passes every check; 1 otherwise (each failure is printed).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REUSE = "Reuse an earlier attempt's artifact"
REUSE_IF = "steps.reuse.outputs.reuse != 'true'"
RECORD = "Record SHA256SUMS"
UPLOAD = "Upload dist artifacts"
DOWNLOAD = "Download dist artifacts"
VERIFY_DIST = "Verify the dist against SHA256SUMS"
TESTPYPI_AFTER = "Verify TestPyPI serves exactly these files"
TESTPYPI_BEFORE = "Verify TestPyPI still serves exactly these files"
PYPI_AFTER = "Verify PyPI serves exactly these files"
REPUBLISH = "republish"
PUBLISH_ACTION = "pypa/gh-action-pypi-publish@"
DIST_INPUT = "${{ env.PUBLISH_DIST_DIR }}/"
GATE_APPROVAL_DAYS = 30


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["on"] = data.pop(True, data.get("on"))
    return data


def names(job: dict) -> "list[str]":
    return [str(s.get("name") or s.get("uses") or "") for s in job.get("steps") or []]


def step(job: dict, name: str) -> "dict | None":
    found = [s for s in job.get("steps") or [] if s.get("name") == name]
    return found[0] if len(found) == 1 else None


def uploads(job: dict) -> "list[int]":
    return [i for i, s in enumerate(job.get("steps") or []) if str(s.get("uses") or "").startswith(PUBLISH_ACTION)]


def environment(job: dict) -> str:
    env = job.get("environment")
    return str(env.get("name") if isinstance(env, dict) else env)


def template(path: Path) -> "dict[str, dict]":
    jobs = load(path)["jobs"]
    want = {
        f"build/{REUSE}": step(jobs["build"], REUSE),
        f"build/{RECORD}": step(jobs["build"], RECORD),
        f"build/{UPLOAD}": step(jobs["build"], UPLOAD),
        f"test/{DOWNLOAD}": step(jobs["testpypi"], DOWNLOAD),
        f"test/{VERIFY_DIST}": step(jobs["testpypi"], VERIFY_DIST),
        f"test/{TESTPYPI_AFTER}": step(jobs["testpypi"], TESTPYPI_AFTER),
        f"prod/{DOWNLOAD}": step(jobs["pypi"], DOWNLOAD),
        f"prod/{VERIFY_DIST}": step(jobs["pypi"], VERIFY_DIST),
        f"prod/{TESTPYPI_BEFORE}": step(jobs["pypi"], TESTPYPI_BEFORE),
        f"prod/{PYPI_AFTER}": step(jobs["pypi"], PYPI_AFTER),
        "republish-job": jobs[REPUBLISH],
        "dispatch": load(path)["on"]["workflow_dispatch"],
    }
    missing = sorted(k for k, v in want.items() if v is None)
    if missing:
        raise SystemExit(f"template {path} lacks {missing}")
    return want


def check(path: Path, want: "dict[str, dict]") -> "list[str]":
    bad: list[str] = []
    wf = load(path)
    jobs = wf.get("jobs") or {}
    env = wf.get("env") or {}
    if set(env) != {"PUBLISH_PACKAGE", "PUBLISH_DIST_DIR"}:
        bad.append(f"workflow env is {env}, expected exactly PUBLISH_PACKAGE and PUBLISH_DIST_DIR")
    if (wf.get("on") or {}).get("workflow_dispatch") != want["dispatch"]:
        bad.append(f"workflow_dispatch is {(wf.get('on') or {}).get('workflow_dispatch')}, expected the template's")
    if set((wf.get("on") or {})) != {"release", "workflow_dispatch"} or (wf.get("on") or {}).get("release") != {"types": ["published"]}:
        bad.append(f"triggers are {wf.get('on')}, expected release: published and workflow_dispatch only")
    top = wf.get("permissions")
    if top not in ({}, {"contents": "read"}):
        bad.append(f"top-level permissions {top} must be {{}} or contents: read")
    test_ids = [j for j, job in jobs.items() if job.get("name") == "Publish to TestPyPI"]
    prod_ids = [j for j, job in jobs.items() if job.get("name") == "Publish to PyPI"]
    if len(test_ids) != 1 or len(prod_ids) != 1 or "build" not in jobs or REPUBLISH not in jobs:
        bad.append(f"jobs {sorted(jobs)}: need build, one 'Publish to TestPyPI', one 'Publish to PyPI' and republish")
        return bad
    test_id, prod_id = test_ids[0], prod_ids[0]
    build, test, prod = jobs["build"], jobs[test_id], jobs[prod_id]
    extra = sorted(set(jobs) - {"build", test_id, prod_id, REPUBLISH})
    if extra:
        print(f"    note: extra job(s) {extra}: check each needs and gates as intended")
    if build.get("name") != "Build and Validate" or "environment" in build or uploads(build):
        bad.append("the build job must be 'Build and Validate', hold no environment and upload nothing")
    if test.get("needs") != "build" or prod.get("needs") != test_id:
        bad.append(f"chain: {test_id}.needs={test.get('needs')}, {prod_id}.needs={prod.get('needs')}")
    if environment(test) != "testpypi" or environment(prod) != "pypi":
        bad.append(f"environments: {environment(test)}, {environment(prod)}")
    guard = str(build.get("if") or "")
    if "republish_from_testpypi" not in guard and "github.event_name == 'release'" not in guard and "github.event.release.tag_name" not in guard:
        bad.append(f"build guard {guard!r} lets the republish dispatch build")
    if "github.event_name != 'release'" in guard:
        bad.append(f"build guard {guard!r} runs on every non-release event, the republish dispatch included")
    # Permissions: only the uploading jobs mint.
    minting = sorted(j for j, job in jobs.items() if (job.get("permissions") or {}).get("id-token") == "write")
    uploading = sorted(j for j, job in jobs.items() if uploads(job))
    if minting != uploading or sorted(uploading) != sorted([test_id, prod_id, REPUBLISH]):
        bad.append(f"id-token: write is held by {minting}, uploads are in {uploading}")
    if (top or {}).get("id-token"):
        bad.append("top-level permissions hold id-token")
    # A check made non-blocking is a check switched off: no job of the chain may continue on error (a step-level
    # continue-on-error or if: on a template step already fails the step comparison below).
    for job_id in ("build", test_id, prod_id, REPUBLISH):
        if "continue-on-error" in jobs[job_id]:
            bad.append(f"job {job_id} sets continue-on-error, so its checks do not block")
    if build.get("permissions") != {"contents": "read", "actions": "read"}:
        bad.append(f"build permissions {build.get('permissions')}")
    if test.get("permissions") != {"contents": "read", "id-token": "write"}:
        bad.append(f"{test_id} permissions {test.get('permissions')}")
    if (prod.get("permissions") or {}).get("id-token") != "write" or set(prod.get("permissions") or {}) - {"contents", "id-token"}:
        bad.append(f"{prod_id} permissions {prod.get('permissions')}")
    # The template steps, as parsed YAML, equal cascor's.
    have = {
        f"build/{REUSE}": step(build, REUSE),
        f"build/{RECORD}": step(build, RECORD),
        f"build/{UPLOAD}": step(build, UPLOAD),
        f"test/{DOWNLOAD}": step(test, DOWNLOAD),
        f"test/{VERIFY_DIST}": step(test, VERIFY_DIST),
        f"test/{TESTPYPI_AFTER}": step(test, TESTPYPI_AFTER),
        f"prod/{DOWNLOAD}": step(prod, DOWNLOAD),
        f"prod/{VERIFY_DIST}": step(prod, VERIFY_DIST),
        f"prod/{TESTPYPI_BEFORE}": step(prod, TESTPYPI_BEFORE),
        f"prod/{PYPI_AFTER}": step(prod, PYPI_AFTER),
        "republish-job": jobs[REPUBLISH],
    }
    for key, value in have.items():
        if value != want[key]:
            bad.append(f"{key} differs from the template")
    # Reuse step first; every later build step skipped on reuse (a push-only gate excepted).
    steps = build.get("steps") or []
    if not steps or steps[0].get("name") != REUSE:
        bad.append("the reuse step is not the build job's first step")
    for s in steps[1:]:
        if s.get("if") != REUSE_IF and s.get("if") != "github.event_name == 'push'":
            bad.append(f"build step {s.get('name') or s.get('uses')} lacks if: {REUSE_IF}")
    upload = step(build, UPLOAD) or {}
    if int((upload.get("with") or {}).get("retention-days") or 0) <= GATE_APPROVAL_DAYS:
        bad.append("the artifact does not outlive the 30-day pypi gate")
    # Order, and no checkout inside the template run of each publish job.
    for job_id, job, sequence, last in (
        (test_id, test, [DOWNLOAD, VERIFY_DIST, "UPLOAD", TESTPYPI_AFTER], TESTPYPI_AFTER),
        (prod_id, prod, [DOWNLOAD, VERIFY_DIST, TESTPYPI_BEFORE, "UPLOAD", PYPI_AFTER], PYPI_AFTER),
    ):
        listed = names(job)
        ups = uploads(job)
        if len(ups) != 1:
            bad.append(f"{job_id} has {len(ups)} uploads")
            continue
        try:
            at = [ups[0] if n == "UPLOAD" else listed.index(n) for n in sequence]
        except ValueError as exc:
            bad.append(f"{job_id}: {exc}")
            continue
        if at != sorted(at):
            bad.append(f"{job_id}: steps out of order {list(zip(sequence, at))}")
        between = [str(s.get("uses") or "") for s in job["steps"][at[0] : listed.index(last)]]
        if [u for u in between if u.startswith("actions/checkout@")]:
            bad.append(f"{job_id}: a checkout runs between the download and {last}")
        installs = [i for i, s in enumerate(job["steps"]) if "pip install" in str(s.get("run") or "")]
        if job_id == test_id and (not installs or min(installs) < listed.index(TESTPYPI_AFTER)):
            bad.append(f"{job_id}: the install check must exist and follow {TESTPYPI_AFTER}")
    for job_id, job in jobs.items():
        for i in uploads(job):
            inputs = job["steps"][i].get("with") or {}
            if "skip-existing" in inputs:
                bad.append(f"{job_id}: an upload sets skip-existing")
            if inputs.get("packages-dir") != DIST_INPUT:
                bad.append(f"{job_id}: an upload takes packages-dir {inputs.get('packages-dir')}")
    if (test["steps"][uploads(test)[0]].get("with") or {}).get("repository-url") != "https://test.pypi.org/legacy/":
        bad.append(f"{test_id}: the upload does not target TestPyPI")
    if "repository-url" in (prod["steps"][uploads(prod)[0]].get("with") or {}):
        bad.append(f"{prod_id}: the upload names a repository-url")
    return bad


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("workflows", nargs="+", type=Path)
    args = parser.parse_args(argv)
    want = template(args.template)
    failed = 0
    for path in args.workflows:
        bad = check(path, want)
        env = load(path).get("env") or {}
        label = f"{path.parent.parent.parent.name}/{path.name}"
        print(f"{'PASS' if not bad else 'FAIL'} {label}  (PUBLISH_PACKAGE={env.get('PUBLISH_PACKAGE')}, PUBLISH_DIST_DIR={env.get('PUBLISH_DIST_DIR')})")
        for line in bad:
            print(f"    - {line}")
        failed += bool(bad)
    print(f"{len(args.workflows) - failed} of {len(args.workflows)} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
