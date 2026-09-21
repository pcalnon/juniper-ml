#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     1.0.0
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

WHY THE PUBLISH PATH IS THE RIGHT TARGET
----------------------------------------
In all five image repos the import smoke test is gated:

    if: github.event_name != 'release' && !inputs.push

so on a **release** -- the path that actually ships -- the only in-image execution is
`check_image_cpu_only.py`, a distribution census plus torch-posture check that **never
imports the application**. The `/v1/health` probe exists only in `ci.yml`, against a
*locally built* image. So nothing today proves a PUBLISHED service image can serve. That is
precisely the shape of the six-month defect, and this script is the missing assertion.

WHAT IT CHECKS, IN ESCALATING ORDER
-----------------------------------
  T1  IMPORT    -- can the application package be imported inside the image?
                   This is the direct analogue of the conftest ImportError. Dependency-free,
                   fast, and decisive: a failure here means the image cannot possibly work.
  T2  ENTRYPOINT-- does the image's declared entry resolve and respond to a trivial
                   invocation (console script `--help`)? Proves the wiring, not just the
                   package.
  T3  SERVE     -- does the real CMD start and the HEALTHCHECK endpoint answer 200?
                   The strongest signal, but several images legitimately need backing
                   services, so a T3 failure is reported with its reason and is NOT treated
                   as equivalent to a T1 failure.

A NOTE ON ONE HEALTHCHECK, because it is a vacuous-pass instance
----------------------------------------------------------------
`juniper-cascor-worker/Dockerfile:120` is `CMD kill -0 1` -- it asserts only that PID 1
exists. A worker that booted, failed to connect and is sitting idle passes it. Compare the
other four, which all probe a real HTTP endpoint. Recorded, not fixed here.

Read-only with respect to the repos. It PULLS and RUNS public images; it pushes nothing and
writes nothing outside stdout. Requires `docker`. Exits 0 always -- a report, not a gate.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time

REGISTRY = "ghcr.io/pcalnon"

# name -> (tag, import target, console script or None, health port, health path, dist name)
#
# Use the LIVENESS endpoint, not readiness. A standalone container has no backing services,
# so cascor's `/v1/health/ready` correctly answers 503 {"status":"not_ready"} -- that is the
# probe working, not the image failing. v1.0.0 of this script pointed at `/v1/health/ready`
# and scored cascor FAIL: the instrument was answering an adjacent question. `/v1/health`
# and `/v1/health/live` both return 200.
IMAGES = {
    "juniper-cascor": ("0.11.0", "cascade_correlation", None, 8200, "/v1/health", "juniper-cascor"),
    "juniper-data": ("0.14.0", "juniper_data", None, 8100, "/v1/health", "juniper-data"),
    "juniper-canopy": ("0.8.0", "juniper_canopy", None, 8050, "/v1/health", "juniper-canopy"),
    "juniper-cascor-worker": ("0.6.0", "juniper_cascor_worker", "juniper-cascor-worker", None, None, "juniper-cascor-worker"),
    "juniper-recurrence": ("0.5.0", "juniper_recurrence", "juniper-recurrence", 8210, "/v1/health", "juniper-recurrence"),
}

RUN_TIMEOUT = 120
SERVE_WAIT = 45


def sh(args: list[str], timeout: int = RUN_TIMEOUT) -> tuple[int, str]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT after {timeout}s"
    except Exception as exc:  # pragma: no cover - environment failure
        return 125, f"{type(exc).__name__}: {exc}"


def t1_import(ref: str, module: str, dist: str) -> tuple[str, str]:
    """Import the app package AND cross-check `__version__` against distribution metadata.

    The cross-check is not decoration. juniper-cascor-worker:0.6.0 imports fine and reports
    `__version__ == "0.4.0"` while its metadata says 0.6.0 -- `__init__.py` was never bumped
    past 0.4.0, so two releases shipped a stale in-package version. An import-only check
    passes that silently, which is the vacuous-pass class all over again.
    """
    probe = (
        f"import {module} as m, importlib.metadata as md;"
        f"v=getattr(m,'__version__','ABSENT');"
        f"d=md.version('{dist}');"
        "print('ok', v, '| dist', d, '| MISMATCH' if v not in ('ABSENT', d) else '')"
    )
    code, out = sh(["docker", "run", "--rm", "--entrypoint", "python", ref, "-c", probe])
    if code != 0:
        return "FAIL", out.splitlines()[-1] if out else f"exit {code}"
    last = out.splitlines()[-1] if out else "ok"
    return ("MISMATCH" if "MISMATCH" in last else "PASS"), last


def t2_entrypoint(ref: str, script: str | None) -> tuple[str, str]:
    if script is None:
        return "N/A", "no console script (CMD runs a file path)"
    code, out = sh(["docker", "run", "--rm", "--entrypoint", script, ref, "--help"])
    if code == 0:
        first = next((line for line in out.splitlines() if line.strip()), "")
        return "PASS", first[:70]
    return "FAIL", out.splitlines()[-1][:90] if out else f"exit {code}"


def t3_serve(name: str, ref: str, port: int | None, path: str | None) -> tuple[str, str]:
    if port is None:
        return "N/A", "no HTTP healthcheck (worker uses `kill -0 1` -- vacuous)"
    cname = f"juniper-class2-{name}"
    sh(["docker", "rm", "-f", cname], timeout=30)
    code, out = sh(["docker", "run", "-d", "--name", cname, "-p", f"{port}:{port}", ref], timeout=60)
    if code != 0:
        return "FAIL", f"container did not start: {out.splitlines()[-1][:80] if out else code}"
    try:
        probe = (
            "import urllib.request,sys;"
            f"r=urllib.request.urlopen('http://127.0.0.1:{port}{path}',timeout=4);"
            "print(r.status)"
        )
        deadline = time.time() + SERVE_WAIT
        last = ""
        while time.time() < deadline:
            c, o = sh(["docker", "exec", cname, "python", "-c", probe], timeout=15)
            if c == 0 and "200" in o:
                return "PASS", f"{path} -> 200"
            last = o.splitlines()[-1][:80] if o else f"exit {c}"
            rc, _ = sh(["docker", "inspect", "-f", "{{.State.Running}}", cname], timeout=15)
            time.sleep(3)
        lc, logs = sh(["docker", "logs", "--tail", "3", cname], timeout=20)
        return "FAIL", f"no 200 in {SERVE_WAIT}s; last={last}; logs={logs.splitlines()[-1][:70] if logs else ''}"
    finally:
        sh(["docker", "rm", "-f", cname], timeout=30)


def main() -> int:
    if shutil.which("docker") is None:
        print("docker not available -- cannot run a class-2 sweep. "
              "This check REQUIRES running the artifact; do not substitute reading it.")
        return 0

    print("CLASS 2 SWEEP -- does each PUBLISHED image do its job?")
    print("T1 import (decisive) | T2 entrypoint | T3 serve (dependency-sensitive)\n")

    rows = []
    for name, (tag, module, script, port, path, dist) in IMAGES.items():
        ref = f"{REGISTRY}/{name}:{tag}"
        print(f"── {name}:{tag}")
        code, _ = sh(["docker", "pull", "-q", ref], timeout=900)
        if code != 0:
            print("   PULL FAILED -- skipping\n")
            rows.append((name, "PULL-FAIL", "-", "-"))
            continue

        s1, d1 = t1_import(ref, module, dist)
        print(f"   T1 import {module:<24} {s1}  {d1}")
        s2, d2 = t2_entrypoint(ref, script)
        print(f"   T2 entrypoint {'':<20} {s2}  {d2}")
        s3, d3 = t3_serve(name, ref, port, path)
        print(f"   T3 serve {'':<24} {s3}  {d3}")
        print()
        rows.append((name, s1, s2, s3))

    print("SUMMARY")
    print(f"{'image':<24} {'T1 import':<11} {'T2 entry':<10} {'T3 serve'}")
    for r in rows:
        print(f"{r[0]:<24} {r[1]:<11} {r[2]:<10} {r[3]}")
    print()
    print("A T1 FAIL means the published image CANNOT work -- that is the six-month defect's")
    print("shape. A T3 FAIL may simply mean the service needs a backing dependency; read the")
    print("reason before concluding. Neither is asserted anywhere in CI on the release path.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
