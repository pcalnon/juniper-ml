#!/usr/bin/env python3
"""
Probe an INSTALLED juniper-recurrence for the model / data-client pair it actually runs on.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-18
Status: ad-hoc — investigation (W1.13: the dependency floors juniper-recurrence 0.6.0 shipped without)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
         (W1.13), juniper-recurrence#206 (the floors: model >=0.4.0, data-client >=0.6.0),
         util/ad-hoc/2026-10-17_verify_data_client_0_6_0_published_wheel.py (whose 0.5.0 control
         shows what the older data client accepts)

Why this exists
---------------
juniper-recurrence 0.6.0 moved its IMAGE lock to juniper-recurrence-model 0.4.0 and
juniper-data-client 0.6.0, and its release notes list what the service now refuses because of
them. Its ``pyproject.toml`` ranges still admitted model ``>=0.3.0`` and data-client ``>=0.4.2``.
A fresh ``pip install`` resolves the new pair. ``pip install -U juniper-recurrence`` over a 0.5.0
environment does not: pip's default ``only-if-needed`` strategy keeps any installed release the
range admits. Nothing then fails loudly, which is the point of this probe:

1. ``pip check`` is clean, because the installed metadata's own floors admit the old pair;
2. the app imports, builds and serves ``GET /v1/health`` -- 0.6.0 calls
   ``sequence_data_from_arrays(arrays, split)`` without ``target=``, and data-client 0.4.2 already
   exports ``validate_npz_contract``;
3. the markers of the newer pair are absent: no ``juniper_recurrence_model.data.DEFAULT_TARGET``
   (W1.3, model 0.4.0), and a data client below 0.6.0 (the W1.4 rules).

``--expect stale`` asserts that state (the defect reproduced); ``--expect current`` asserts the
fixed one (both markers present, ``pip check`` clean, the app serving). Run it with the
interpreter of the environment under test, isolated: ``<venv>/bin/python -I <this file>``. It
reads nothing from a git tree, and drops every ``JUNIPER_*`` variable from its own process before
importing the app, so an operator's settings cannot change the result; it never prints a value.

Exit status: 0 the environment matches ``--expect``; 1 it does not; 2 usage, or the app's test
client is unavailable (``pip install httpx`` into the environment under test).
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import os
import subprocess
import sys

PACKAGES = ("juniper-recurrence", "juniper-recurrence-model", "juniper-data-client")
FIRST_CURRENT = {"juniper-recurrence-model": (0, 4, 0), "juniper-data-client": (0, 6, 0)}


def _release(version: str) -> tuple[int, ...]:
    """Return the numeric release tuple of a plain ``X.Y.Z`` version (enough for these packages)."""
    parts = []
    for piece in version.split(".")[:3]:
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _declared(requirement_prefixes: tuple[str, ...]) -> list[str]:
    """Return juniper-recurrence's own Requires-Dist lines for the named packages (base, no extras)."""
    lines = metadata.requires("juniper-recurrence") or []
    return [line for line in lines if line.startswith(requirement_prefixes) and "extra ==" not in line]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 2)[1])
    parser.add_argument("--expect", choices=("stale", "current"), required=True, help="the state the environment must be in")
    args = parser.parse_args(argv)

    print(f"interpreter: {sys.executable}")
    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            print(f"FAIL {name} is not installed in this environment")
            return 1
        print(f"installed: {name} {versions[name]}")
    for line in _declared(("juniper-recurrence-model", "juniper-data-client")):
        print(f"declared by juniper-recurrence {versions['juniper-recurrence']}: {line}")

    check = subprocess.run([sys.executable, "-m", "pip", "check", "--disable-pip-version-check"], capture_output=True, text=True, check=False)
    pip_check_ok = check.returncode == 0
    print(f"pip check: exit {check.returncode}: {(check.stdout or check.stderr).strip()}")

    import juniper_recurrence_model.data as model_data

    has_default_target = hasattr(model_data, "DEFAULT_TARGET")
    print(f"model marker (W1.3, 0.4.0): DEFAULT_TARGET {'present' if has_default_target else 'ABSENT'}")
    client_current = _release(versions["juniper-data-client"]) >= FIRST_CURRENT["juniper-data-client"]
    model_current = _release(versions["juniper-recurrence-model"]) >= FIRST_CURRENT["juniper-recurrence-model"]
    print(f"data-client marker (W1.4, 0.6.0): {'present' if client_current else 'ABSENT'} ({versions['juniper-data-client']})")

    dropped = [key for key in os.environ if key.startswith("JUNIPER_")]
    for key in dropped:
        del os.environ[key]
    print(f"dropped {len(dropped)} JUNIPER_* variable(s) from this process before importing the app (values not read)")
    try:
        from fastapi.testclient import TestClient
    except ImportError as exc:  # starlette's TestClient needs httpx
        print(f"cannot build the test client ({exc}); install httpx into the environment under test")
        return 2
    from juniper_recurrence.app import build_app

    with TestClient(build_app()) as client:
        response = client.get("/v1/health")
    serves = response.status_code == 200
    print(f"GET /v1/health -> {response.status_code} {response.text.strip()}")

    if args.expect == "stale":
        matched = pip_check_ok and serves and not has_default_target and not model_current and not client_current
        verdict = "REPRODUCED: a clean pip check and a serving app over the pre-W1.3 / pre-W1.4 pair" if matched else "NOT REPRODUCED"
    else:
        matched = pip_check_ok and serves and has_default_target and model_current and client_current
        verdict = "CURRENT: the app serves over model >=0.4.0 and data-client >=0.6.0" if matched else "NOT CURRENT"
    print(verdict)
    return 0 if matched else 1


if __name__ == "__main__":
    sys.exit(main())
