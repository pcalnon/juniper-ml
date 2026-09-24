#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     2.0.0
License:     MIT License

CLASS 2 sweep: does each PUBLISHED Juniper image actually DO ITS JOB?

WHY THIS EXISTS
---------------
`memory/reference_juniper_deploy_image_publish_traps.md` names TWO defect classes to check
before publishing any Juniper image. Class 1 (secrets reachable from the build context) is
covered by `2026-09-21_image_build_context_sweep.py`. **This is class 2**, and it is the one
that actually bit:

    juniper-deploy's containerized test runner ran ZERO tests from 2026-03-13 to 2026-09-17.
    The image BUILT. It STARTED. It looked fine from outside. It died at conftest import on
    every run, for six months, because nothing asserted the suite was runnable.

    "It builds" is not "it works". Assert the artifact's PURPOSE.

WHAT IT CHECKS, IN ESCALATING ORDER
-----------------------------------
  T1  IMPORT    -- the application package imports inside the image, AND its `__version__`
                   equals the installed distribution's metadata version.
  T2  ENTRYPOINT-- the image's console script answers `--help`.
  T3  SERVE     -- the image's OWN entrypoint + command, started exactly as `docker run IMG`
                   starts it, answers 200 on its LIVENESS endpoint (`/v1/health`), probed from
                   inside the container. Readiness is deliberately not probed: a standalone
                   container has no backing services, so `/ready` answering 503 is the probe
                   working, not the image failing.
  T4  VERSION   -- every version the RUNNING service reports equals the installed metadata:
                   the `version` field of the `/v1/health` body, and -- where the service wraps
                   its responses in an envelope -- `meta.version` of an enveloped response.

WHAT v2.0.0 FIXED (2026-09-23), per the 09-22 container-registry handoff's item-5 detail
------------------------------------------------------------------------------------------
v1.0.0 passed two images it should have failed, and could not see a third:

* **An absent `__version__` scored PASS.** The probe printed MISMATCH only when a version was
  present AND different, so `ABSENT` fell through to PASS. That is how juniper-cascor 0.11.0
  passed: its image ships no `juniper_cascor` package at all (the Dockerfile copies `src/`),
  the import target was `cascade_correlation`, which has no `__version__`, and the envelope's
  `meta.version` -- the image's real version surface -- read `0.6.0` in a 0.11.0 image
  (cascor#668; fixed on `main` by cascor#672, from the next release). v2 scores ABSENT as FAIL
  unless the row declares that the image has no version-bearing package, and then T4 must carry
  the check on a served surface instead.
* **The tags were hard-coded** at the 2026-09-21 releases, so every run after the next release
  swept images nobody deploys. v2 resolves each repo's newest Release from GitHub
  (`releases/latest`, which the ceremony keeps current since juniper-ml#2055) and prints the
  ref it swept. `--image name:tag` overrides.
* **The worker's serve check was skipped** ("no HTTP healthcheck"). The worker DOES serve
  `/v1/health` -- on 127.0.0.1:8210 inside its container -- so v2 probes it there. Its Docker
  HEALTHCHECK is `kill -0 1`, which proves only that PID 1 exists; that is recorded, not fixed.

Read-only with respect to the repos. It PULLS and RUNS public images; it pushes nothing and
writes nothing outside stdout. Requires `docker` and `gh`. Exit 0 when every check that applies
passes, 1 when any fails, 2 when an image could not be pulled or a tag could not be resolved --
an unswept image is not a clean one.

Usage:
    python3 util/ad-hoc/2026-09-21_image_does_its_job_sweep.py
    python3 util/ad-hoc/2026-09-21_image_does_its_job_sweep.py --image juniper-cascor:0.11.0 --image juniper-data:0.16.0
    python3 util/ad-hoc/2026-09-21_image_does_its_job_sweep.py --only juniper-cascor-worker --verbose
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass

REGISTRY = "ghcr.io/pcalnon"
RUN_TIMEOUT = 120
SERVE_WAIT = 60


@dataclass(frozen=True)
class Row:
    repo: str  # the image name == the owning repo
    tag_prefix: str  # the repo's primary release tag prefix, stripped to get the image tag
    module: str | None  # the version-bearing application package; None = the image ships none
    dist: str  # the distribution whose metadata is the truth
    script: str | None  # console script for T2, or None
    port: int  # the liveness port INSIDE the container
    enveloped_path: str | None  # an endpoint whose response carries meta.version, or None
    why_no_module: str = ""


ROWS = {
    # The cascor IMAGE ships `src/` and the dist-info, not the `juniper_cascor` package
    # (Dockerfile copies pyproject.toml, README.md, LICENSE and src/), so there is no
    # in-package __version__ to compare. Its version surfaces are served: /v1/health and the
    # response envelope. `/v1/workers` is enveloped and needs no backing service.
    "juniper-cascor": Row("juniper-cascor", "v", None, "juniper-cascor", None, 8200, "/v1/workers", "the image ships src/, not the juniper_cascor package"),
    "juniper-data": Row("juniper-data", "v", "juniper_data", "juniper-data", None, 8100, None),
    "juniper-canopy": Row("juniper-canopy", "v", "juniper_canopy", "juniper-canopy", None, 8050, None),
    "juniper-cascor-worker": Row("juniper-cascor-worker", "v", "juniper_cascor_worker", "juniper-cascor-worker", "juniper-cascor-worker", 8210, None),
    "juniper-recurrence": Row("juniper-recurrence", "juniper-recurrence-v", "juniper_recurrence", "juniper-recurrence", "juniper-recurrence", 8210, None),
}


def sh(args: list[str], timeout: int = RUN_TIMEOUT) -> tuple[int, str]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT after {timeout}s"
    except Exception as exc:  # pragma: no cover - environment failure
        return 125, f"{type(exc).__name__}: {exc}"


def resolve_tag(row: Row) -> str | None:
    code, out = sh(["gh", "api", f"repos/pcalnon/{row.repo}/releases/latest", "--jq", ".tag_name"], timeout=60)
    if code != 0 or not out.startswith(row.tag_prefix):
        return None
    return out[len(row.tag_prefix) :]


def metadata_version(ref: str, dist: str) -> str | None:
    code, out = sh(["docker", "run", "--rm", "--entrypoint", "python", ref, "-c", f"import importlib.metadata as m; print(m.version({dist!r}))"])
    return out.splitlines()[-1].strip() if code == 0 and out else None


def t1_import(ref: str, row: Row, dist_version: str | None) -> tuple[str, str]:
    if row.module is None:
        return "N/A", f"{row.why_no_module}; T4 carries the version check"
    probe = f"import {row.module} as m; print(getattr(m, '__version__', 'ABSENT'))"
    code, out = sh(["docker", "run", "--rm", "--entrypoint", "python", ref, "-c", probe])
    if code != 0:
        return "FAIL", (out.splitlines()[-1] if out else f"exit {code}")[:100]
    version = out.splitlines()[-1].strip()
    if version == "ABSENT":
        return "FAIL", f"{row.module} imports but has no __version__ (v1 scored this PASS)"
    if version != dist_version:
        return "FAIL", f"__version__ {version} != metadata {dist_version}"
    return "PASS", f"__version__ {version} == metadata"


def t2_entrypoint(ref: str, script: str | None) -> tuple[str, str]:
    if script is None:
        return "N/A", "no console script"
    code, out = sh(["docker", "run", "--rm", "--entrypoint", script, ref, "--help"])
    if code == 0:
        return "PASS", next((line for line in out.splitlines() if line.strip()), "")[:70]
    return "FAIL", (out.splitlines()[-1] if out else f"exit {code}")[:90]


def _get_json(cname: str, port: int, path: str) -> tuple[int | None, dict | None, str]:
    probe = (
        "import json, sys, urllib.request, urllib.error\n"
        f"try:\n    r = urllib.request.urlopen('http://127.0.0.1:{port}{path}', timeout=4)\n"
        "    status, body = r.status, r.read()\n"
        "except urllib.error.HTTPError as e:\n    status, body = e.code, e.read()\n"
        "print(status); print(body.decode('utf-8', 'replace'))\n"
    )
    code, out = sh(["docker", "exec", cname, "python", "-c", probe], timeout=20)
    if code != 0 or not out:
        return None, None, (out.splitlines()[-1] if out else f"exit {code}")[:90]
    status_line, _, body = out.partition("\n")
    try:
        return int(status_line), json.loads(body), ""
    except ValueError:
        return (int(status_line) if status_line.isdigit() else None), None, body[:90]


def t3_t4_serve(name: str, ref: str, row: Row, dist_version: str | None, verbose: bool) -> tuple[tuple[str, str], tuple[str, str]]:
    cname = f"juniper-class2-{name}"
    sh(["docker", "rm", "-f", cname], timeout=30)
    # No -p: the probe runs INSIDE the container, so a service bound to 127.0.0.1 (the worker's
    # health server) is reachable, and no host port can collide.
    code, out = sh(["docker", "run", "-d", "--name", cname, ref], timeout=60)
    if code != 0:
        return ("FAIL", f"container did not start: {(out.splitlines()[-1] if out else code)}"[:100]), ("N/A", "not served")
    try:
        deadline = time.time() + SERVE_WAIT
        status, body, err = None, None, ""
        while time.time() < deadline:
            running = sh(["docker", "inspect", "-f", "{{.State.Running}}", cname], timeout=15)[1]
            if running != "true":
                logs = sh(["docker", "logs", "--tail", "5", cname], timeout=20)[1]
                return ("FAIL", f"container exited; logs: {logs.splitlines()[-1][:80] if logs else '-'}"), ("N/A", "not served")
            status, body, err = _get_json(cname, row.port, "/v1/health")
            if status == 200:
                break
            time.sleep(3)
        if status != 200:
            logs = sh(["docker", "logs", "--tail", "3", cname], timeout=20)[1]
            return ("FAIL", f"no 200 on /v1/health in {SERVE_WAIT}s (last {status} {err}); logs: {logs.splitlines()[-1][:60] if logs else '-'}"), ("N/A", "not served")
        if verbose:
            print(f"      /v1/health body: {json.dumps(body)[:300]}")
        t3 = ("PASS", f"/v1/health -> 200 on :{row.port}")

        # T4: every served version surface must equal the metadata. A body with no version
        # field is reported, not scored PASS.
        findings: list[str] = []
        served = (body or {}).get("version") if isinstance(body, dict) else None
        if served is None:
            findings.append("/v1/health carries no version field")
        elif served != dist_version:
            findings.append(f"/v1/health version {served} != metadata {dist_version}")
        if row.enveloped_path:
            e_status, e_body, e_err = _get_json(cname, row.port, row.enveloped_path)
            meta_version = ((e_body or {}).get("meta") or {}).get("version") if isinstance(e_body, dict) else None
            if verbose:
                print(f"      {row.enveloped_path} -> {e_status}: {json.dumps(e_body)[:300] if e_body is not None else e_err}")
            if meta_version is None:
                findings.append(f"{row.enveloped_path} ({e_status}) carries no meta.version")
            elif meta_version != dist_version:
                findings.append(f"{row.enveloped_path} meta.version {meta_version} != metadata {dist_version}")
        mismatches = [f for f in findings if "!=" in f]
        if mismatches:
            return t3, ("FAIL", "; ".join(findings))
        if findings:
            return t3, ("WARN", "; ".join(findings))
        return t3, ("PASS", f"served version(s) == metadata {dist_version}")
    finally:
        sh(["docker", "rm", "-f", cname], timeout=30)


def main() -> int:
    parser = argparse.ArgumentParser(description="Class-2 sweep of the published Juniper images.")
    parser.add_argument("--image", action="append", default=[], help="name:tag to sweep instead of the newest Release (repeatable)")
    parser.add_argument("--only", action="append", default=[], help="sweep only this image name (repeatable)")
    parser.add_argument("--verbose", action="store_true", help="print each image's config and served bodies")
    args = parser.parse_args()

    if shutil.which("docker") is None:
        print("docker not available -- a class-2 sweep REQUIRES running the artifact; do not substitute reading it.")
        return 2

    overrides = dict(item.split(":", 1) for item in args.image)
    names = args.only or list(ROWS)
    print("CLASS 2 SWEEP v2 -- does each PUBLISHED image do its job?")
    print("T1 import+__version__ | T2 entrypoint | T3 serve /v1/health | T4 served version == metadata\n")

    worst = 0
    rows_out = []
    for name in names:
        row = ROWS[name]
        tag = overrides.get(name) or resolve_tag(row)
        if tag is None:
            print(f"── {name}: could not resolve the newest Release tag -- NOT SWEPT\n")
            rows_out.append((name, "-", "UNRESOLVED", "-", "-", "-"))
            worst = max(worst, 2)
            continue
        ref = f"{REGISTRY}/{name}:{tag}"
        print(f"── {ref}")
        code, out = sh(["docker", "pull", "-q", ref], timeout=900)
        if code != 0:
            print(f"   PULL FAILED -- NOT SWEPT: {out.splitlines()[-1] if out else code}\n")
            rows_out.append((name, tag, "PULL-FAIL", "-", "-", "-"))
            worst = max(worst, 2)
            continue
        if args.verbose:
            config = sh(["docker", "inspect", "--format", "{{json .Config}}", ref], timeout=30)[1]
            try:
                c = json.loads(config)
                print(f"      entrypoint={c.get('Entrypoint')} cmd={c.get('Cmd')} exposed={list((c.get('ExposedPorts') or {}))} healthcheck={((c.get('Healthcheck') or {}).get('Test'))} user={c.get('User')!r}")
            except ValueError:
                print(f"      config: {config[:200]}")

        dist_version = metadata_version(ref, row.dist)
        print(f"   metadata {row.dist} = {dist_version}")
        s1, d1 = t1_import(ref, row, dist_version)
        print(f"   T1 import        {s1:<5} {d1}")
        s2, d2 = t2_entrypoint(ref, row.script)
        print(f"   T2 entrypoint    {s2:<5} {d2}")
        (s3, d3), (s4, d4) = t3_t4_serve(name, ref, row, dist_version, args.verbose)
        print(f"   T3 serve         {s3:<5} {d3}")
        print(f"   T4 version       {s4:<5} {d4}\n")
        rows_out.append((name, tag, s1, s2, s3, s4))
        if "FAIL" in (s1, s2, s3, s4) or dist_version != tag:
            worst = max(worst, 1)
        if dist_version != tag:
            print(f"   !! the image tagged {tag} carries metadata {dist_version}\n")

    print("SUMMARY")
    print(f"{'image':<24} {'tag':<8} {'T1':<6} {'T2':<6} {'T3':<6} {'T4'}")
    for r in rows_out:
        print(f"{r[0]:<24} {r[1]:<8} {r[2]:<6} {r[3]:<6} {r[4]:<6} {r[5]}")
    print(f"\nexit={worst}")
    return worst


if __name__ == "__main__":
    sys.exit(main())
