#!/usr/bin/env python3
"""Audit every Juniper PyPI / TestPyPI publish workflow: does PyPI get the files TestPyPI took?

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- investigation (read-only audit behind the juniper-cascor one-artifact publish fix)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py (measured the symptom: PyPI's
         juniper-cascor 0.13.0 files differ from TestPyPI's by sha256); notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md
         section 10.3 (the "rebuild in the pypi job" decision, marked historical); util/release_train/ceremony.py
         ``classify_publish_run`` (reads publish job NAMES by substring)

Why
---
The owner's directive of 2026-11-15: "deploy to pypi should send the same artifact that was already sent to testpypi."
juniper-cascor's ``publish.yml`` ran ``python -m build`` in its TestPyPI job and again in its PyPI job, so for 0.13.0
and 0.14.0 PyPI serves a second build, with a different sha256, of what TestPyPI verified. This reads every publish
workflow on each repo's default branch and classifies it:

(a) BUILD: does each publish job download one artifact a build job made ("shared"), or run a build itself ("REBUILDS")?
(b) HASHES: does anything compare the files' sha256 with TestPyPI before the PyPI upload (and after the TestPyPI one)?
(c) SKIP: can the TestPyPI upload skip an existing file (``skip-existing``), so that the install check after it would
    test an OLDER file than the one this run built, and nothing would say so?

It also reports the shared artifact's ``retention-days``: the PyPI job downloads the artifact only after the owner
approves the ``pypi`` gate, which may wait up to 30 days, so an artifact that expires sooner strands the release; and
each publish job's NAME, which ``util/release_train/ceremony.py`` reads ("testpypi" in the name = the TestPyPI job;
"pypi" without "testpypi" = the PyPI job).

Read-only: every workflow is fetched with ``gh api repos/<owner>/<repo>/contents/<path>?ref=<branch>``; nothing is
written, approved, re-run or cancelled. Output goes to stdout.

    python3 -I util/ad-hoc/2026-11-15_publish_workflow_artifact_audit.py
    python3 -I util/ad-hoc/2026-11-15_publish_workflow_artifact_audit.py --repo juniper-cascor --verbose

Exit status: 0 when the audit ran (whatever it found); 2 when a repository or workflow could not be read.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess  # nosec B404 -- runs gh with a fixed argv
import sys

import yaml

OWNER = "pcalnon"
#: The repositories the brief names; juniper-deploy is included in case it publishes anything.
REPOS = (
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-recurrence",
    "juniper-ml",
    "juniper-deploy",
)
PUBLISH_ACTION = "pypa/gh-action-pypi-publish"
TWINE_UPLOAD = re.compile(r"\btwine\s+upload\b")
BUILD_COMMAND = re.compile(r"\bpython3?\s+-m\s+build\b|\buv\s+build\b|\bhatch\s+build\b|\bpoetry\s+build\b|\bflit\s+build\b|\bpip3?\s+wheel\b|\bsetup\.py\s+(?:sdist|bdist_wheel)\b|\bpyproject-build\b")
HASH_WORD = re.compile(r"sha256|digests|SHA256SUMS", re.IGNORECASE)


class Unreadable(Exception):
    """A repository or workflow file could not be read; the audit refuses rather than guessing."""


def gh_json(path: str) -> object:
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)  # nosec B603 B607 -- fixed argv
    if proc.returncode != 0:
        raise Unreadable(f"gh api {path}: {proc.stderr.strip() or proc.stdout.strip()}")
    return json.loads(proc.stdout)


def default_branch(repo: str) -> str:
    meta = gh_json(f"repos/{OWNER}/{repo}")
    return str(meta["default_branch"])


def workflow_files(repo: str, ref: str) -> list[tuple[str, str]]:
    """Return ``(path, text)`` for every workflow file on ``ref``; an absent workflows directory is an empty list."""
    proc = subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/contents/.github/workflows?ref={ref}"], capture_output=True, text=True, check=False)  # nosec B603 B607 -- fixed argv
    if proc.returncode != 0:
        if "Not Found" in proc.stdout or "Not Found" in proc.stderr:
            return []
        raise Unreadable(f"{repo}: cannot list the workflows directory: {proc.stderr.strip()}")
    listing = json.loads(proc.stdout)
    found = []
    for entry in listing:
        name = entry.get("name") or ""
        if entry.get("type") != "file" or not name.endswith((".yml", ".yaml")):
            continue
        blob = gh_json(f"repos/{OWNER}/{repo}/contents/{entry['path']}?ref={ref}")
        content = blob.get("content") or ""
        if not content:
            raise Unreadable(f"{repo}: {entry['path']} came back without inline content (over 1 MB?)")
        found.append((entry["path"], base64.b64decode(content).decode("utf-8")))
    return found


def step_text(step: dict) -> str:
    """Everything a step says, for pattern matching: its run script, its action, its inputs and its env.

    The env matters: the one-artifact template's JSON checks name their index only in ``env: INDEX_URL``, so without
    it this audit read juniper-cascor's pre-PyPI check ("Verify TestPyPI still serves exactly these files") as absent.
    """
    return "\n".join([str(step.get("run") or ""), str(step.get("uses") or ""), json.dumps(step.get("with") or {}, sort_keys=True), json.dumps(step.get("env") or {}, sort_keys=True)])


def publish_target(step: dict) -> "str | None":
    """``testpypi`` / ``pypi`` when the step uploads a distribution, else ``None``."""
    uses = str(step.get("uses") or "")
    if uses.startswith(PUBLISH_ACTION):
        url = str((step.get("with") or {}).get("repository-url") or "")
        return "testpypi" if "test.pypi.org" in url else "pypi"
    run = str(step.get("run") or "")
    if TWINE_UPLOAD.search(run):
        return "testpypi" if ("test.pypi.org" in run or "testpypi" in run) else "pypi"
    return None


def skips_existing(step: dict) -> bool:
    value = (step.get("with") or {}).get("skip-existing")
    if value is True or str(value).strip().lower() == "true":
        return True
    return "--skip-existing" in str(step.get("run") or "")


def environment_name(job: dict) -> str:
    env = job.get("environment")
    if isinstance(env, dict):
        return str(env.get("name") or "")
    return str(env or "")


def audit_workflow(path: str, text: str) -> "dict | None":
    """Classify one workflow, or return ``None`` when it uploads nothing to an index."""
    doc = yaml.safe_load(text) or {}
    jobs = doc.get("jobs") or {}
    triggers = doc.get(True, doc.get("on"))  # PyYAML reads the bare key ``on`` as the boolean True
    trigger_names = sorted(triggers) if isinstance(triggers, dict) else ([triggers] if isinstance(triggers, str) else sorted(triggers or []))
    uploads: dict[str, dict] = {}
    publish_jobs = []
    for job_id, job in jobs.items():
        steps = job.get("steps") or []
        targets = [(i, publish_target(s)) for i, s in enumerate(steps)]
        targets = [(i, t) for i, t in targets if t]
        for s in steps:
            if str(s.get("uses") or "").startswith("actions/upload-artifact"):
                with_ = s.get("with") or {}
                uploads[str(with_.get("name") or "artifact")] = {"job": job_id, "retention": with_.get("retention-days")}
        if not targets:
            continue
        downloads = [str((s.get("with") or {}).get("name") or "*") for s in steps if str(s.get("uses") or "").startswith("actions/download-artifact")]
        builds = [str(s.get("name") or s.get("run") or "").splitlines()[0] for s in steps if BUILD_COMMAND.search(str(s.get("run") or ""))]
        first = targets[0][0]
        before = steps[:first]
        after = steps[first + 1 :]
        publish_jobs.append(
            {
                "id": job_id,
                "name": str(job.get("name") or job_id),
                "environment": environment_name(job),
                "needs": job.get("needs"),
                "if": job.get("if"),
                "targets": sorted({t for _, t in targets}),
                "skip_existing": any(skips_existing(steps[i]) for i, t in targets if t == "testpypi"),
                "downloads": downloads,
                "builds": builds,
                # A pre-upload comparison with TestPyPI: a step before the upload that reads TestPyPI and hashes.
                "pre_hash_vs_testpypi": [str(s.get("name") or "?") for s in before if "test.pypi.org" in step_text(s) and HASH_WORD.search(step_text(s))],
                # A post-upload check that the index serves these hashes.
                "post_hash": [str(s.get("name") or "?") for s in after if HASH_WORD.search(step_text(s)) and ("pypi.org" in step_text(s) or "INDEX_URL" in step_text(s))],
            }
        )
    if not publish_jobs:
        return None
    # What a port of the one-artifact template needs to know: where each job builds, what it uploads, what it publishes.
    details = []
    for job_id, job in jobs.items():
        steps = job.get("steps") or []
        workdir = ((job.get("defaults") or {}).get("run") or {}).get("working-directory")
        pythons = sorted({str((s.get("with") or {}).get("python-version")) for s in steps if str(s.get("uses") or "").startswith("actions/setup-python")})
        ups = [f"{(s.get('with') or {}).get('name')}<-{str((s.get('with') or {}).get('path')).strip()}" for s in steps if str(s.get("uses") or "").startswith("actions/upload-artifact")]
        downs = [f"{(s.get('with') or {}).get('name')}->{(s.get('with') or {}).get('path')}" for s in steps if str(s.get("uses") or "").startswith("actions/download-artifact")]
        pubs = [f"{publish_target(s)}:{(s.get('with') or {}).get('packages-dir', 'dist(default)')}" for s in steps if publish_target(s)]
        checkouts = sum(1 for s in steps if str(s.get("uses") or "").startswith("actions/checkout"))
        details.append(f"{job_id} name={job.get('name')!r} env={environment_name(job) or '-'} needs={job.get('needs')} if={job.get('if')} workdir={workdir} python={pythons} checkouts={checkouts} uploads={ups} downloads={downs} publishes={pubs}")
    test_jobs = [j for j in publish_jobs if "testpypi" in j["targets"]]
    prod_jobs = [j for j in publish_jobs if "pypi" in j["targets"]]
    rebuilding = [j["id"] for j in publish_jobs if j["builds"]]
    if not rebuilding and all(j["downloads"] for j in publish_jobs):
        names = sorted({n for j in publish_jobs for n in j["downloads"]})
        made_by = sorted({uploads[n]["job"] for n in names if n in uploads})
        build = f"shared ({', '.join(names)} from {', '.join(made_by) or '?'})"
    elif rebuilding and len(rebuilding) == len(publish_jobs):
        build = f"REBUILDS in every publish job ({', '.join(rebuilding)})"
    elif rebuilding:
        build = f"MIXED: {', '.join(rebuilding)} build(s) their own"
    else:
        build = "UNCLEAR: a publish job neither builds nor downloads"
    retention = sorted({str(uploads[n]["retention"]) for j in publish_jobs for n in j["downloads"] if n in uploads})
    pre = [n for j in prod_jobs for n in j["pre_hash_vs_testpypi"]]
    post_test = [n for j in test_jobs for n in j["post_hash"]]
    return {
        "path": path,
        "name": str(doc.get("name") or path),
        "triggers": trigger_names,
        "concurrency": doc.get("concurrency") is not None,
        "build": build,
        "hash_before_pypi": ("yes: " + "; ".join(pre)) if pre else "no",
        "hash_after_testpypi": ("yes: " + "; ".join(post_test)) if post_test else "no",
        "skip_existing": "YES" if any(j["skip_existing"] for j in test_jobs) else ("no" if test_jobs else "n/a (no TestPyPI job)"),
        "retention": ",".join(retention) if retention else "-",
        "jobs": publish_jobs,
        "details": details,
    }


def ceremony_reading(row: dict) -> str:
    """How ``ceremony.classify_publish_run`` would sort this run's publish jobs, by name substring."""
    notes = []
    for job in row["jobs"]:
        lowered = job["name"].lower()
        is_test = "testpypi" in lowered
        is_prod = "pypi" in lowered and not is_test
        if "testpypi" in job["targets"] and not is_test:
            notes.append(f"{job['name']!r} uploads to TestPyPI but the ceremony would not read it as the TestPyPI job")
        if "pypi" in job["targets"] and not is_prod:
            notes.append(f"{job['name']!r} uploads to PyPI but the ceremony would not read it as the PyPI job")
    return "; ".join(notes) if notes else "names match the ceremony's substrings"


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", action="append", help="audit only this repository (repeatable); default: all nine")
    parser.add_argument("--verbose", action="store_true", help="print each publish job's environment, needs, guard and evidence")
    parser.add_argument("--details", action="store_true", help="print every job's working directory, Python, checkouts, artifact uploads/downloads and publish steps")
    args = parser.parse_args(argv)
    repos = tuple(args.repo) if args.repo else REPOS
    rows = []
    quiet = []
    try:
        for repo in repos:
            ref = default_branch(repo)
            audited = [audit_workflow(path, text) for path, text in workflow_files(repo, ref)]
            hits = [r for r in audited if r]
            if not hits:
                quiet.append(f"{repo}@{ref}")
            for row in hits:
                row["repo"] = repo
                row["ref"] = ref
                rows.append(row)
    except Unreadable as exc:
        print(f"REFUSED: {exc}")
        return 2
    header = ("repo", "workflow", "(a) build", "(b) sha256 vs TestPyPI before PyPI", "(b') after TestPyPI upload", "(c) TestPyPI skip-existing", "artifact retention-days", "dispatch")
    print("| " + " | ".join(header) + " |")
    print("|" + "|".join("---" for _ in header) + "|")
    for row in rows:
        dispatch = "yes" if "workflow_dispatch" in row["triggers"] else "no"
        cells = (row["repo"], row["path"].rsplit("/", 1)[-1], row["build"], row["hash_before_pypi"], row["hash_after_testpypi"], row["skip_existing"], row["retention"], dispatch)
        print("| " + " | ".join(cells) + " |")
    print()
    print("Publish job names (the release-train ceremony classifies by them):")
    for row in rows:
        names = ", ".join(f"{j['id']}={j['name']!r} [{'+'.join(j['targets'])}, env {j['environment'] or '-'}]" for j in row["jobs"])
        print(f"  {row['repo']}/{row['path'].rsplit('/', 1)[-1]}: {names} -- {ceremony_reading(row)}")
        if args.verbose:
            for job in row["jobs"]:
                print(f"      {job['id']}: needs={job['needs']} if={job['if']} downloads={job['downloads']} builds={job['builds']} pre={job['pre_hash_vs_testpypi']} post={job['post_hash']}")
        if args.details:
            print(f"      triggers={row['triggers']} concurrency={row['concurrency']}")
            for line in row["details"]:
                print(f"      {line}")
    if quiet:
        print()
        print("No PyPI/TestPyPI upload in any workflow: " + ", ".join(quiet))
    print()
    rebuild = sum(1 for r in rows if r["build"].startswith(("REBUILDS", "MIXED")))
    unchecked = sum(1 for r in rows if r["hash_before_pypi"] == "no")
    skipping = sum(1 for r in rows if r["skip_existing"] == "YES")
    print(f"{len(rows)} publish workflow(s) in {len({r['repo'] for r in rows})} repo(s): {rebuild} rebuild per publish job, {unchecked} compare no sha256 with TestPyPI before PyPI, {skipping} can skip an existing TestPyPI file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
